#!/usr/bin/env python3
"""15m BTCUSDT analysis bot (alert-only).

Runs after each 15m candle close (cron should trigger at minute 01/16/31/46 UTC).

What it does:
- Fetch snapshot (1d/4h/1h/15m)
- Compute trend labels (RSI14 + EMA9(RSI) + WMA45(RSI))
- Compute a local SL from the nearest 15m pivot high/low (simple swing pivots)
- Decide OPEN/CLOSE based on:
  - OPEN SHORT when HTF is STRONG_DOWN and 15m is STRONG_DOWN
  - CLOSE when "bad force" on 15m: RSI in 40–60 balance zone OR bias flips against position
- Log decisions to CSV (open/close only)
- Output a single line:
    TELEGRAM: <message>
  or:
    NOOP

Config/state:
- trading/state_15m.json (created automatically)
- trading/trades_15m.csv (created automatically)

NOTE: This logs *strategy signals* (not executed fills).
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

WORKSPACE = Path(__file__).resolve().parents[1]
SKILL_DIR = WORKSPACE / "skills" / "trading-bot"
SNAPSHOT = SKILL_DIR / "scripts" / "snapshot_mtf.py"
MOD_TREND = SKILL_DIR / "scripts" / "module_trend_mtf.py"

STATE_PATH = WORKSPACE / "trading" / "state_15m.json"
CSV_PATH = WORKSPACE / "trading" / "trades_15m.csv"

SYMBOL = "BTCUSDT"
TFS = "1d,4h,1h,15m"
LIMIT = "210"

BALANCE_USDT_DEFAULT = 1000.0
RISK_PCT_DEFAULT = 1.0

PIVOT_K = 2
SL_BUFFER_USDT = 20.0  # small buffer above pivot high / below pivot low


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str], input_text: Optional[str] = None) -> str:
    p = subprocess.run(
        cmd,
        input=input_text.encode("utf-8") if input_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return p.stdout.decode("utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_csv(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    headers = [
        "event_id",
        "event_ts_utc",
        "symbol",
        "action",
        "side",
        "tf_manage",
        "entry",
        "sl",
        "size_btc",
        "balance_usdt",
        "risk_pct",
        "risk_usdt",
        "rsi15",
        "ema9_rsi15",
        "wma45_rsi15",
        "bias15m",
        "bias1h",
        "bias4h",
        "bias1d",
        "snapshot_candle_ts_utc",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(headers)


def append_csv(path: Path, row: dict):
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        w.writerow(row)


def pivot_highs(candles: list[dict], k: int = 2):
    piv = []
    for i in range(k, len(candles) - k):
        h = candles[i]["high"]
        if all(h > candles[i - j]["high"] for j in range(1, k + 1)) and all(
            h > candles[i + j]["high"] for j in range(1, k + 1)
        ):
            piv.append((i, h, candles[i]["ts_utc"]))
    return piv


def pivot_lows(candles: list[dict], k: int = 2):
    piv = []
    for i in range(k, len(candles) - k):
        l = candles[i]["low"]
        if all(l < candles[i - j]["low"] for j in range(1, k + 1)) and all(
            l < candles[i + j]["low"] for j in range(1, k + 1)
        ):
            piv.append((i, l, candles[i]["ts_utc"]))
    return piv


def nearest_pivot_high_above(candles: list[dict], price: float) -> Optional[Tuple[int, float, str]]:
    highs = [p for p in pivot_highs(candles, PIVOT_K) if p[1] > price]
    highs.sort(key=lambda x: x[1])
    return highs[0] if highs else None


def nearest_pivot_low_below(candles: list[dict], price: float) -> Optional[Tuple[int, float, str]]:
    lows = [p for p in pivot_lows(candles, PIVOT_K) if p[1] < price]
    lows.sort(key=lambda x: -x[1])
    return lows[0] if lows else None


def in_balance_zone(rsi: float) -> bool:
    return 40.0 <= rsi <= 60.0


def main():
    state = {
        "last_candle_ts_utc": None,
        "position": None,  # {side, entry, sl, size_btc, opened_ts_utc}
        "balance_usdt": BALANCE_USDT_DEFAULT,
        "risk_pct": RISK_PCT_DEFAULT,
    }
    if STATE_PATH.exists():
        try:
            state.update(load_json(STATE_PATH))
        except Exception:
            pass

    # snapshot
    snap_json = run(
        ["python3", str(SNAPSHOT), "--symbol", SYMBOL, "--tfs", TFS, "--limit", LIMIT]
    )
    snap = json.loads(snap_json)

    # trend labels
    trend_json = run(["python3", str(MOD_TREND)], input_text=snap_json)
    trend = json.loads(trend_json)

    tf15 = snap["timeframes"]["15m"]
    candles = tf15["candles"]
    last_candle = candles[-1]
    candle_ts = last_candle["ts_utc"]
    close = float(last_candle["close"])

    if state.get("last_candle_ts_utc") == candle_ts:
        print("NOOP")
        return

    state["last_candle_ts_utc"] = candle_ts

    labels = trend["labels"]
    l1d, l4h, l1h, l15 = labels["1d"], labels["4h"], labels["1h"], labels["15m"]

    # extract RSI values from snapshot indicators (15m)
    ind15 = tf15["indicators"]
    # snapshot_mtf.py schema (v0): indicators.rsi/ema_rsi/wma_rsi each has {length,value}
    rsi15 = float(ind15["rsi"]["value"])
    ema9 = float(ind15["ema_rsi"]["value"])
    wma45 = float(ind15["wma_rsi"]["value"])

    ensure_csv(CSV_PATH)

    def log_event(action: str, side: str, entry: str, sl: str, size_btc: str, notes: str):
        row = {
            "event_id": f"{candle_ts}_{action}",
            "event_ts_utc": utc_now_iso(),
            "symbol": SYMBOL,
            "action": action,
            "side": side,
            "tf_manage": "15m",
            "entry": entry,
            "sl": sl,
            "size_btc": size_btc,
            "balance_usdt": str(state.get("balance_usdt")),
            "risk_pct": str(state.get("risk_pct")),
            "risk_usdt": str(float(state.get("balance_usdt", BALANCE_USDT_DEFAULT)) * float(state.get("risk_pct", RISK_PCT_DEFAULT)) / 100.0),
            "rsi15": f"{rsi15:.2f}",
            "ema9_rsi15": f"{ema9:.2f}",
            "wma45_rsi15": f"{wma45:.2f}",
            "bias15m": l15["bias"],
            "bias1h": l1h["bias"],
            "bias4h": l4h["bias"],
            "bias1d": l1d["bias"],
            "snapshot_candle_ts_utc": candle_ts,
            "notes": notes,
        }
        append_csv(CSV_PATH, row)

    pos = state.get("position")

    # CLOSE logic (bad force)
    # Rule update (2026-01-31): RSI 40-60 is WARNING only, not auto-close.
    # Close only when:
    #   (a) bias flips to opposite direction (e.g., SHORT but 15m shows BUY_BIAS)
    #   (b) RSI 40-60 AND bias flips (confirmation required)
    # RSI 40-60 alone = HOLD with warning
    if pos is not None:
        side = pos["side"]
        bad_force = False
        warning_only = False
        reason = []

        # Check if RSI in balance zone (warning, not auto-close)
        rsi_in_balance = in_balance_zone(rsi15)
        if rsi_in_balance:
            warning_only = True
            reason.append("RSI15 in 40-60 balance zone (warning)")

        # bias flips opposite → this IS a close signal
        if side == "SHORT" and l15["bias"].startswith("BUY"):
            bad_force = True
            reason.append(f"15m bias flipped to {l15['bias']}")
        if side == "LONG" and l15["bias"].startswith("SELL"):
            bad_force = True
            reason.append(f"15m bias flipped to {l15['bias']}")

        # Only close on actual bad force (bias flip), not just RSI balance zone
        if bad_force:
            notes = "; ".join(reason)
            log_event(
                action="CLOSE",
                side=side,
                entry=str(pos.get("entry")),
                sl=str(pos.get("sl")),
                size_btc=str(pos.get("size_btc")),
                notes=notes,
            )
            state["position"] = None
            save_json(STATE_PATH, state)
            print(
                "TELEGRAM: [BTCUSDT 15m] CLOSE {side} | Price={p:.2f} | RSI={r:.2f} | Reason: {notes} | CandleUTC={cts}".format(
                    side=side, p=close, r=rsi15, notes=notes, cts=candle_ts
                )
            )
            return

        # Warning only (RSI balance zone but no bias flip) - HOLD but emit warning
        if warning_only and not bad_force:
            save_json(STATE_PATH, state)
            print(
                "TELEGRAM: [BTCUSDT 15m] ⚠️ WARNING {side} | Price={p:.2f} | RSI={r:.2f} | {warn} | HOLD position | CandleUTC={cts}".format(
                    side=side, p=close, r=rsi15, warn="; ".join(reason), cts=candle_ts
                )
            )
            return

    # OPEN logic (only when flat)
    if pos is None:
        htf_strong_down = (l1d["B"] == "STRONG_DOWN") and (l4h["B"] == "STRONG_DOWN")
        ltf_strong_down = (l15["B"] == "STRONG_DOWN")

        if htf_strong_down and ltf_strong_down:
            # pick SL from nearest pivot high above entry
            piv_hi = nearest_pivot_high_above(candles, close)
            if not piv_hi:
                save_json(STATE_PATH, state)
                print("NOOP")
                return
            sl = float(piv_hi[1]) + SL_BUFFER_USDT
            entry = close
            stop_dist = sl - entry
            if stop_dist <= 0:
                save_json(STATE_PATH, state)
                print("NOOP")
                return
            risk_usdt = float(state.get("balance_usdt", BALANCE_USDT_DEFAULT)) * float(state.get("risk_pct", RISK_PCT_DEFAULT)) / 100.0
            size_btc = risk_usdt / stop_dist
            # guardrails
            if size_btc <= 0 or not math.isfinite(size_btc):
                save_json(STATE_PATH, state)
                print("NOOP")
                return

            state["position"] = {
                "side": "SHORT",
                "entry": entry,
                "sl": sl,
                "size_btc": size_btc,
                "opened_ts_utc": utc_now_iso(),
                "pivot_high_ts_utc": piv_hi[2],
                "pivot_high": piv_hi[1],
            }
            log_event(
                action="OPEN",
                side="SHORT",
                entry=f"{entry:.2f}",
                sl=f"{sl:.2f}",
                size_btc=f"{size_btc:.6f}",
                notes=f"HTF STRONG_DOWN + 15m STRONG_DOWN; SL from nearest 15m pivot high {piv_hi[1]:.2f} (+{SL_BUFFER_USDT:.0f}).",
            )
            save_json(STATE_PATH, state)
            print(
                "TELEGRAM: [BTCUSDT 15m] OPEN SHORT | Entry={e:.2f} SL={sl:.2f} Size={sz:.6f}BTC | RSI={r:.2f} | CandleUTC={cts}".format(
                    e=entry, sl=sl, sz=size_btc, r=rsi15, cts=candle_ts
                )
            )
            return

    save_json(STATE_PATH, state)
    print("NOOP")


if __name__ == "__main__":
    main()
