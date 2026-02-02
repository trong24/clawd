#!/usr/bin/env python3
"""MTF Support/Resistance (S/R) zones (skeleton).

Input: snapshot JSON from snapshot_mtf.py (stdin)
Output: JSON zones + nearest support/resistance.

Method (v0):
- For each timeframe: detect pivot highs/lows (fractal) using a fixed window.
- Convert each pivot into a small zone (lo/hi) using a width in pct.
- Cluster overlapping zones.
- Score strength by (TF weight) + touches.
- Choose nearest support/resistance relative to last 15m close.

Notes:
- This is a starting point; we will later replace/augment with your exact MTF S/R rules.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass


TF_WEIGHT = {
    "1d": 4.0,
    "4h": 3.0,
    "1h": 2.0,
    "15m": 1.0,
}


@dataclass
class Zone:
    tf: str
    kind: str  # support|resistance
    lo: float
    hi: float
    strength: float
    touches: int
    last_touch_utc: str


def pct_band(price: float, pct: float) -> tuple[float, float]:
    w = price * (pct / 100.0)
    return price - w, price + w


def is_pivot_high(highs: list[float], i: int, left: int, right: int) -> bool:
    h = highs[i]
    for j in range(i - left, i + right + 1):
        if j == i:
            continue
        if j < 0 or j >= len(highs):
            continue
        if highs[j] >= h:
            return False
    return True


def is_pivot_low(lows: list[float], i: int, left: int, right: int) -> bool:
    l = lows[i]
    for j in range(i - left, i + right + 1):
        if j == i:
            continue
        if j < 0 or j >= len(lows):
            continue
        if lows[j] <= l:
            return False
    return True


def cluster_zones(zones: list[Zone]) -> list[Zone]:
    # simple overlap clustering per tf+kind
    out: list[Zone] = []
    zones_sorted = sorted(zones, key=lambda z: (z.kind, z.lo, z.hi))

    for z in zones_sorted:
        if not out:
            out.append(z)
            continue
        last = out[-1]
        if z.kind == last.kind and z.lo <= last.hi:
            # merge
            merged = Zone(
                tf=last.tf if TF_WEIGHT.get(last.tf, 1) >= TF_WEIGHT.get(z.tf, 1) else z.tf,
                kind=last.kind,
                lo=min(last.lo, z.lo),
                hi=max(last.hi, z.hi),
                strength=last.strength + z.strength,
                touches=last.touches + z.touches,
                last_touch_utc=max(last.last_touch_utc, z.last_touch_utc),
            )
            out[-1] = merged
        else:
            out.append(z)

    return out


def main() -> None:
    snap = json.load(sys.stdin)
    tfs = snap.get("timeframes", {})

    # reference price: last 15m close (fallback: any tf)
    ref_price = None
    ref_ts = None
    if "15m" in tfs and tfs["15m"].get("candles"):
        last = tfs["15m"]["candles"][-1]
        ref_price = float(last["close"])
        ref_ts = last["ts_utc"]
    else:
        for tf, block in tfs.items():
            if block.get("candles"):
                last = block["candles"][-1]
                ref_price = float(last["close"])
                ref_ts = last["ts_utc"]
                break

    if ref_price is None:
        print(
            json.dumps(
                {
                    "module": "sr_mtf",
                    "version": "0.1",
                    "error": True,
                    "error_message": "no candles",
                },
                ensure_ascii=False,
            )
        )
        return

    # pivot params per timeframe (rough defaults)
    pivot_window = {
        "1d": (3, 3),
        "4h": (3, 3),
        "1h": (4, 4),
        "15m": (5, 5),
    }

    # zone width per tf (pct around pivot)
    zone_pct = {
        "1d": 0.30,
        "4h": 0.25,
        "1h": 0.20,
        "15m": 0.15,
    }

    zones: list[Zone] = []

    for tf, block in tfs.items():
        candles = block.get("candles") or []
        if len(candles) < 20:
            continue

        highs = [float(c["high"]) for c in candles]
        lows = [float(c["low"]) for c in candles]
        ts = [c["ts_utc"] for c in candles]

        left, right = pivot_window.get(tf, (4, 4))
        pct = zone_pct.get(tf, 0.2)
        weight = TF_WEIGHT.get(tf, 1.0)

        for i in range(left, len(candles) - right):
            if is_pivot_high(highs, i, left, right):
                lo, hi = pct_band(highs[i], pct)
                zones.append(
                    Zone(
                        tf=tf,
                        kind="resistance",
                        lo=lo,
                        hi=hi,
                        strength=weight,
                        touches=1,
                        last_touch_utc=ts[i],
                    )
                )
            if is_pivot_low(lows, i, left, right):
                lo, hi = pct_band(lows[i], pct)
                zones.append(
                    Zone(
                        tf=tf,
                        kind="support",
                        lo=lo,
                        hi=hi,
                        strength=weight,
                        touches=1,
                        last_touch_utc=ts[i],
                    )
                )

    clustered = cluster_zones(zones)

    # Score bump for more touches
    for z in clustered:
        z.strength = z.strength + 0.5 * max(0, z.touches - 1)

    # Pick nearest support/resistance (prefer HTF implicitly via strength)
    supports = [z for z in clustered if z.kind == "support" and z.hi <= ref_price]
    resistances = [z for z in clustered if z.kind == "resistance" and z.lo >= ref_price]

    supports_sorted = sorted(
        supports,
        key=lambda z: (-(z.strength), abs(ref_price - z.hi)),
    )
    resistances_sorted = sorted(
        resistances,
        key=lambda z: (-(z.strength), abs(z.lo - ref_price)),
    )

    nearest_support = supports_sorted[0] if supports_sorted else None
    nearest_resistance = resistances_sorted[0] if resistances_sorted else None

    out = {
        "module": "sr_mtf",
        "version": "0.1",
        "exchange": snap.get("exchange"),
        "symbol": snap.get("symbol"),
        "ref": {"price": ref_price, "ts_utc": ref_ts},
        "zones": [z.__dict__ for z in sorted(clustered, key=lambda z: (-z.strength, z.lo))][:50],
        "nearest_support": nearest_support.__dict__ if nearest_support else None,
        "nearest_resistance": nearest_resistance.__dict__ if nearest_resistance else None,
        "confidence": 0.3,
        "reasons": [
            "skeleton pivot+clustering; HTF weighted",
            "zones are approximate bands around pivots",
        ],
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
