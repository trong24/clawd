# Module 04E — RSI, Quán Tính & Đồng Thuận Đa Khung (Bản Cô Đọng Huấn Luyện LLM)

## Tóm tắt trọng tâm
- **RSI >50** ưu tiên long; **RSI <50** ưu tiên short.
- MA9 và MA45 đặt trên RSI để đo quán tính: MA9 phía trên MA45 cho bias tăng và ngược lại.
- Đồng thuận đa khung: anchor (H4/D1) xác định xu hướng; khung tín hiệu (H1) và khung vào lệnh (M15) phải đồng pha.

## Quy trình rút gọn
1. **Xác định anchor**: chọn khung lớn (H4/D1) và đánh giá RSI + MA9/45 để biết xu hướng chính.
2. **Tìm tín hiệu**: ở khung trung gian (H1), chờ RSI hồi nhưng vẫn giữ trên 50 (long) hoặc dưới 50 (short).
3. **Kích hoạt quán tính**: chuyển xuống khung vào lệnh (M15) và đợi RSI chạm ≥80 (long) hoặc ≤20 (short) để xác nhận đà.
4. **Thực thi & quản lý**: vào lệnh sau nến xác nhận; quản lý theo M15, thoát khi RSI mất quán tính (<40 long / >60 short).

## Q&A nhanh
- **Hỏi:** Vì sao cần MA9 và MA45 trên RSI?
  **Đáp:** Hai đường MA cho biết quán tính của RSI; khi MA9 cách xa và cùng hướng với MA45, đà hiện tại mạnh và đáng tin cậy.
- **Hỏi:** Dấu hiệu mất đồng thuận MTF là gì?
  **Đáp:** Khi anchor nghiêng tăng nhưng H1 rơi dưới 50 và MA9 cắt xuống MA45, tín hiệu và anchor lệch pha nên tạm dừng lệnh.

## Checklist
- [ ] Anchor H4/D1 xác nhận bias rõ ràng?
- [ ] RSI khung tín hiệu duy trì >50 (long) / <50 (short)?
- [ ] MA9 và MA45 trên RSI đang **mở rộng** theo hướng bias?
- [ ] Khung vào lệnh xuất hiện quán tính ≥80 (long) / ≤20 (short)?
- [ ] Rủi ro ≤2%/lệnh và R:R tối thiểu 1:1.5?
