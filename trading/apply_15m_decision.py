#!/usr/bin/env python3
"""Apply an LLM decision (OPEN/CLOSE/NOOP) to local state + CSV log.

This script does NOT decide; it only records:
- state_15m.json (position open/closed)
- trades_15m.csv (append on OPEN/CLOSE)

Usage examples:
  python3 trading/apply_15m_decision.py \
    --action OPEN --side SHORT --tf 15m --entry 83920 --sl 84120 --size 0.05 \
    --candle-ts 2026-01-31T06:00:00+00:00 --notes "..." \
    --rsi 34.7 --ema9 33.2 --wma45 42.9 --bias15m SELL_BIAS

  python3 trading/apply_15m_decision.py \
    --action CLOSE --side SHORT --tf 15m --entry 83920 --sl 84120 --size 0.05 \
    --candle-ts ... --notes "bad force" --rsi ... --ema9 ... --wma45 ... --bias15m WAIT

"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
STATE_PATH = WORKSPACE / "trading" / "state_15m.json"
CSV_PATH = WORKSPACE / "trading" / "trades_15m.csv"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"position": None, "last_candle_ts_utc": None, "balance_usdt": 1000.0, "risk_pct": 1.0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"position": None, "last_candle_ts_utc": None, "balance_usdt": 1000.0, "risk_pct": 1.0}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_csv():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.exists():
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
        "candle_ts_utc",
        "notes",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(headers)


def append_row(row: dict):
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--action", required=True, choices=["OPEN", "CLOSE", "NOOP"])
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--side", default="")
    ap.add_argument("--tf", default="15m")
    ap.add_argument("--entry", type=float, default=None)
    ap.add_argument("--sl", type=float, default=None)
    ap.add_argument("--size", type=float, default=None)
    ap.add_argument("--candle-ts", required=True)
    ap.add_argument("--notes", default="")
    ap.add_argument("--rsi", type=float, required=True)
    ap.add_argument("--ema9", type=float, required=True)
    ap.add_argument("--wma45", type=float, required=True)
    ap.add_argument("--bias15m", required=True)

    args = ap.parse_args()

    state = load_state()
    state["last_candle_ts_utc"] = args.candle_ts

    if args.action == "NOOP":
        save_state(state)
        return

    ensure_csv()
    bal = float(state.get("balance_usdt", 1000.0))
    risk_pct = float(state.get("risk_pct", 1.0))
    risk_usdt = bal * risk_pct / 100.0

    row = {
        "event_id": f"{args.candle_ts}_{args.action}",
        "event_ts_utc": utc_now_iso(),
        "symbol": args.symbol,
        "action": args.action,
        "side": args.side,
        "tf_manage": args.tf,
        "entry": "" if args.entry is None else f"{args.entry:.2f}",
        "sl": "" if args.sl is None else f"{args.sl:.2f}",
        "size_btc": "" if args.size is None else f"{args.size:.6f}",
        "balance_usdt": f"{bal:g}",
        "risk_pct": f"{risk_pct:g}",
        "risk_usdt": f"{risk_usdt:g}",
        "rsi15": f"{args.rsi:.2f}",
        "ema9_rsi15": f"{args.ema9:.2f}",
        "wma45_rsi15": f"{args.wma45:.2f}",
        "bias15m": args.bias15m,
        "candle_ts_utc": args.candle_ts,
        "notes": args.notes,
    }
    append_row(row)

    if args.action == "OPEN":
        state["position"] = {
            "side": args.side,
            "tf": args.tf,
            "entry": args.entry,
            "sl": args.sl,
            "size_btc": args.size,
            "opened_ts_utc": utc_now_iso(),
        }

    if args.action == "CLOSE":
        state["position"] = None

    save_state(state)


if __name__ == "__main__":
    main()
