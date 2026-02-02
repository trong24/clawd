# Module 04B — Quán tính RSI (Inertia) & Ứng dụng

Mục tiêu: dùng **quán tính trên RSI** để bám xu hướng, vào sau điều chỉnh, thoát khi lực suy yếu.

## 1) Thiết lập
- RSI: **14**; ngưỡng mạnh **80/20** khi thị trường có trend.
- MA nhanh/chậm trên RSI: **9 / 45**.

## 2) 3 giai đoạn quán tính
**GĐ1 — Bật mạnh**
- Long: RSI ≥80, MA9>MA45, RSI trên cả hai MA.
- Short: RSI ≤20, MA9<MA45, RSI dưới cả hai MA.

**GĐ2 — Điều chỉnh**
- RSI thu hẹp về MA; có thể xuyên tạm khỏi 80/20.
- Nếu RSI hạ mà **giá đi ngang/không giảm** ⇒ lực đối nghịch **yếu**.

**GĐ3 — Hoàn tất / Thất bại**
- **Hoàn tất**: giá vượt đỉnh (long) / đáy (short) của GĐ1.
- **Fail**: long khi **RSI <40**, short khi **RSI >60** trên khung đang quản lý.

## 3) Vào lệnh sau điều chỉnh
- Chỉ vào khi có **đồng thuận MTF**.
- Tái đồng thuận: RSI bật lại cùng hướng, **MA9 tách xa MA45** (mở rộng), RSI ở cùng phía với MA.

## 4) Quản lý lệnh theo quán tính
- Vào H1 ⇒ thường **quản theo M15** (khung lớn nhất còn quán tính).
- Long thoát khi RSI(M15) <40 hoặc MA9 cắt xuống + mất mở rộng (short đối xứng).
- Thực thi R-multiple: chốt 1/2 tại **1R**, dời SL→BE; mục tiêu cơ bản **≥2R**.

## 5) Kháng cự/hỗ trợ HTF
- Sát kháng cự D1/W: **partial** 1/2 + trailing để giảm áp lực tâm lý.

## 6) Tránh
- Bắt đỉnh/đáy ngược HTF.
- Quyết định bằng M1/M3.
- Giao dịch khi RSI 40–60 & MA đan xen.
