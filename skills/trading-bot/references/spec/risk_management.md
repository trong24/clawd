# Risk Management Notes (human-readable)

- Risk per trade: 0.5% NAV (tùy chỉnh).
- Max daily loss: 2% NAV, chạm ngưỡng thì dừng giao dịch trong ngày.
- Minimum R multiple: 2.0 (kèo < 2R thì bỏ).
- Sizing rule: size = floor( (NAV_USDT * risk_per_trade_pct/100) / |entry - stop| ).
- Partial take-profit: chốt 50% tại 1R, dời stop về BE; phần còn lại trailing theo EMA20 1h.
- Không trung bình giá thua; tránh trade sát giờ news quan trọng.
