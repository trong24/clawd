# MTF Pipeline Skeleton (v0)

Goal: run a deterministic multi-timeframe snapshot, then apply modular analysis.

## Timeframes (placeholder)

- HTF: 4H / 1D
- MTF: 1H
- LTF: 15m
- Entry/Timing: 5m or 1m (testing)

## Modules (contracts)

Each module MUST:
- accept a JSON input (snapshot + upstream module outputs)
- return a JSON output with a stable schema
- include `confidence` (0-1) and `reasons` (bullet strings)

### module_trend
Input: HTF + MTF candles
Output:
- trend: UP|DOWN|RANGE
- structure: HHHL|LHLL|CHOP|UNKNOWN
- invalidation_levels: [{level, why, tf}]
- confidence, reasons

### module_sr (support/resistance)
Input: HTF + MTF candles
Output:
- zones: [{tf, kind: support|resistance, lo, hi, strength, touches, last_touch_utc}]
- nearest_support: {lo, hi, tf, strength} | null
- nearest_resistance: {lo, hi, tf, strength} | null
- candidate_sl: {kind, level, tf, why}[]
- confidence, reasons

### module_regime_wave
Input: MTF + LTF candles
Output:
- regime: TRENDING|RANGING|HIGH_VOL|LOW_VOL|UNKNOWN
- wave_state: IMPULSE|CORRECTION|CHOP|UNKNOWN
- ok_to_trade: boolean
- confidence, reasons

### module_setup_15m
Input: LTF (15m) + outputs(trend,sr,regime_wave) + indicators
Output:
- decision: BUY|SELL|NO_TRADE
- entry: {type: market|limit|trigger, price?, trigger?, why}
- stoploss: {level, based_on: sr_zone_ref, distance_pct, ok_1pct: boolean}
- take_profit: {targets:[{level, rr, why}]}
- invalidate: {level, why}
- confidence, reasons

### module_execution
Input: Entry TF + setup output
Output:
- timing_ok: boolean
- trigger: {conditions: string[]}
- confidence, reasons

## Journaling (placeholder)

Write per run:
- sessions/YYYY/MM/*.session.json (inputs)
- sessions/YYYY/MM/*.output.json (decision + alert + notes)
