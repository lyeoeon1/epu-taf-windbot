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
- **Giờ hỗ trợ:** 9:00 - 17:00, Thứ 2 - Thứ 6 (trừ lễ/tết)
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

---

## 7. Điều khoản bổ sung

- SLA chỉ áp dụng cho phiên bản phần mềm đã bàn giao
- Nếu EPU/TAF tự ý sửa đổi source code, SLA không áp dụng cho phần bị sửa
- Gia hạn SLA: thỏa thuận riêng trước khi hết hạn

---

## 8. Chữ ký

| | Bên cung cấp | Bên sử dụng |
|---|---|---|
| **Ký tên** | _________________ | _________________ |
| **Họ và tên** | _________________ | _________________ |
| **Chức vụ** | _________________ | _________________ |
| **Ngày** | ____/____/________ | ____/____/________ |
