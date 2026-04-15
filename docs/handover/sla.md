# THỎA THUẬN HỖ TRỢ SAU TRIỂN KHAI (SLA)

**Dự án:** AI Chatbot Tua-bin Gió (WINDBOT)

---

## 1. Thông tin chung

- **Ngày hiệu lực:** [ngày bàn giao]
- **Thời hạn:** 3 tháng kể từ ngày bàn giao
- **Bên cung cấp:** [Nhóm phát triển]
- **Bên sử dụng:** EPU/TAF

---

## 2. Phân loại sự cố

| Mức độ | Mô tả | Ví dụ | Thời gian phản hồi | Thời gian xử lý |
|--------|--------|-------|---------------------|------------------|
| Critical | Hệ thống ngừng hoạt động hoàn toàn | Backend down, database không kết nối | ≤4 giờ | ≤24 giờ |
| Normal | Lỗi chức năng ảnh hưởng trải nghiệm | Chatbot trả lời sai, streaming lỗi, tìm kiếm không chính xác | ≤2 ngày làm việc | ≤5 ngày làm việc |
| Minor | Lỗi giao diện, cosmetic | Lỗi hiển thị, typo, font | ≤5 ngày làm việc | ≤10 ngày làm việc |

---

## 3. Phạm vi hỗ trợ (Included)

- Sửa lỗi phần mềm (bugs) trong code hiện tại
- Hướng dẫn sử dụng và vận hành hệ thống
- Hỗ trợ nạp tài liệu mới vào knowledge base
- Cập nhật nhỏ (minor updates) không thay đổi kiến trúc
- Hỗ trợ renew API keys (OpenAI, Supabase, LlamaCloud)

---

## 4. Ngoài phạm vi (Excluded)

- Phát triển tính năng mới (feature requests)
- Tích hợp VR360
- Thay đổi kiến trúc hệ thống
- Migration sang model/hosting khác
- Đào tạo thêm ngoài buổi bàn giao
- Sự cố do bên thứ 3 (OpenAI outage, Supabase downtime, VPS provider)

---

## 5. Kênh tiếp nhận

- **Email:** [placeholder]
- **GitHub Issues:** [placeholder repo URL]
- **Giờ hỗ trợ:** 9:00 - 17:00 (GMT+7, giờ Việt Nam), Thứ 2 - Thứ 6 (trừ lễ/tết)
- **Ngoài giờ:** chỉ xử lý sự cố Critical

---

## 6. Quy trình báo lỗi

Khi phát hiện lỗi, vui lòng sử dụng template sau:

```
Tiêu đề: [Mức độ] Mô tả ngắn
Mô tả chi tiết: ...
Bước tái hiện: 1. ... 2. ... 3. ...
Kết quả mong đợi: ...
Kết quả thực tế: ...
Screenshots/Logs (nếu có): ...
```

> **Cách thu thập logs:** Xem hướng dẫn tại `docs/guides/admin-guide-advanced.md`, mục "Xử lý sự cố nâng cao".

---

## 7. Điều khoản bổ sung

- SLA chỉ áp dụng cho phiên bản phần mềm đã bàn giao.
- Nếu EPU/TAF tự ý sửa đổi source code, SLA không áp dụng cho phần bị sửa.
- Gia hạn SLA: thỏa thuận riêng trước khi hết hạn.

### Quy trình escalation

Nếu sự cố không được xử lý trong thời gian cam kết:

1. Gửi email nhắc nhở (reply lại email ban đầu).
2. Nếu sau 24 giờ (Critical) hoặc 3 ngày làm việc (Normal) vẫn chưa phản hồi, liên hệ trực tiếp lead developer qua điện thoại.
3. Mọi escalation sẽ được ghi nhận và xử lý ưu tiên.

### Sau khi hết thời hạn SLA

Sau 3 tháng, EPU/TAF có các lựa chọn:

1. **Gia hạn SLA** — Thỏa thuận hợp đồng hỗ trợ mới với phạm vi và chi phí cụ thể.
2. **Tự vận hành** — Sử dụng tài liệu hướng dẫn đã bàn giao (`docs/guides/admin-guide.md`, `docs/guides/disaster-recovery.md`) để tự quản lý hệ thống.
3. **Thuê bên thứ 3** — Chuyển giao vận hành cho đơn vị CNTT khác. Toàn bộ source code và tài liệu đã thuộc về EPU/TAF.

> **Khuyến nghị:** Liên hệ ít nhất 2 tuần trước khi SLA hết hạn để thảo luận phương án tiếp theo.

---

## 8. Chữ ký

| | Bên cung cấp | Bên sử dụng |
|---|---|---|
| **Ký tên** | _________________ | _________________ |
| **Họ và tên** | _________________ | _________________ |
| **Chức vụ** | _________________ | _________________ |
| **Ngày** | ____/____/________ | ____/____/________ |
