#!/usr/bin/env python3
"""Collect 15m after-close context for BTCUSDT.

This script is deterministic (no decision-making).
It outputs a single JSON object to stdout.

Used by an LLM-in-the-loop cron job which:
- reads this JSON
- decides OPEN/CLOSE/NOOP
- writes logs + sends Telegram

"""

from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List

WORKSPACE = Path(__file__).resolve().parents[1]
SKILL_DIR = WORKSPACE / "skills" / "trading-bot"
SNAPSHOT = SKILL_DIR / "scripts" / "snapshot_mtf.py"
MOD_TREND = SKILL_DIR / "scripts" / "module_trend_mtf.py"
MOD_SR = SKILL_DIR / "scripts" / "module_sr_mtf.py"

STATE_PATH = WORKSPACE / "trading" / "state_15m.json"

SYMBOL = "BTCUSDT"
# Include lower TFs so the LLM can compare recent history (e.g., "02:30 GMT+7" vs now)
# without needing a separate fetch.
TFS = "1d,4h,1h,30m,15m,5m"
LIMIT = "210"

# How many most-recent candles to include per TF in the JSON output.
# Keep this bounded to avoid huge payloads.
HISTORY_LIMITS = {
    "1h": 120,
    "30m": 160,
    "15m": 200,
    "5m": 240,
}



def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str], input_text: str | None = None) -> str:
    p = subprocess.run(
        cmd,
        input=input_text.encode("utf-8") if input_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return p.stdout.decode("utf-8")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"position": None, "last_candle_ts_utc": None, "balance_usdt": 1000.0, "risk_pct": 1.0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"position": None, "last_candle_ts_utc": None, "balance_usdt": 1000.0, "risk_pct": 1.0}


def pick_sr_zone(sr: dict, kind: str, prefer_tfs: list[str], price: float) -> Optional[dict]:
    """Pick nearest zone of given kind relative to price, preferring TF order.

    kind: 'support' or 'resistance'
    For resistance: choose nearest zone with lo > price (above)
    For support: choose nearest zone with hi < price (below)
    """
    zones = sr.get('zones') or []


