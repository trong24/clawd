---
name: trading-bot
description: Futures BTC/crypto trading analysis + alert workflow for OpenClaw. Use when running cron-based trading checks, generating BTCUSDT signals from Binance data, formatting Telegram alerts, journaling decisions, and proposing spec updates the user approves.
---

# Trading Bot (alert-first, futures)

## Default contract

- **Mode:** alert-only (no order placement)
- **Market:** Binance data (public)
- **Primary:** BTCUSDT
- **Timeframe:** 15m (cron), optionally 1m for testing
- **Risk rule (account-based):** risk per trade is **~1% of account balance** (max loss if SL is hit; fees not included). Choose the stop level based on the **nearest support/resistance** + invalidation; then compute **position size** from `(entry - SL)` (or `(SL - entry)` for shorts) so that the loss at SL ≈ 1% of account balance. If the required stop is too wide/tight for sensible sizing/liquidity, propose **NO TRADE** or adjust (user approval required).
- **Mindset rule:** always prioritize discipline + prebuilt scenarios; if performance degrades, audit psychology/discipline before changing the system.
- **No revenge trading:** after a loss, do not immediately "gỡ" / revenge-trade; pause and re-check plan.
- **Probabilistic thinking:** treat trades as a sequence of probabilities; aim for consistency, not prediction.
- **Scenario-based trading (2-way):** prebuild If-Up / If-Down conditions ("kịch bản"); avoid directional prediction.
- **Consistent + flexible:** be consistent with rules, but switch when signals invalidate the scenario (avoid stubbornness).
- **Avoid being pulled by price chart:** if you feel "bị cuốn theo đồ thị giá", pause and re-check the plan.
- **Signal wave vs profit wave:** accept missing the extreme; prioritize entries on the *signal wave* ("sóng tín hiệu"), aim to harvest the *profit wave* ("sóng lợi nhuận").
- **Risk-first at entry:** define SL + max loss acceptance immediately when entering; if you cannot define a stop/invalidation, it's **NO TRADE**.
- **TP is adaptive (avoid chốt non):** combine (A) no hard exchange TP by default (manage exits by conditions), and (B) keep a TP *reference* (target zone) but do not auto-close the whole position there; keep monitoring trend strength/"lực" and exit when signals deteriorate.
- **Daily plan budget:** spend ~30 minutes/day to build scenarios; otherwise just check if price is following the plan (reduce OMO/overtrading).
- **3-step workflow:** Plan (kịch bản + risk) → Enter → Manage (monitor "lực" / market pressure).
- **Regime expectation (60/40):** expect ~60% of time in accumulation/range/adjustment and ~40% in clear trends; default to **NO TRADE** in unclear regimes.
- **50/50 (fueling) regime:** when buy/sell pressure is effectively balanced → edge is low; do not force tools; wait for confirmation (signal wave).
- **Fuel = psychology:** strong/fast moves can reduce participation (people fear buying high); expect pauses/adjustments that rebuild acceptance.
- **Habituation/anchoring:** time-at-level matters; sideways builds acceptance at new price levels.
- **Itchy-hands guardrail:** during fueling/range, either trade smaller/less, or stay out until a clear signal appears.
- **Regime override on conflicts:** when indicators/tools are conflicting/"ngược pha" → treat as fueling regime; shift to capital preservation (smaller/less trades or NO TRADE).
- **WYSIWYT (what you see is what you think):** avoid prediction; act on what is confirmed by the market.
- **Avoid holy-grail chasing:** in hard/sideways regimes, do not switch systems impulsively; diagnose regime first.
- **Regime vs system:** drawdowns during choppy regimes do not imply the system is broken; change rules/tools only after regime diagnosis.
- **"Yếu" is context-only:** treat "yếu" as a scenario/context helper, not an entry trigger.
- **Probability segmentation:** prefer legs with clear edge (e.g., "80%" setups); exit around 50/50 zones and wait for the next signal wave before re-entering.
- **Not fighting the market (greed/FOMO):** in 50/50 or choppy regimes, you're usually fighting your own greed/FOMO; default to NO TRADE to protect prior gains.
- **SL as business cost:** treat stoploss as a normal business expense to find/participate in winning legs (not a personal failure).
- **Trend loop:** in a strong trend, repeat: enter on signal → exit/stand aside on bad signal → re-enter when trend resumes.
- **Price = psychology/force:** read moves as buy/sell pressure, not just candle direction.
- **MTF = participant mapping:** timeframes represent different participant groups; use MTF to avoid misreading and to align trades.
- **MTF build-up:** trends often start on small TFs and propagate upward; strong trends emerge when multiple TF/participant groups align.
- **Transcript + evidence policy:**
  - Ưu tiên dùng **Browser Relay (profile=chrome)** để xem video đang chạy và đọc minh hoạ trực tiếp.
  - Auto-transcript có thể nhiễu → dùng để lấy timestamp/quote khi có.
  - Nếu **không lấy được transcript**: vẫn được viết note theo **những gì thấy trên chart/video**, nhưng phải gắn nhãn **(ƯỚC LƯỢNG)** ở phần Quote(s) và **không được nâng rule lên confirmed** chỉ dựa trên đoạn này (chỉ để draft).

