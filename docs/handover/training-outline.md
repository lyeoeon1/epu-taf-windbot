# KẾ HOẠCH ĐÀO TẠO BÀN GIAO HỆ THỐNG WINDBOT

**Dự án:** AI Chatbot Tua-bin Gió (WINDBOT)

---

## 1. Thông tin chung

- **Thời lượng dự kiến:** 2-3 giờ
- **Hình thức:** Trực tiếp (tại EPU/TAF)
- **Đối tượng:** Đội ngũ quản lý và vận hành hệ thống
- **Yêu cầu:** Laptop có kết nối internet, trình duyệt Chrome/Firefox

---

## 2. Nội dung đào tạo

### Phần 1: Tổng quan hệ thống (30 phút)

- Giới thiệu WINDBOT: mục đích, tính năng, kiến trúc
- Demo live: hỏi đáp về tua-bin gió (Tiếng Việt + English)
- Giải thích luồng hoạt động: câu hỏi → RAG retrieval → AI → streaming response
- Các thành phần: Frontend (Vercel), Backend (VPS), Database (Supabase), AI (OpenAI)

### Phần 2: Hướng dẫn quản trị cơ bản (45 phút)

- Truy cập hệ thống (URLs, dashboards)
- Thực hành: Thêm tài liệu mới vào knowledge base (step-by-step demo)
- Thực hành: Xem lịch sử chat trên Supabase
- Thực hành: Kiểm tra health của hệ thống
- Quản lý API keys và chi phí

### Phần 3: Xử lý sự cố (30 phút)

- Các lỗi thường gặp và cách khắc phục
- Demo: Restart backend service
- Demo: Kiểm tra logs
- Demo: Rebuild vector index
- Khi nào cần liên hệ hỗ trợ

### Phần 4: Quản lý hạ tầng (30 phút)

- VPS: SSH access, systemd service management
- Vercel: Frontend deployment, environment variables
- Supabase: Dashboard, SQL Editor, backups
- Giám sát chi phí: OpenAI usage, Supabase usage

### Phần 5: Hỏi đáp (15 phút)

- Giải đáp thắc mắc
- Xác nhận thông tin liên hệ hỗ trợ
- Nhắc lại SLA và quy trình báo lỗi

---

## 3. Tài liệu phát cho học viên

- Bản in `docs/guides/admin-guide.md`
- Bản in `docs/handover/sla.md`
- Thông tin access credentials (bàn giao trực tiếp)

---

## 4. Tiêu chí hoàn thành đào tạo

- Học viên có thể tự thêm tài liệu mới vào knowledge base
- Học viên biết cách xử lý các sự cố cơ bản
- Học viên biết cách liên hệ hỗ trợ khi cần

---

## 5. Ghi chú

Nội dung đào tạo có thể điều chỉnh theo nhu cầu thực tế của EPU/TAF.