def rsi_wilder(series: List[float], length: int = 14) -> List[Optional[float]]:
    """Wilder's RSI.

    Returns a list aligned to `series` (same length). Values are None until enough
    data is available.
    """
    if len(series) < length + 1:
        return [None] * len(series)

    deltas = [series[i] - series[i - 1] for i in range(1, len(series))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    avg_gain = sum(gains[:length]) / length
    avg_loss = sum(losses[:length]) / length

    out: List[Optional[float]] = [None] * len(series)

    def rsi_from_avgs(g: float, l: float) -> float:
        if l == 0:
            return 100.0
        rs = g / l
        return 100.0 - (100.0 / (1.0 + rs))

    # RSI value corresponds to the candle at index `length` (0-indexed)
    out[length] = rsi_from_avgs(avg_gain, avg_loss)

    for i in range(length + 1, len(series)):
        g = gains[i - 1]
        l = losses[i - 1]
        avg_gain = ((avg_gain * (length - 1)) + g) / length
        avg_loss = ((avg_loss * (length - 1)) + l) / length
        out[i] = rsi_from_avgs(avg_gain, avg_loss)

    return out


def ema(series: List[Optional[float]], length: int) -> List[Optional[float]]:
    """EMA over a series that may contain None.

    Starts once the first non-None value appears; before that EMA is None.
    """
    alpha = 2.0 / (length + 1.0)
    out: List[Optional[float]] = [None] * len(series)
    prev: Optional[float] = None

    for i, v in enumerate(series):
        if v is None:
            out[i] = None
            continue
        if prev is None:
            prev = float(v)
        else:
            prev = (alpha * float(v)) + ((1 - alpha) * prev)
        out[i] = prev

    return out


def wma(series: List[Optional[float]], length: int) -> List[Optional[float]]:
    """WMA over a series that may contain None.

    Requires a full window of non-None values.
    """
    out: List[Optional[float]] = [None] * len(series)
    weights = list(range(1, length + 1))
    wsum = float(sum(weights))

    for i in range(len(series)):
        if i < length - 1:
            continue
        window = series[i - length + 1 : i + 1]
        if any(v is None for v in window):
            continue
        out[i] = sum(float(v) * w for v, w in zip(window, weights)) / wsum

    return out

    def filt(tf: str):
        if kind == 'resistance':
            cand = [z for z in zones if z.get('kind')=='resistance' and z.get('tf')==tf and float(z.get('lo'))>price]
            cand.sort(key=lambda z: float(z['lo']))
            return cand[0] if cand else None
        else:
            cand = [z for z in zones if z.get('kind')=='support' and z.get('tf')==tf and float(z.get('hi'))<price]
            cand.sort(key=lambda z: -float(z['hi']))
            return cand[0] if cand else None

    for tf in prefer_tfs:
        z = filt(tf)
        if z:
            return z

    # fallback: any tf
    if kind == 'resistance':
        cand = [z for z in zones if z.get('kind')=='resistance' and float(z.get('lo'))>price]
        cand.sort(key=lambda z: float(z['lo']))
        return cand[0] if cand else None
    else:
        cand = [z for z in zones if z.get('kind')=='support' and float(z.get('hi'))<price]
        cand.sort(key=lambda z: -float(z['hi']))
        return cand[0] if cand else None


def main():
    state = load_state()

    snap_json = run(["python3", str(SNAPSHOT), "--symbol", SYMBOL, "--tfs", TFS, "--limit", LIMIT])
    snap = json.loads(snap_json)

    trend_json = run(["python3", str(MOD_TREND)], input_text=snap_json)
    trend = json.loads(trend_json)

    sr_json = run(["python3", str(MOD_SR)], input_text=snap_json)
    sr = json.loads(sr_json)

    tf15 = snap["timeframes"]["15m"]
    candles = tf15["candles"]
    last = candles[-1]
    candle_ts = last["ts_utc"]
    close = float(last["close"])

    ind15 = tf15["indicators"]
    rsi15 = float(ind15["rsi"]["value"])
    ema9 = float(ind15["ema_rsi"]["value"])
    wma45 = float(ind15["wma_rsi"]["value"])

    # ZONE candidates for SL/TP reference.
    # SL/TP selection is done by LLM; this script only provides numeric candidates.
    z_res_1d = pick_sr_zone(sr, 'resistance', ['1d'], close)
    z_res_4h = pick_sr_zone(sr, 'resistance', ['4h'], close)
    z_res_1h = pick_sr_zone(sr, 'resistance', ['1h'], close)
    z_res_15m = pick_sr_zone(sr, 'resistance', ['15m'], close)

    z_sup_1d = pick_sr_zone(sr, 'support', ['1d'], close)
    z_sup_4h = pick_sr_zone(sr, 'support', ['4h'], close)
    z_sup_1h = pick_sr_zone(sr, 'support', ['1h'], close)
    z_sup_15m = pick_sr_zone(sr, 'support', ['15m'], close)

    def sl_candidate(kind: str, z: dict, edge: str, label: str):
        return {
            'tf': z.get('tf'),
            'kind': z.get('kind'),
            'lo': float(z.get('lo')),
            'hi': float(z.get('hi')),
            'strength': z.get('strength'),
            'touches': z.get('touches'),
            'last_touch_utc': z.get('last_touch_utc'),
            'level': float(z.get(edge)),
            'edge': edge,
            'label': label,
        }

    suggested_sl_short = {
        'method': 'zone',
        'candidates': [],
        'rule': 'SHORT SL = resistance zone HI (candidates: 1H,15m,4H)'
    }
    # candidates ordered from big TF -> small TF
    if z_res_1d:
        suggested_sl_short['candidates'].append(sl_candidate('short', z_res_1d, 'hi', '1d'))
    if z_res_4h:
        suggested_sl_short['candidates'].append(sl_candidate('short', z_res_4h, 'hi', '4h'))
    if z_res_1h:
        suggested_sl_short['candidates'].append(sl_candidate('short', z_res_1h, 'hi', '1h'))
    if z_res_15m:
        suggested_sl_short['candidates'].append(sl_candidate('short', z_res_15m, 'hi', '15m'))

    suggested_sl_long = {
        'method': 'zone',
        'candidates': [],
        'rule': 'LONG SL = support zone LO (candidates: 1H,15m,4H)'
    }
    # candidates ordered from big TF -> small TF
    if z_sup_1d:
        suggested_sl_long['candidates'].append(sl_candidate('long', z_sup_1d, 'lo', '1d'))
    if z_sup_4h:
        suggested_sl_long['candidates'].append(sl_candidate('long', z_sup_4h, 'lo', '4h'))
    if z_sup_1h:
        suggested_sl_long['candidates'].append(sl_candidate('long', z_sup_1h, 'lo', '1h'))
    if z_sup_15m:
        suggested_sl_long['candidates'].append(sl_candidate('long', z_sup_15m, 'lo', '15m'))

    def compact_candles(tf_key: str) -> list[dict]:
        """Return recent candle history for tf_key with derived indicators.

        Includes RSI14 + EMA9(RSI) + WMA45(RSI) per candle so the LLM can compare
        a specific local time (e.g. 02:30 GMT+7) vs now deterministically.
        """
        tf = snap["timeframes"].get(tf_key)
        if not tf:
            return []
        n = int(HISTORY_LIMITS.get(tf_key, 0) or 0)
        c = tf.get("candles") or []
        if n > 0:
            c = c[-n:]

        closes = [float(x.get("close")) for x in c]
        rsi = rsi_wilder(closes, length=14)
        ema_rsi = ema(rsi, length=9)
        wma_rsi = wma(rsi, length=45)

        out = []
        for i, x in enumerate(c):
            out.append(
                {
                    "ts_utc": x.get("ts_utc"),
                    "open": float(x.get("open")),
                    "high": float(x.get("high")),
                    "low": float(x.get("low")),
                    "close": float(x.get("close")),
                    "volume": float(x.get("volume")),
                    "rsi14": rsi[i],
                    "ema9_rsi": ema_rsi[i],
                    "wma45_rsi": wma_rsi[i],
                }
            )
        return out

    out = {
        "generated_at_utc": utc_now_iso(),
        "symbol": SYMBOL,
        "candle_15m_ts_utc": candle_ts,
        "price_close": close,
        "trend": trend,
        "sr": sr,
        "rsi15": {"rsi": rsi15, "ema9": ema9, "wma45": wma45},
        "history": {
            "1h": compact_candles("1h"),
            "30m": compact_candles("30m"),
            "15m": compact_candles("15m"),
            "5m": compact_candles("5m"),
        },
        "suggested_sl": {"short": suggested_sl_short, "long": suggested_sl_long},
        "tp_reference": {
            "short": {
                "candidates": [
                    # ordered big TF -> small TF
                    sl_candidate('tp_short', z_sup_1d, 'hi', '1d') if z_sup_1d else None,
                    sl_candidate('tp_short', z_sup_4h, 'hi', '4h') if z_sup_4h else None,
                    sl_candidate('tp_short', z_sup_1h, 'hi', '1h') if z_sup_1h else None,
                    sl_candidate('tp_short', z_sup_15m, 'hi', '15m') if z_sup_15m else None,
                ],
                "rule": "SHORT TP_ref = support zone HI (nearest below price; candidates 1H,15m,4H)"
            },
            "long": {
                "candidates": [
                    # ordered big TF -> small TF
                    sl_candidate('tp_long', z_res_1d, 'lo', '1d') if z_res_1d else None,
                    sl_candidate('tp_long', z_res_4h, 'lo', '4h') if z_res_4h else None,
                    sl_candidate('tp_long', z_res_1h, 'lo', '1h') if z_res_1h else None,
                    sl_candidate('tp_long', z_res_15m, 'lo', '15m') if z_res_15m else None,
                ],
                "rule": "LONG TP_ref = resistance zone LO (nearest above price; candidates 1H,15m,4H)"
            }
        },
        "state": {
            "balance_usdt": state.get("balance_usdt", 1000.0),
            "risk_pct": state.get("risk_pct", 1.0),
            "position": state.get("position"),
            "last_candle_ts_utc": state.get("last_candle_ts_utc"),
        },
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