- **Capture policy (training-only):**
  - Capture chỉ để hiểu trong lúc training, **không lưu**.
  - Chỉ lưu ảnh khi user nói rõ “lưu lại” hoặc khi assistant đề xuất “key visual” và hỏi user 1 câu để confirm.

- **Rule lifecycle:**
  - Rule mới từ video note mặc định là **draft**.
  - Chỉ chuyển **draft → confirmed** khi user trả lời “confirm” (hoặc tương đương).
  - Cron/trading logic chỉ ưu tiên áp dụng rules **confirmed**.

- **Exit policy (cron 15m) — UPDATE #1 (user approved):**
  - **Chỉ được CLOSE theo kỹ thuật lực (force-based) trên TF quản trị (15m).**
  - **Không được CLOSE chỉ vì chạm HTF support/resistance hoặc vì đã lời nhiều R.**
  - Nếu muốn bảo toàn lợi nhuận mà chưa có tín hiệu CLOSE kỹ thuật: ghi "Kế hoạch quản trị" (ví dụ dời SL/giảm rủi ro) nhưng quyết định chính vẫn là **HOLD**.

- **Rule naming + structure:**
  - Format: `Pxx — <định nghĩa 1 câu>`. Trong note/index luôn có thêm `Why:` (1 câu) + `Anti-misuse:` (1 câu “không dùng để …”).
  - Tags ngắn gọn, nhất quán để search: `#force #adjustment #mtf #manage #context_only #no_prediction`.

- **Question discipline (khi training):**
  - Mặc định **không hỏi user** trong lúc training.
  - Nhưng nếu có chỗ **không hiểu/chưa rõ** (sau khi đã tự rà + thử diễn giải lại): **bắt buộc** hỏi user để làm rõ.
  - Giới hạn: được hỏi **nhiều câu nếu cần**, nhưng phải **gộp trong 1 message** và tối đa **3 câu**/block (đánh số 1–3), mỗi câu kèm nhãn **(CẦN LÀM RÕ)**.

- **Per-block quality checklist:**
  - Self-check nội dung: có mơ hồ/mâu thuẫn với rules confirmed hiện tại không?
  - Self-check ngôn ngữ: chính tả / ngữ pháp / độ rõ (khó hiểu thì sửa ngay).
  - Nếu không chắc: ghi rule dạng **draft**, không tự suy diễn thành confirmed.

## Trend definition (MTF) — your system

Define trend using **RSI(14)** and two moving averages of RSI:
- EMA9(RSI14)
- WMA45(RSI14)

**Update (scope):** Bỏ qua phân tích theo **đường trung bình (baseline) trên đồ thị giá** (price MA baseline). Chỉ dùng MA của **RSI**, không dùng MA của **giá** để ra quyết định/trình bày.

Rules:
- **Rule A (midline 50):**
  - UP if RSI>50 AND EMA(RSI)>WMA(RSI)
  - DOWN if RSI<50 AND EMA(RSI)<WMA(RSI)
  - else RANGE/TRANSITION
