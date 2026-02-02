# RSI Cheatsheet (dựa trên thực hành + nguyên lý “range rules”)

## Vùng động lượng (range rules) & bias
- Bull range khỏe: RSI thường dao động ~40–80/90; nhịp hồi **giữ trên ~40**.
- Bear range khỏe: RSI thường dao động ~10/20–60; nhịp hồi **kẹt dưới ~60**.
- Vùng 40–60 là “trung tính/sideways”: dễ whipsaw → ưu tiên chờ thêm bằng chứng.

## MA trên RSI (SMA-9 & WMA-45)
- **SMA-9 (nhanh)**: nhịp ngắn, báo cắt sớm; tốt cho trigger.
- **WMA-45 (chậm, có trọng số)**: xu hướng nền (regime filter). WMA-45 **hướng lên** + SMA-9 **trên** WMA-45 ⇒ long bias (ngược lại cho short bias).

## Trigger mẫu
- Long: trong bull bias, đợi RSI hồi về 40–50 rồi **cắt lên SMA-9**.
- Short: trong bear bias, đợi RSI nảy lên 50–60 rồi **cắt xuống SMA-9**.

## Quản trị lệnh
- Mất bias: **SMA-9 cắt ngược** qua WMA-45 hoặc RSI đánh rơi mốc 40 (với long) / vượt hẳn 60 (với short) ⇒ xem xét thoát/giảm vị thế.
- Chốt bậc thang: khi RSI áp 70–80 (long) / 20–30 (short) mà đà chậm lại.

## Mẫu hình RSI hữu ích
- **Failure Swing**: phá đỉnh/đáy RSI rồi đảo ngược thất bại ⇒ tín hiệu đảo chiều.
- **Range Shift**: RSI chuyển “vùng hoạt động” (ví dụ từ 20–60 sang 40–80) ⇒ thay đổi chế độ.
- **Trendline trên RSI**: phá trendline RSI thường sớm hơn phá cấu trúc giá.

## Lưu ý
- Sideways: 2 đường MA trên RSI quấn chặt ⇒ đứng ngoài hoặc hạ khung vị thế.
- MA = có trễ; bù lại giảm nhiễu.
- Luôn kết hợp cấu trúc giá (swing high/low), ATR cho SL, và MTF để tăng xác suất.
