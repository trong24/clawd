#!/usr/bin/env python3
"""Collect 15m context for BTCUSDT — minimal version.

Only fetches raw numbers. Analysis is done by LLM.

Output: JSON with price, RSI/EMA/WMA per TF, recent candles, state.
No trend labels, no S/R clustering, no SL/TP logic — that's LLM's job.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SNAPSHOT = WORKSPACE / "skills" / "trading-bot" / "scripts" / "snapshot_mtf.py"
STATE_PATH = WORKSPACE / "trading" / "state_15m.json"

SYMBOL = "BTCUSDT"
TFS = "1d,4h,1h,30m,15m,5m"
LIMIT = "100"  # enough for RSI+EMA+WMA warmup

# How many recent candles to include per TF
CANDLE_LIMITS = {"1d": 30, "4h": 50, "1h": 72, "30m": 96, "15m": 96, "5m": 60}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"position": None, "balance_usdt": 1000.0, "risk_pct": 1.0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"position": None, "balance_usdt": 1000.0, "risk_pct": 1.0}


def main():
    # 1. Fetch snapshot
    p = subprocess.run(
        ["python3", str(SNAPSHOT), "--symbol", SYMBOL, "--tfs", TFS, "--limit", LIMIT],
        capture_output=True, text=True, check=True
    )
    snap = json.loads(p.stdout)

    # 2. Extract per-TF data (just numbers, no classification)
    timeframes = {}
    for tf, block in snap.get("timeframes", {}).items():
        candles = block.get("candles") or []
        ind = block.get("indicators") or {}

        # Trim candles
        limit = CANDLE_LIMITS.get(tf, 50)
        recent = candles[-limit:] if len(candles) > limit else candles

        # Simplify candle format
        simple_candles = [
            {
                "ts": c["ts_utc"],
                "o": round(c["open"], 2),
                "h": round(c["high"], 2),
                "l": round(c["low"], 2),
                "c": round(c["close"], 2),
                "v": round(c["volume"], 2),
            }
            for c in recent
        ]

        timeframes[tf] = {
            "rsi": round(ind.get("rsi", {}).get("value") or 0, 2),
            "ema9_rsi": round(ind.get("ema_rsi", {}).get("value") or 0, 2),
            "wma45_rsi": round(ind.get("wma_rsi", {}).get("value") or 0, 2),
            "last_close": round(candles[-1]["close"], 2) if candles else None,
            "last_high": round(candles[-1]["high"], 2) if candles else None,
            "last_low": round(candles[-1]["low"], 2) if candles else None,
            "candles": simple_candles,
        }

    # 3. Current price from 15m
    tf15 = snap["timeframes"].get("15m", {})
    candles15 = tf15.get("candles") or []
    price = round(candles15[-1]["close"], 2) if candles15 else None
    candle_ts = candles15[-1]["ts_utc"] if candles15 else None

    # 4. State
    state = load_state()

    # 5. Output
    out = {
        "generated_at_utc": utc_now_iso(),
        "symbol": SYMBOL,
        "price": price,
        "candle_15m_ts": candle_ts,
        "timeframes": timeframes,
        "state": {
            "balance_usdt": state.get("balance_usdt", 1000.0),
            "risk_pct": state.get("risk_pct", 1.0),
            "position": state.get("position"),
        },
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
