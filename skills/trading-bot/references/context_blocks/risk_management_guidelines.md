# Risk Management Guidelines (Machine-Readable-ish)

- risk_per_trade_pct = 0.5
- max_daily_loss_pct = 2.0
- min_R_multiple = 2.0
- sizing_rule: size = floor( (NAV_USDT * risk_per_trade_pct/100) / abs(entry - stop) )
- partials: take 50% at 1R, move stop to BE; remainder trailing = EMA20_1h
- hard NOs: no averaging losers; avoid trades within 30m of high-impact news
