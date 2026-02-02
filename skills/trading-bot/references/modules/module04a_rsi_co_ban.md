# Module 04A — RSI cơ bản

## 1) RSI là gì?
- Dao động 0–100, đo cân bằng **lực mua vs lực bán**.
- Mức ý nghĩa:
  - >50: thiên mua; <50: thiên bán.
  - Xu hướng mạnh: dùng ngưỡng 80/20 thay vì 70/30.

## 2) Cấu hình khuyến nghị
- RSI length: **14**
- Hai đường **MA trên RSI**: **9** (nhanh) & **45** (chậm) để đọc quán tính trên chính RSI.

## 3) Cách đọc nhanh
- **Đồng pha tăng**: RSI>50, RSI nằm **trên** MA9 & MA45, và **MA9>MA45**.
- **Đồng pha giảm**: đối xứng.
- **Sideways**: RSI lắc 40–60, MA9↔MA45 đan xen.

## 4) Sai lầm thường gặp
- Dùng tín hiệu “RSI chạm 70/30 là đảo chiều” → **sai trong xu hướng mạnh**.
- Nhảy vào lệnh chỉ vì **RSI cắt MA** một lần → cần bối cảnh MTF & mở rộng MA.

## 5) Checklist
- [ ] Khung anchor nghiêng hướng nào?
- [ ] RSI khung vào lệnh >50 (long) / <50 (short)?
- [ ] Vị trí RSI so với MA9/MA45? MA có **mở rộng** không?
