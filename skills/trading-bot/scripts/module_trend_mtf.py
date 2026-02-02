#!/usr/bin/env python3
"""MTF trend labeler based on RSI14 + EMA9(RSI14) + WMA45(RSI14).

Input: snapshot JSON from snapshot_mtf.py (stdin)
Output: JSON with per-timeframe trend labels and reasons.

Rules:
- Rule A (midline 50):
  - UP if RSI>50 AND EMA(RSI)>WMA(RSI)
  - DOWN if RSI<50 AND EMA(RSI)<WMA(RSI)
  - else RANGE/TRANSITION
- Rule B (band 40/60):
  - STRONG_UP if RSI>60 AND EMA>WMA
  - STRONG_DOWN if RSI<40 AND EMA<WMA
  - else neutral

We keep both A and B and report both.
"""

from __future__ import annotations

import json
import math
import sys


def fnum(x):
    if x is None:
        return None
    try:
        v = float(x)
        if math.isnan(v):
            return None
        return v
    except Exception:
        return None


def classify(rsi_v: float, ema_v: float, wma_v: float) -> dict:
    out = {
        "A": "TRANSITION",
        "B": "NEUTRAL",
        "bias": "WAIT",
        "reasons": [],
    }

    ema_gt = ema_v > wma_v
    ema_lt = ema_v < wma_v

    # Rule A
    if rsi_v > 50 and ema_gt:
        out["A"] = "UP"
    elif rsi_v < 50 and ema_lt:
        out["A"] = "DOWN"
    else:
        out["A"] = "RANGE"

    # Rule B
    if rsi_v > 60 and ema_gt:
        out["B"] = "STRONG_UP"
    elif rsi_v < 40 and ema_lt:
        out["B"] = "STRONG_DOWN"
    else:
        out["B"] = "NEUTRAL"

    # Bias (simple): prefer B if strong, else A
    if out["B"] == "STRONG_UP":
        out["bias"] = "BUY_BIAS"
    elif out["B"] == "STRONG_DOWN":
        out["bias"] = "SELL_BIAS"
    elif out["A"] == "UP":
        out["bias"] = "BUY_BIAS_WEAK"
    elif out["A"] == "DOWN":
        out["bias"] = "SELL_BIAS_WEAK"
    else:
        out["bias"] = "WAIT"

    out["reasons"].append(f"RSI14={rsi_v:.2f}")
    out["reasons"].append(f"EMA9(RSI)={ema_v:.2f} vs WMA45(RSI)={wma_v:.2f}")
    return out


def main() -> None:
    snapshot = json.load(sys.stdin)
    tfs = snapshot.get("timeframes", {})

    labels = {}
    errors = []

    for tf, block in tfs.items():
        ind = (block or {}).get("indicators", {})
        rsi_v = fnum((ind.get("rsi") or {}).get("value"))
        ema_v = fnum((ind.get("ema_rsi") or {}).get("value"))
        wma_v = fnum((ind.get("wma_rsi") or {}).get("value"))

        if rsi_v is None or ema_v is None or wma_v is None:
            labels[tf] = {
                "A": "UNKNOWN",
                "B": "UNKNOWN",
                "bias": "WAIT",
                "reasons": [],
            }
            errors.append(f"{tf}: missing indicator values")
            continue

        labels[tf] = classify(rsi_v, ema_v, wma_v)

    # Overall bias: HTF wins
    order = ["1d", "4h", "1h", "15m"]
    bias = "WAIT"
    for tf in order:
        if tf in labels:
            b = labels[tf]["bias"]
            if b != "WAIT":
                bias = b
                break

    out = {
        "module": "trend_mtf_rsi",
        "version": "0.1",
        "exchange": snapshot.get("exchange"),
        "symbol": snapshot.get("symbol"),
        "generated_at_utc": snapshot.get("generated_at_utc"),
        "labels": labels,
        "overall_bias": bias,
        "errors": errors if errors else [],
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
