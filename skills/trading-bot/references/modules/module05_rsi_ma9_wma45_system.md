# Module 05 — Hệ thống RSI + MA9/WMA45 (thực chiến)

## Mục tiêu
Chuẩn hóa cách đọc RSI theo “range rules” + dùng **SMA-9** (nhanh) và **WMA-45** (chậm) đặt trong **panel RSI** để:
1) Lọc chế độ (regime) — quyết định ưu tiên long/short.
2) Lấy trigger vào/ra lệnh ít nhiễu hơn RSI trần.

## Tham số khuyến nghị
- RSI length: 14 (mặc định).
- SMA (trên RSI): 9.
- WMA (trên RSI): 45.
- Ngưỡng tham chiếu: 40 / 50 / 60 (linh hoạt theo sản phẩm/khung).

## Quy trình 6 bước
1) **Xác nhận regime**
   - Long bias: **SMA-9 > WMA-45** và **WMA-45 dốc lên**; RSI vận động phần lớn **trên ~40**.
   - Short bias: **SMA-9 < WMA-45** và **WMA-45 dốc xuống**; RSI vận động phần lớn **dưới ~60**.

2) **Bối cảnh giá**
   - Chỉ long khi giá trên EMA-50/200; chỉ short khi giá dưới EMA-50/200 (lọc nhiễu).

3) **Trigger**
   - Long: đợi RSI hồi về 40–50 rồi **cắt lên SMA-9** (nến đóng).
   - Short: đợi RSI nảy 50–60 rồi **cắt xuống SMA-9** (nến đóng).

4) **Vào lệnh & dừng lỗ**
   - Entry: ngay sau nến xác nhận (hoặc limit tại 0.382–0.618 retrace của nến tín hiệu).
   - SL: dưới/ trên swing gần nhất **hoặc** ATR(14) × 1.5–2 (tùy biến theo biến động).

5) **Quản lý & thoát**
   - Move SL về hòa vốn khi có R=1 hoặc khi **RSI vượt 60–65 (long)** / rơi dưới 35–40 (short).
   - Chốt phần khi RSI áp 70–80 (long) / 20–30 (short) và momentum chững.
   - **Thoát toàn bộ** nếu **SMA-9 cắt ngược WMA-45** (mất bias) hoặc RSI phá mốc 40/60 theo hướng bất lợi.

6) **Đa khung (MTF)**
   - Khung lớn (trend): H4/D1 → xác lập regime;
   - Khung vào lệnh: M15–H1;
   - Chỉ vào khi **cả 2 khung đều cùng bias**.

## Checklist nhanh
- [ ] WMA-45( RSI ) cùng hướng với bias?
- [ ] SMA-9 ( RSI ) ở đúng phía WMA-45?
- [ ] RSI không ở vùng 40–60 quá lâu (sideways)?
- [ ] Giá đồng pha (EMA-50/200, cấu trúc HH/HL hoặc LL/LH)?
- [ ] Risk ≤ 1–2%/lệnh; R:R tối thiểu 1:1.5–2.

## Sai lầm phổ biến
- Vào giữa vùng 40–60 (rất dễ whipsaw).
- Bỏ qua dốc của WMA-45 (RSI), chỉ nhìn mỗi giao cắt.
- Không đồng bộ bias với cấu trúc giá/MA của **giá**.

## Tối ưu hoá & backtest
- Tối ưu 9/45 thành 8/34 hoặc 10/50 cho từng thị trường.
- Kiểm tra tỷ lệ thắng khi thêm điều kiện “RSI phá trendline” trước trigger.
- Thêm rule “no-trade” khi độ dốc WMA-45 |slope| < ngưỡng (ví dụ < 0.05 điểm RSI / thanh).

> Ghi chú: “Range rules / range shift, failure swing” là các nguyên lý cốt lõi thường gắn với RSI; dùng như bộ lọc để tránh tín hiệu giả trong thị trường đi ngang.
