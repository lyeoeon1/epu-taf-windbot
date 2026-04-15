# WINDBOT AI Chatbot - Hướng dẫn quản trị hệ thống

> Tài liệu dành cho nhân viên EPU/TAF quản trị hệ thống chatbot WINDBOT.
> Cập nhật lần cuối: Tháng 4/2026

---

## Mục lục

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Truy cập hệ thống](#2-truy-cập-hệ-thống)
3. [Quản lý tài liệu (Thêm tài liệu mới vào Knowledge Base)](#3-quản-lý-tài-liệu-thêm-tài-liệu-mới-vào-knowledge-base)
4. [Quản lý thuật ngữ (Glossary)](#4-quản-lý-thuật-ngữ-glossary)
5. [Xem lịch sử chat](#5-xem-lịch-sử-chat)
6. [Xử lý sự cố thường gặp](#6-xử-lý-sự-cố-thường-gặp)
7. [Quản lý API Key](#7-quản-lý-api-key)
8. [Backup & Khôi phục](#8-backup--khôi-phục)
9. [Liên hệ hỗ trợ](#9-liên-hệ-hỗ-trợ)

---

## 1. Tổng quan hệ thống

### WINDBOT là gì?

WINDBOT là chatbot trí tuệ nhân tạo (AI) chuyên trả lời các câu hỏi liên quan đến tuabin gió. Hệ thống hoạt động dựa trên tài liệu kỹ thuật đã được nạp vào cơ sở tri thức (knowledge base). Khi người dùng đặt câu hỏi, AI sẽ tìm kiếm thông tin phù hợp trong cơ sở tri thức và tổng hợp câu trả lời chính xác.

### Luồng hoạt động đơn giản

```
Người dùng đặt câu hỏi
    ↓
Frontend gửi câu hỏi đến Backend
    ↓
Backend tìm kiếm nội dung liên quan trong cơ sở tri thức (vector search)
    ↓
AI (OpenAI GPT) tổng hợp câu trả lời dựa trên nội dung tìm được
    ↓
Câu trả lời được stream (gửi từng phần) về cho người dùng
```

### Địa chỉ truy cập

| Thành phần | URL |
|---|---|
| **Frontend** (giao diện chatbot) | https://windbot.vercel.app |
| **Backend API** (máy chủ xử lý) | `http://[VPS-IP]:8000` |
| **API Documentation** | `http://[VPS-IP]:8000/docs` |

---

## 2. Truy cập hệ thống

### 2.1. Frontend (Giao diện chatbot)

- **URL:** https://windbot.vercel.app
- **Đăng nhập:** Hiện tại chưa yêu cầu đăng nhập. Mở trình duyệt và truy cập URL là có thể sử dụng ngay.
- **Trình duyệt hỗ trợ:** Chrome, Firefox, Safari, Edge (phiên bản mới nhất).

### 2.2. Backend API Documentation

- **URL:** `http://[VPS-IP]:8000/docs`
- Đây là trang tài liệu API tự động (Swagger UI). Quản trị viên có thể xem danh sách các endpoint, tham số, và thử gọi API trực tiếp từ giao diện này.

### 2.3. Supabase Dashboard

- **URL:** https://supabase.com/dashboard
- **Đăng nhập:** Sử dụng tài khoản email/mật khẩu của project (được cung cấp khi bàn giao).
- Supabase Dashboard cho phép quản trị viên:
  - Xem và chỉnh sửa dữ liệu trong database
  - Chạy câu lệnh SQL
  - Quản lý cấu hình project
  - Xem backup (nếu dùng gói Pro)

### 2.4. VPS (Máy chủ)

- **Kết nối:** SSH qua terminal hoặc phần mềm SFTP
- **Thông tin:**
  - Host: `[VPS-IP]`
  - User: `root`
  - Port: `22`
  - Xác thực: SSH key hoặc mật khẩu (theo cấu hình bàn giao)

**Ví dụ kết nối SSH từ terminal:**

```bash
ssh root@[VPS-IP]
```

> **Lưu ý:** Truy cập VPS chỉ dành cho các thao tác nâng cao (nạp tài liệu, restart dịch vụ, xem log). Hầu hết các thao tác quản trị thông thường có thể thực hiện qua Supabase Dashboard.

---

## 3. Quản lý tài liệu (Thêm tài liệu mới vào Knowledge Base)

Đây là phần quan trọng nhất trong công việc quản trị. Khi có tài liệu kỹ thuật mới cần bổ sung vào chatbot, hãy thực hiện theo các bước sau:

### Bước 1: Chuẩn bị file

**Định dạng hỗ trợ:**

| Định dạng | Mô tả |
|---|---|
| PDF | Tài liệu PDF (bao gồm cả PDF scan - hỗ trợ OCR tiếng Việt và tiếng Anh) |
| DOCX, DOC | Tài liệu Microsoft Word |
| PPTX | Bài trình chiếu Microsoft PowerPoint |
| XLSX | Bảng tính Microsoft Excel |
| TXT | File văn bản thuần |
| MD | File Markdown |
| CSV | File dữ liệu dạng bảng |

**Quy tắc đặt tên file:**

- Chỉ dùng các ký tự: chữ cái (a-z, A-Z), số (0-9), dấu gạch ngang (`-`), dấu gạch dưới (`_`), dấu chấm (`.`)
- **Tốt:** `huong-dan-bao-tri-tuabin.pdf`, `maintenance_guide_v2.docx`
- **Tránh:** `hướng dẫn bảo trì (v2).pdf`, `tài liệu mới!.docx`

**Lưu ý về kích thước:**

- File lớn hơn 20MB có thể mất vài phút để xử lý.
- Nếu file quá lớn, cân nhắc chia thành nhiều file nhỏ hơn.

### Quy trình tổng quan

Để thêm tài liệu mới vào knowledge base, quy trình gồm 5 bước chính:

1. **Chuẩn bị file** — Đảm bảo đúng định dạng và quy tắc đặt tên
2. **Upload lên máy chủ** — Sử dụng phần mềm SFTP (Termius, FileZilla)
3. **Chạy script nạp** — Script tự động xử lý và đưa vào knowledge base
4. **Cập nhật index** — Rebuild vector index trên Supabase Dashboard
5. **Restart & kiểm tra** — Restart backend và test chatbot

> **Hướng dẫn chi tiết từng bước (bao gồm lệnh SSH):** Xem `docs/guides/admin-guide-advanced.md`, mục "Quy trình nạp tài liệu chi tiết".

Nếu bạn không quen với SSH và dòng lệnh, hãy nhờ nhân viên kỹ thuật hỗ trợ hoặc liên hệ đội ngũ hỗ trợ.

---

## 4. Quản lý thuật ngữ (Glossary)

Hệ thống có sẵn bộ thuật ngữ chuyên ngành tuabin gió để hỗ trợ AI hiểu và trả lời chính xác hơn.

### Thông tin hiện tại

- **Tổng số thuật ngữ:** 87 thuật ngữ song ngữ Việt-Anh
- **Số danh mục:** 7 (structure, components, operations, maintenance, safety, troubleshooting, general)

### Xem danh sách thuật ngữ

Mở trình duyệt tại `http://[VPS-IP]:8000/docs`, tìm endpoint `/api/glossary` và nhấn "Try it out" rồi "Execute".

### Thêm thuật ngữ mới

Vào Supabase Dashboard → **Table Editor** → bảng `glossary` → **Insert Row** → điền thông tin thuật ngữ mới.

> **Thêm nhiều thuật ngữ bằng script:** Xem `docs/guides/admin-guide-advanced.md`, mục "Quản lý thuật ngữ".

---

## 5. Xem lịch sử chat

1. Truy cập https://supabase.com/dashboard
2. Chọn project WINDBOT
3. Vào **Table Editor** (thanh menu bên trái)
4. Chọn bảng:
   - **`chat_sessions`**: Danh sách các phiên chat (mỗi cuộc hội thoại là một session)
   - **`chat_messages`**: Tất cả tin nhắn trong các phiên chat
5. Nhấn vào một session để xem chi tiết tin nhắn

> **Truy vấn nâng cao bằng SQL:** Xem `docs/guides/admin-guide-advanced.md`, mục "Truy vấn lịch sử chat".

---

## 6. Xử lý sự cố thường gặp

### Sự cố bạn có thể tự xử lý

| Vấn đề | Cách khắc phục |
|---|---|
| Response rất chậm (>10 giây) | Kiểm tra [OpenAI Status Page](https://status.openai.com). Nếu OpenAI đang sự cố, chờ vài phút rồi thử lại |
| Lỗi "SSL connection closed" | Vào [Supabase Dashboard](https://supabase.com/dashboard), nhấn nút **Restore** để khôi phục project |
| Frontend hiển thị lỗi trắng | Xóa cache trình duyệt (Ctrl+Shift+R). Nếu vẫn lỗi, kiểm tra [Vercel Dashboard](https://vercel.com/dashboard) |
| Lỗi kết nối (không mở được trang) | Kiểm tra VPS đang chạy từ dashboard nhà cung cấp VPS |

### Sự cố cần nhân viên kỹ thuật

| Vấn đề | Cần làm |
|---|---|
| Chatbot không phản hồi (backend down) | Nhân viên kỹ thuật SSH vào VPS và restart service |
| Không tìm thấy nội dung mới nạp | Cần rebuild vector index (xem hướng dẫn nâng cao) |
| Lỗi "Permission denied" | Cần fix quyền file trên VPS |

> **Hướng dẫn xử lý sự cố nâng cao (SSH, logs, systemd):** Xem `docs/guides/admin-guide-advanced.md`, mục "Xử lý sự cố nâng cao".
> **Kế hoạch phục hồi khi sự cố nghiêm trọng:** Xem `docs/guides/disaster-recovery.md`.

---

## 7. Quản lý API Key

Hệ thống sử dụng 3 dịch vụ bên ngoài cần API Key:

### 7.1. OpenAI API Key

| Thông tin | Chi tiết |
|---|---|
| **Mục đích** | Cung cấp mô hình AI (GPT) để tạo câu trả lời |
| **Dashboard** | https://platform.openai.com/api-keys |
| **Xem mức sử dụng** | https://platform.openai.com/usage |
| **Chi phí ước tính** | ~$5-20/tháng tùy lượng sử dụng |

### 7.2. Supabase

| Thông tin | Chi tiết |
|---|---|
| **Mục đích** | Database (PostgreSQL) và vector storage |
| **Dashboard** | https://supabase.com/dashboard |
| **Gói hiện tại** | Free tier (500MB database, 1GB file storage) |

**Lưu ý quan trọng:** Supabase Free tier sẽ **tự động tạm dừng (pause)** project nếu không có hoạt động trong 7 ngày. Đảm bảo có ít nhất 1 lượt sử dụng chatbot mỗi tuần, hoặc nâng cấp lên gói Pro ($25/tháng).

### 7.3. LlamaCloud API Key

| Thông tin | Chi tiết |
|---|---|
| **Mục đích** | Xử lý tài liệu khi nạp vào knowledge base |
| **Dashboard** | https://cloud.llamaindex.ai/ |
| **Khi nào cần** | Chỉ cần khi nạp tài liệu mới. Không cần cho chat thông thường. |

> **File mẫu cấu hình:** Xem `backend/.env.example` để biết danh sách đầy đủ các biến môi trường cần thiết.
> **Quy trình đổi API key (SSH vào VPS):** Xem `docs/guides/admin-guide-advanced.md`, mục "Quản lý API Key".

---

## 8. Backup & Khôi phục

### Tổng quan

Hệ thống có script `export_data.py` để xuất toàn bộ dữ liệu (lịch sử chat, thuật ngữ, metadata...). Nhờ nhân viên kỹ thuật chạy script định kỳ hàng tuần.

### Supabase Backup

| Gói | Backup |
|---|---|
| **Free tier** | Không có backup tự động. Cần dùng `export_data.py` |
| **Pro tier** ($25/tháng) | Backup tự động hàng ngày. Vào Dashboard → Settings → Database → Backups |

> **Hướng dẫn chi tiết backup & khôi phục:** Xem `docs/guides/admin-guide-advanced.md`, mục "Backup & Khôi phục nâng cao".
> **Kế hoạch phục hồi khi mất dữ liệu:** Xem `docs/guides/disaster-recovery.md`.

---

## 9. Liên hệ hỗ trợ

### Trong thời gian SLA (3 tháng kể từ ngày bàn giao)

| Thông tin | Chi tiết |
|---|---|
| **Email** | [email hỗ trợ - xem tài liệu bàn giao] |
| **Kênh liên hệ** | Email / GitHub Issues |

### Thời gian phản hồi cam kết

| Mức độ | Thời gian phản hồi |
|---|---|
| **Critical** (hệ thống ngừng hoạt động hoàn toàn) | Trong vòng 4 giờ |
| **Normal** (lỗi nhỏ, câu hỏi, yêu cầu hỗ trợ) | Trong vòng 2 ngày làm việc |

### Tài liệu tham khảo thêm

- Chi tiết cam kết SLA: xem file `docs/handover/sla.md`
- Tài liệu kiến trúc hệ thống: xem thư mục `docs/architecture/`
- Hướng dẫn triển khai: xem thư mục `docs/deployment/`

---

> **Lời khuyên:** Lưu lại tài liệu này và quay lại tra cứu khi cần. Nếu gặp vấn đề không có trong mục "Xử lý sự cố", hãy liên hệ đội ngũ hỗ trợ qua các kênh nêu trên.