- **Rule B (band 40/60) — direction bias:**
  - BULLISH if RSI>60 AND EMA>WMA
  - BEARISH if RSI<40 AND EMA<WMA
  - else NEUTRAL (balance zone)
- **Rule C (extreme 80/20) — true momentum strength:**
  - STRONG (overbought) if RSI > 80
  - STRONG (oversold) if RSI < 20
  - 60-80 / 20-40 = có hướng nhưng chưa mạnh thực sự

**RSI Zones cheat sheet:**
| Zone | RSI | Ý nghĩa |
|------|-----|---------|
| Overbought mạnh | > 80 | Momentum cực mạnh, có thể điều chỉnh |
| Bullish | 60-80 | Có hướng tăng, chưa extreme |
| Balance | 40-60 | Cân bằng, không rõ trend |
| Bearish | 20-40 | Có hướng giảm, chưa extreme |
| Oversold mạnh | < 20 | Momentum cực mạnh, có thể bounce |

Additional concept (video-derived):
- **RSI ~50 balance zone:** when RSI oscillates around 50 (roughly 40–60), buy/sell pressure is near-balanced → trend is unclear → default to WAIT/NO TRADE until a clear signal wave forms.
- **Close-on-bad-force (TF-specific):** manage and close based on the same TF you entered on. "Bad force" = the current trend ends and either (a) RSI returns to the sideway/balance zone (~40–60), or (b) the system flips to the opposite bias (e.g., in a LONG, signals start indicating SHORT; in a SHORT, signals start indicating LONG).
- **RSI overbought/oversold is not auto-reversal:** do not auto-short at RSI>70 (even with divergence) and do not auto-long at RSI<30. Use RSI 70/30 and 80/20 as *context*; require trend/regime confirmation.
- **RSI extreme follows trend:** in strong trends, interpret RSI extremes as force confirmation; keep actions trend-aligned (uptrend: buy/wait; downtrend: sell/wait). Note: a pullback/adjustment signal is clearer when RSI **leaves** the extreme zone (breaks down from high / breaks up from low), not merely by being extreme.
- **Divergence (RSI) = adjustment warning:** treat divergence as a weakening/adjustment warning, not a reversal call; never use divergence alone as an entry trigger.

MTF priority (bias): 1D → 4H → 1H → 15m.
- **MTF confluence (strong trend):** treat a trend as strong only when multiple timeframes/tools are aligned ("đồng vọng/đồng thuận").
- **Kỷ luật hold:** Đã vào lệnh = chờ đến SL hoặc TP. Không close vì "không move", "RSI hồi chút", hoặc "không chắc chắn". Commit to the plan.

## Folder structure

```
skills/trading-bot/
├── SKILL.md                    ← BẠN ĐANG ĐÂY - entry point, rules chính
├── scripts/                    ← Python scripts (fetch data, tính toán)
│   ├── snapshot_mtf.py         ← fetch candles từ Binance
│   ├── module_trend_mtf.py     ← legacy trend labels
│   ├── module_sr_mtf.py        ← legacy S/R zones
│   └── run_signal.py           ← legacy single-TF signal
└── references/
    ├── glossary_vi.md          ← thuật ngữ tiếng Việt
    ├── modules/                ← 10 training modules (mindset, RSI, MTF...)
    ├── context_blocks/         ← cheatsheets (RSI, risk management)
    ├── spec/                   ← trader_spec.yaml, risk_management.md
    ├── templates/              ← prompt templates
    └── video_notes/            ← notes từ 4 videos đã học
```

## Files to use

- **Glossary (terms):** `references/glossary_vi.md`
- **RSI cheatsheet:** `references/context_blocks/rsi_cheatsheet.md`
- **Risk rules:** `references/context_blocks/risk_management_guidelines.md`
- **Trading spec:** `references/spec/trader_spec.yaml`
- **Training modules:** `references/modules/` (RSI, MTF, psychology...)
- **Video notes:** `references/video_notes/` (learned from videos)

## Market snapshot (deterministic)

### Multi-timeframe snapshot (preferred)

