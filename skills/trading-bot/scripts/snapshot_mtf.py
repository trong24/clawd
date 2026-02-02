#!/usr/bin/env python3
"""MTF snapshot fetcher (Binance public REST, no external deps).

Fetches OHLCV candles for multiple timeframes and prints a single JSON snapshot.
Designed to match `skills/trading-bot/references/schemas/snapshot.schema.json`.

Example:
  python3 skills/trading-bot/scripts/snapshot_mtf.py --symbol BTCUSDT --tfs 1d,4h,1h,15m --limit 210
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request


def ema(values: list[float], length: int) -> list[float | None]:
    if length <= 0:
        raise ValueError("length must be > 0")
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out
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


BINANCE_BASE_URLS = [
    "https://api.binance.com",
    # Fallback for connectivity / geofencing scenarios
    "https://data-api.binance.vision",
]


def iso_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()


def fetch_json(url: str, timeout_s: int) -> object:
    req = Request(url, headers={"User-Agent": "openclaw-trading-bot"})
    with urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_klines(symbol: str, interval: str, limit: int) -> list[list]:
    """Fetch klines with retries across base URLs and timeouts."""
    last_err: Exception | None = None
    for base in BINANCE_BASE_URLS:
        url = f"{base}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        for attempt, timeout_s in enumerate([8, 12, 20], start=1):
            try:
                data = fetch_json(url, timeout_s=timeout_s)
                assert isinstance(data, list)
                return data  # type: ignore[return-value]
            except Exception as e:
                last_err = e
                if attempt < 3:
                    time.sleep(0.4 * attempt)
                continue
    raise last_err  # type: ignore[misc]


def klines_to_candles(klines: list[list]) -> list[dict]:
    candles: list[dict] = []
    # kline format: [ openTime, open, high, low, close, volume, closeTime, ...]
    for k in klines:
        open_time = int(k[0])
        candles.append(
            {
                "ts_utc": iso_utc(open_time),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
        )
    return candles


def compute_indicators(candles: list[dict]) -> dict:
    """Compute RSI14 + EMA9(RSI14) + WMA45(RSI14)."""
    closes = [float(c["close"]) for c in candles]
    rsi14 = rsi(closes, 14)

    # For EMA/WMA of RSI, replace None with previous value to keep series usable.
    rsi_filled: list[float] = []
    last_val = 50.0
    for v in rsi14:
        if v is None:
            rsi_filled.append(last_val)
        else:
            last_val = float(v)
            rsi_filled.append(last_val)

    ema9_rsi14 = ema(rsi_filled, 9)
    wma45_rsi14 = wma(rsi_filled, 45)

    i = len(candles) - 1
    return {
        "rsi": {"length": 14, "value": rsi14[i]},
        "ema_rsi": {"length": 9, "value": ema9_rsi14[i]},
        "wma_rsi": {"length": 45, "value": wma45_rsi14[i]},
        "rules": {
            "A": {"kind": "midline", "mid": 50},
            "B": {"kind": "band", "low": 40, "high": 60},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--tfs", default="1d,4h,1h,15m")
    ap.add_argument("--limit", type=int, default=210)
    args = ap.parse_args()

    tfs = [tf.strip() for tf in args.tfs.split(",") if tf.strip()]

    snapshot = {
        "exchange": "binance",
        "symbol": args.symbol,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timeframes": {},
    }

    errors: list[str] = []

    for tf in tfs:
        try:
            klines = fetch_klines(args.symbol, tf, args.limit)
            candles = klines_to_candles(klines)
            snapshot["timeframes"][tf] = {
                "interval": tf,
                "candles": candles,
                "indicators": compute_indicators(candles),
            }
            # small spacing to be gentle to API
            time.sleep(0.15)
        except Exception as e:
            errors.append(f"{tf}: {e}")

    if errors:
        snapshot["error"] = True
        snapshot["error_message"] = "; ".join(errors)

    print(json.dumps(snapshot, ensure_ascii=False))


if __name__ == "__main__":
    main()
