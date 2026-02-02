# Module Output Schemas (Skeleton)

All modules return JSON.

Common fields:
- `module`: string
- `version`: string (e.g. "0.1")
- `confidence`: number (0..1)
- `reasons`: string[]
- `errors`: string[] (optional)

## trend
```json
{
  "module": "trend",
  "version": "0.1",
  "trend": "UP|DOWN|RANGE|UNKNOWN",
  "structure": "HHHL|LHLL|CHOP|UNKNOWN",
  "invalidation_levels": [{"level": 0, "why": "", "tf": ""}],
  "confidence": 0.0,
  "reasons": []
}
```

## sr
```json
{
  "module": "sr",
  "version": "0.1",
  "zones": [{"tf": "", "kind": "support|resistance", "lo": 0, "hi": 0, "strength": 0, "touches": 0, "last_touch_utc": ""}],
  "nearest_support": {"tf": "", "lo": 0, "hi": 0, "strength": 0},
  "nearest_resistance": {"tf": "", "lo": 0, "hi": 0, "strength": 0},
  "candidate_sl": [{"kind": "buy|sell", "level": 0, "tf": "", "why": ""}],
  "confidence": 0.0,
  "reasons": []
}
```

## regime_wave
```json
{
  "module": "regime_wave",
  "version": "0.1",
  "regime": "TRENDING|RANGING|HIGH_VOL|LOW_VOL|UNKNOWN",
  "wave_state": "IMPULSE|CORRECTION|CHOP|UNKNOWN",
  "ok_to_trade": false,
  "confidence": 0.0,
  "reasons": []
}
```

## setup_15m
```json
{
  "module": "setup_15m",
  "version": "0.1",
  "decision": "BUY|SELL|NO_TRADE",
  "entry": {"type": "market|limit|trigger", "price": 0, "trigger": "", "why": ""},
  "stoploss": {"level": 0, "based_on": "sr_zone_ref", "distance_pct": 0, "ok_1pct": false, "why": ""},
  "take_profit": {"targets": [{"level": 0, "rr": 0, "why": ""}]},
  "confidence": 0.0,
  "reasons": []
}
```