- Script: `scripts/snapshot_mtf.py`
- Example:
  - `python3 skills/trading-bot/scripts/snapshot_mtf.py --symbol BTCUSDT --tfs 1d,4h,1h,15m --limit 210`

This snapshot includes per-timeframe indicators:
- RSI14
- EMA9(RSI14)
- WMA45(RSI14)

## Phân tích lực (LLM-first approach)

**QUAN TRỌNG:** Không dùng code Python để tính toán thống kê (avg, %, distribution). Chỉ fetch số liệu thô, rồi LLM tự đọc và phân tích.

### Nguyên tắc phân tích:

1. **Xem history dài (120-240 candles)** — không chỉ 1 thời điểm
   - 1D: 60+ candles (2 tháng)
   - 4H: 120+ candles (20 ngày)
   - 1H: 120+ candles (5 ngày)
   - 15m: 200+ candles (2 ngày)

2. **Đọc quán tính (momentum flow):**
   - RSI đang tăng hay giảm theo thời gian?
   - Peaks đang cao dần hay thấp dần?
   - Troughs đang cao dần hay thấp dần?
   - Bounce/pullback đến đâu rồi quay đầu?

3. **Xác định regime từ pattern:**
   - **Bull range:** RSI 40-80, hồi giữ > 40, peaks thường > 60
   - **Bear range:** RSI 20-60, rally kẹt < 60, peaks thường < 60
   - Regime shift cần thấy pattern thay đổi, không chỉ 1 điểm

4. **RSI extreme (Rule C):**
   - **> 80:** Overbought mạnh (momentum cực mạnh)
   - **60-80:** Bullish nhưng chưa extreme
   - **40-60:** Balance zone — WAIT
   - **20-40:** Bearish nhưng chưa extreme
   - **< 20:** Oversold mạnh (momentum cực mạnh, có thể bounce)

5. **Context script:** `trading/cron_15m_context.py`
   - Chỉ fetch raw numbers
   - Không tính trend labels, S/R, hay SL/TP
   - LLM đọc số và tự phân tích theo rules trên

### Single-timeframe signal (legacy / quick tests)

- Script: `scripts/run_signal.py`
- Example:
  - 15m: `python3 skills/trading-bot/scripts/run_signal.py --symbol BTCUSDT --interval 15m --limit 210 --rsi-buy-max 60 --rsi-sell-min 40`
  - 1m test: `python3 skills/trading-bot/scripts/run_signal.py --symbol BTCUSDT --interval 1m --limit 210 --rsi-buy-max 60 --rsi-sell-min 40`

If `error=true`, treat it as a transient data failure.

## Decision workflow (agent)

Use the pipeline skeleton in `references/mtf_pipeline.md`.

Skeleton (v0):
1) Get snapshot JSON from `run_signal.py` (single-TF now; multi-TF later).
2) If `signal=NONE`: **do not alert** (unless running a test cron).
3) If `signal=BUY/SELL`:
   - (Placeholder) apply MTF reasoning using `references/modules/`.
   - Enforce futures risk rule: stoploss must be based on nearest S/R AND distance ≈ 1% from entry.
   - If that constraint cannot be satisfied: output **NO TRADE**.
   - Output an alert message.

## Telegram alert format (short)

Use 1 message:

- `[BTCUSDT 15m] BUY|SELL`
- `Giá: ...`
- `RSI14: ... | EMA9: ... | WMA45: ...`
- `SL (≈1%): <level> | Lý do: <nearest S/R>`
- `Reason: <reason>`
- `UTC: <ts_utc>`

## Journaling (learning loop)

After each **decision-bearing** run (BUY/SELL), write a pair under your training repo layout:

- `sessions/YYYY/MM/YYYY-MM-DD_NN.session.json`
- `sessions/YYYY/MM/YYYY-MM-DD_NN.output.json`

Include:
- snapshot JSON
- final alert text
- whether trade was valid under the 1% + S/R rule

## Spec updates (user-approved)

When you identify a recurring mistake (false positives, stop placement issues, volatility regime):
- propose a **small patch** to `references/spec/trader_spec.yaml` or a specific module file
- do **not** auto-edit without explicit user approval
- keep a changelog note in the output message (1–2 lines)
