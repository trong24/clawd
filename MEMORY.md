# MEMORY.md - Long-Term Memory

This is my curated memory — distilled wisdom, not raw logs. Daily files in `memory/` have the details.

---

## About Trong (my human)
- Vietnamese speaker, timezone GMT+7
- Learning RSI-based trading system from video materials
- Risk tolerance: 1% per trade
- Prefers zone-based S/R, not just pivot points
- Exit policy: force-based on managing TF, adaptive TP

## Trading Rules I've Learned

### Entry
- MTF confluence required: HTF (1D, 4H) + LTF (15m) must align
- No trade if fueling/conflict regime (HTF vs LTF disagree)
- SL from nearest S/R zone (prefer 1H, fallback 15m)
- Size = (balance × risk_pct) / SL_distance

### Exit (Close Logic)
- **RSI 40-60 = WARNING, not auto-close** (clarified 2026-01-31)
- Close only when:
  - 15m bias flips opposite to position
  - SL hit
  - Adaptive TP at HTF S/R (discretionary, not auto)
- Never close just because price hit HTF S/R (needs force confirmation)

### Indicators
- RSI(14) + EMA9(RSI) + WMA45(RSI)
- Rule A (midline 50): UP/DOWN/RANGE
- Rule B (band 40/60): BULLISH/BEARISH/NEUTRAL (hướng, chưa mạnh)
- Rule C (extreme 80/20): **TRUE STRONG** — RSI > 80 hoặc < 20 mới là mạnh thực sự

**RSI Zones:**
- > 80: overbought, momentum cực mạnh
- 60-80: bullish nhưng chưa extreme
- 40-60: balance zone, không trade
- 20-40: bearish nhưng chưa extreme
- < 20: oversold, momentum cực mạnh

## Code Architecture

### Trading bot files
- `trading/cron_15m_context.py` — generates JSON context for LLM
- `trading/cron_15m_bot.py` — deterministic bot (no LLM)
- `trading/apply_15m_decision.py` — logs LLM decisions to CSV
- `skills/trading-bot/scripts/snapshot_mtf.py` — fetches candles from Binance
- `skills/trading-bot/scripts/module_trend_mtf.py` — labels trend per TF
- `skills/trading-bot/scripts/module_sr_mtf.py` — detects S/R zones

### State files
- `trading/state_15m.json` — position, balance, risk
- `trading/trades_15m.csv` — trade log

## Lessons Learned
1. Always check function bodies after `return` — orphan code is unreachable
2. Rule changes need code updates — spec vs implementation drift is dangerous
3. CSV schemas must align across all writers
4. Workspace identity files matter for continuity
5. **Phân tích lực = xem history dài (120-240 candles)**, không chỉ 1 thời điểm
6. **LLM-first approach:** Chỉ fetch raw numbers, LLM tự phân tích — không code thống kê máy móc
7. **Quán tính:** Đọc flow của RSI theo thời gian — peaks/troughs đang cao dần hay thấp dần?
8. **Regime từ pattern:** Bull range (40-80, hồi > 40) vs Bear range (20-60, rally < 60)

---

*Last updated: 2026-02-02*
