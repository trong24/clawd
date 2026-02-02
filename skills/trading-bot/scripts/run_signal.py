#!/usr/bin/env python3
"""Simple Binance BTCUSDT signal generator (no external deps).

- Fetches klines from Binance public REST
- Computes RSI(14), EMA(9), WMA(45)
- Emits a JSON object to stdout

This is intentionally minimal so it can run inside OpenClaw cron via tool exec.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request


def fetch_binance_klines(symbol: str, interval: str, limit: int) -> list[list]:
    """Fetch klines with small retry/backoff to survive transient timeouts."""
    # https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
    url = (
        "https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )

    last_err: Exception | None = None
    # 3 tries: 8s, 12s, 20s timeouts
    for attempt, timeout_s in enumerate([8, 12, 20], start=1):
        try:
            req = Request(url, headers={"User-Agent": "openclaw-cron"})
            with urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            last_err = e
            # brief backoff (attempt 1 -> 0.5s, attempt 2 -> 1.0s)
            if attempt < 3:
                time.sleep(0.5 * attempt)

    raise last_err  # type: ignore[misc]


def ema(values: list[float], length: int) -> list[float | None]:
    if length <= 0:
        raise ValueError("length must be > 0")
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out

    # seed with SMA
    sma = sum(values[:length]) / length
    out[length - 1] = sma
    k = 2 / (length + 1)
    prev = sma
    for i in range(length, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def wma(values: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out
    weights = list(range(1, length + 1))
    denom = sum(weights)
    for i in range(length - 1, len(values)):
        window = values[i - length + 1 : i + 1]
        out[i] = sum(w * v for w, v in zip(weights, window)) / denom
    return out


def rsi(values: list[float], length: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) <= length:
        return out

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, length + 1):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains) / length
    avg_loss = sum(losses) / length

    def calc_rsi(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        rs = ag / al
        return 100.0 - (100.0 / (1.0 + rs))

    out[length] = calc_rsi(avg_gain, avg_loss)

    for i in range(length + 1, len(values)):
        change = values[i] - values[i - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        avg_gain = (avg_gain * (length - 1) + gain) / length
        avg_loss = (avg_loss * (length - 1) + loss) / length
        out[i] = calc_rsi(avg_gain, avg_loss)

    return out


def iso_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="15m")
    ap.add_argument("--limit", type=int, default=210)
    # RSI filter (for combo strategy):
    # - BUY only if RSI <= rsi_buy_max
    # - SELL only if RSI >= rsi_sell_min
    ap.add_argument("--rsi-buy-max", type=float, default=60.0)
    ap.add_argument("--rsi-sell-min", type=float, default=40.0)
    args = ap.parse_args()

    try:
        klines = fetch_binance_klines(args.symbol, args.interval, args.limit)
    except Exception as e:
        # Emit a clean JSON error so cron/agent can relay it predictably.
        err = {
            "exchange": "binance",
            "symbol": args.symbol,
            "timeframe": args.interval,
            "action": "ALERT_ONLY",
            "error": True,
            "error_message": str(e),
            "meta": {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "now_ms": int(time.time() * 1000),
            },
        }
        print(json.dumps(err, ensure_ascii=False))
        return

    # kline format: [ openTime, open, high, low, close, volume, closeTime, ...]
    closes = [float(k[4]) for k in klines]
    opens = [float(k[1]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    vols = [float(k[5]) for k in klines]
    open_times = [int(k[0]) for k in klines]

    ema9 = ema(closes, 9)
    wma45 = wma(closes, 45)
    rsi14 = rsi(closes, 14)

    i = len(closes) - 1
    if i < 2:
        raise SystemExit("not enough data")

    prev_i = i - 1

    signal = "NONE"
    reason = "no-cross"

    # Only decide if both indicators exist on prev and last bars
    if (
        ema9[prev_i] is not None
        and wma45[prev_i] is not None
        and ema9[i] is not None
        and wma45[i] is not None
    ):
        last_rsi = rsi14[i]
        # If RSI isn't available yet, don't emit signals.
        if last_rsi is None or (isinstance(last_rsi, float) and math.isnan(last_rsi)):
            signal = "NONE"
            reason = "rsi_not_ready"
        else:
            cross_up = ema9[prev_i] <= wma45[prev_i] and ema9[i] > wma45[i]
            cross_dn = ema9[prev_i] >= wma45[prev_i] and ema9[i] < wma45[i]

            if cross_up and last_rsi <= args.rsi_buy_max:
                signal = "BUY"
                reason = f"ema9_cross_up_wma45_and_rsi<={args.rsi_buy_max:g}"
            elif cross_dn and last_rsi >= args.rsi_sell_min:
                signal = "SELL"
                reason = f"ema9_cross_down_wma45_and_rsi>={args.rsi_sell_min:g}"
            else:
                signal = "NONE"
                reason = "filters_blocked_signal"

    out = {
        "filters": {
            "rsi_buy_max": args.rsi_buy_max,
            "rsi_sell_min": args.rsi_sell_min,
        },
        "ts_utc": iso_utc(open_times[i]),
        "exchange": "binance",
        "symbol": args.symbol,
        "timeframe": args.interval,
        "price": closes[i],
        "rsi14": rsi14[i],
        "ema9": ema9[i],
        "wma45": wma45[i],
        "signal": signal,
        "reason": reason,
        "action": "ALERT_ONLY",
        "raw": {
            "open": opens[i],
            "high": highs[i],
            "low": lows[i],
            "close": closes[i],
            "volume": vols[i],
        },
        "meta": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "now_ms": int(time.time() * 1000),
        },
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
