#!/usr/bin/env python3
"""Append a strategy DECISION/PLAN row to trading/decisions.csv.

This logs what the assistant *planned* at decision time (even if no real order was placed).
It is intentionally separate from executed trade logs.

Usage:
  python3 trading/log_decision.py --decision-id ... --symbol BTCUSDT --side SHORT \
    --tf-trigger 15m --setup A_breakdown_pivot_low \
    --entry-trigger "15m close < 83930 (sell-stop ~83920)" --sl "84120" \
    --balance 1000 --risk-pct 1 --snapshot-ts "2026-01-31T06:00:00+00:00" --price 83990.57 \
    --size "0.05 BTC (if stopDistance≈200)" --notes "..."

"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

HEADERS = [
    "decision_id",
    "decided_at_local",
    "symbol",
    "side",
    "tf_trigger",
    "setup",
    "entry_trigger",
    "sl",
    "balance_usdt",
    "risk_pct_balance",
    "risk_usdt",
    "position_size_base",
    "notes",
    "snapshot_ts_utc",
    "price_snapshot",
    "outcome",
    "closed_at_local",
    "exit",
    "realized_pnl_usdt",
]


def ensure_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADERS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision-id", required=True)
    ap.add_argument("--decided-at-local", default=datetime.now().strftime("%Y-%m-%d %H:%M"))
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--side", required=True, choices=["LONG", "SHORT"])
    ap.add_argument("--tf-trigger", required=True)
    ap.add_argument("--setup", required=True)
    ap.add_argument("--entry-trigger", required=True)
    ap.add_argument("--sl", required=True)
    ap.add_argument("--balance", required=True, type=float)
    ap.add_argument("--risk-pct", required=True, type=float)
    ap.add_argument("--risk-usdt", default=None, type=float)
    ap.add_argument("--size", required=True)
    ap.add_argument("--notes", default="")
    ap.add_argument("--snapshot-ts", required=True)
    ap.add_argument("--price", required=True)

    args = ap.parse_args()

    risk_usdt = args.risk_usdt
    if risk_usdt is None:
        risk_usdt = args.balance * (args.risk_pct / 100.0)

    out = Path(__file__).resolve().parent / "decisions.csv"
    ensure_file(out)

    row = {
        "decision_id": args.decision_id,
        "decided_at_local": args.decided_at_local,
        "symbol": args.symbol,
        "side": args.side,
        "tf_trigger": args.tf_trigger,
        "setup": args.setup,
        "entry_trigger": args.entry_trigger,
        "sl": args.sl,
        "balance_usdt": f"{args.balance:g}",
        "risk_pct_balance": f"{args.risk_pct:g}",
        "risk_usdt": f"{risk_usdt:g}",
        "position_size_base": args.size,
        "notes": args.notes,
        "snapshot_ts_utc": args.snapshot_ts,
        "price_snapshot": str(args.price),
        "outcome": "OPEN",
        "closed_at_local": "",
        "exit": "",
        "realized_pnl_usdt": "",
    }

    with out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writerow(row)

    print(f"Appended decision → {out}")


if __name__ == "__main__":
    main()
