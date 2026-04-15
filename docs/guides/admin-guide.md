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

- Chi dung cac ky tu: chu cai (a-z, A-Z), so (0-9), dau gach ngang (`-`), dau gach duoi (`_`), dau cham (`.`)
- **Tốt:** `huong-dan-bao-tri-tuabin.pdf`, `maintenance_guide_v2.docx`
- **Tránh:** `hướng dẫn bảo trì (v2).pdf`, `tài liệu mới!.docx`

**Lưu ý về kích thước:**

- File lớn hơn 20MB có thể mất vài phút để xử lý.
- Nếu file quá lớn, cân nhắc chia thành nhiều file nhỏ hơn.

### Bước 2: Upload file lên VPS

Sử dụng phần mềm SFTP để tải file lên máy chủ. Các phần mềm phổ biến:

- **Termius** (khuyên dùng - hỗ trợ cả Windows, macOS, mobile)
- **FileZilla** (miễn phí, Windows/macOS/Linux)
- **WinSCP** (miễn phí, chỉ Windows)

**Các bước thực hiện:**

1. Mở phần mềm SFTP, tạo kết nối mới với thông tin:
   - **Host:** `[VPS-IP]`
   - **User:** `root`
   - **Port:** `22`
   - **Xác thực:** SSH key hoặc mật khẩu

2. Sau khi kết nối thành công, điều hướng đến thư mục:
   ```
   /home/botai/botai-backend/repo/backend/data/
   ```

3. Tạo thư mục mới với tên gợi nhớ, ví dụ:
   ```
   new_docs_2026-04-15
   ```

4. Upload tất cả file tài liệu vào thư mục vừa tạo.

### Bước 3: Fix quyền sở hữu file

Sau khi upload xong, SSH vào VPS với quyền root và chạy lệnh sau để đổi quyền sở hữu file cho user `botai`:

```bash
ssh root@[VPS-IP]
```

```bash
chown -R botai:botai /home/botai/botai-backend/repo/backend/data/[folder-name]/
```

**Ví dụ cụ thể:**

```bash
chown -R botai:botai /home/botai/botai-backend/repo/backend/data/new_docs_2026-04-15/
```

> **Giải thích:** Bước này đảm bảo user `botai` (user chạy backend) có quyền đọc các file vừa upload. Nếu bỏ qua bước này, script nạp tài liệu sẽ báo lỗi "Permission denied".

### Bước 4: Chạy script nạp tài liệu

Chuyển sang user `botai` và chạy script ingest:

```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/ingest_docs.py --dir ./data/[folder-name]/ --language vi
```

**Ví dụ cụ thể:**

```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/ingest_docs.py --dir ./data/new_docs_2026-04-15/ --language vi
```

**Các tùy chọn (options) quan trọng:**

| Tùy chọn | Giá trị | Mô tả |
|---|---|---|
| `--language` | `vi` hoặc `en` | Ngôn ngữ chính của tài liệu. Mặc định: `vi` |
| `--tier` | `cost_effective` | Tiết kiệm chi phí, phù hợp cho hầu hết tài liệu |
| `--tier` | `agentic` | Chất lượng cao hơn, chi phí cao hơn |
| `--tier` | `agentic_plus` | Chất lượng cao nhất, chi phí cao nhất |

> **Lưu ý:** Quá trình nạp tài liệu có thể mất từ vài phút đến vài chục phút tùy thuộc vào số lượng và kích thước file. Theo dõi output trên terminal để biết tiến trình.

### Bước 5: Rebuild vector index

Sau khi nạp tài liệu xong, cần rebuild lại vector index để hệ thống tìm kiếm hiệu quả hơn.

1. Truy cập **Supabase Dashboard** (https://supabase.com/dashboard)
2. Chọn project WINDBOT
3. Vào mục **SQL Editor** (thanh menu bên trái)
4. Dán và chạy lần lượt hai câu lệnh sau:

**Lệnh 1 - Xóa index cũ:**

```sql
DROP INDEX IF EXISTS vecs.ix_vector_cosine_ops_hnsw_m16_efc64_b494534;
```

**Lệnh 2 - Tạo index mới:**

```sql
CREATE INDEX ix_vector_cosine_ops_hnsw_m16_efc64_b494534
ON vecs.wind_turbine_docs
USING hnsw (vec vector_cosine_ops)
WITH (m=16, ef_construction=64);
```

> **Lưu ý:** Mỗi lệnh chạy riêng, nhấn nút "Run" cho từng lệnh. Lệnh tạo index mới có thể mất 1-2 phút nếu cơ sở tri thức lớn.

### Bước 6: Restart backend

Quay lại terminal SSH (với quyền root) và restart dịch vụ backend:

```bash
exit  # thoát khỏi user botai, quay về root
systemctl restart botai-backend
```

Kiểm tra trạng thái dịch vụ:

```bash
systemctl status botai-backend
```

Kết quả mong đợi: trạng thái hiển thị **active (running)** với màu xanh lá.

### Bước 7: Cập nhật metadata (tùy chọn)

Để theo dõi lịch sử nạp tài liệu, thêm thông tin metadata vào bảng `documents_metadata` qua Supabase SQL Editor:

```sql
INSERT INTO documents_metadata (filename, file_type, language, num_chunks, ingested_at) 
VALUES ('filename.pdf', 'pdf', 'vi', [num_chunks], NOW());
```

**Ví dụ cụ thể:**

```sql
INSERT INTO documents_metadata (filename, file_type, language, num_chunks, ingested_at) 
VALUES ('huong-dan-bao-tri-tuabin.pdf', 'pdf', 'vi', 45, NOW());
```

> **Mẹo:** Số lượng chunks (`num_chunks`) có thể xem trong output của script `ingest_docs.py` ở Bước 4.

### Bước 8: Kiểm tra kết quả

1. **Kiểm tra chatbot:** Truy cập https://windbot.vercel.app và đặt câu hỏi liên quan đến nội dung tài liệu vừa nạp. Chatbot cần trả lời được dựa trên nội dung mới.

2. **Kiểm tra số lượng vector:** Vào Supabase SQL Editor, chạy:

```sql
SELECT COUNT(*) FROM vecs."wind_turbine_docs";
```

Kết quả trả về phải lớn hơn số trước khi nạp tài liệu.

### Tổng kết quy trình nạp tài liệu

```
Chuẩn bị file → Upload lên VPS → Fix quyền → Chạy ingest → Rebuild index → Restart backend → Kiểm tra
```

---

## 4. Quản lý thuật ngữ (Glossary)

Hệ thống có sẵn bộ thuật ngữ chuyên ngành tuabin gió để hỗ trợ AI hiểu và trả lời chính xác hơn.

### Thông tin hiện tại

- **Tổng số thuật ngữ:** 87 thuật ngữ
- **Số danh mục:** 7

| Danh mục | Mô tả |
|---|---|
| `structure` | Cấu trúc tuabin gió |
| `components` | Các bộ phận, linh kiện |
| `operations` | Vận hành |
| `maintenance` | Bảo trì, bảo dưỡng |
| `safety` | An toàn |
| `troubleshooting` | Xử lý sự cố |
| `general` | Thuật ngữ chung |

### Xem danh sách thuật ngữ

Truy cập API endpoint:

```
GET http://[VPS-IP]:8000/api/glossary
```

Hoặc mở trình duyệt tại `http://[VPS-IP]:8000/docs`, tìm endpoint `/api/glossary` và nhấn "Try it out" rồi "Execute".

### Thêm thuật ngữ mới

**Cách 1: Sử dụng script (khuyên dùng cho nhiều thuật ngữ)**

```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/seed_glossary.py
```

> **Lưu ý:** Chỉnh sửa file script hoặc file dữ liệu tương ứng trước khi chạy để thêm thuật ngữ mới.

**Cách 2: Thêm trực tiếp qua Supabase**

Vào Supabase Dashboard, chọn **Table Editor**, tìm bảng `glossary`, nhấn **Insert Row** và điền thông tin thuật ngữ mới.

---

## 5. Xem lịch sử chat

### Qua Supabase Dashboard

1. Truy cập https://supabase.com/dashboard
2. Chọn project WINDBOT
3. Vào **Table Editor** (thanh menu bên trái)
4. Chọn bảng:
   - **`chat_sessions`**: Danh sách các phiên chat (mỗi cuộc hội thoại là một session)
   - **`chat_messages`**: Tất cả tin nhắn trong các phiên chat

### Xem các phiên chat gần nhất bằng SQL

Vào **SQL Editor** trên Supabase Dashboard và chạy:

```sql
SELECT 
    cs.id, 
    cs.title, 
    cs.created_at, 
    COUNT(cm.id) as message_count
FROM chat_sessions cs
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
GROUP BY cs.id, cs.title, cs.created_at
ORDER BY cs.created_at DESC 
LIMIT 20;
```

Kết quả hiển thị 20 phiên chat gần nhất, kèm tiêu đề và số lượng tin nhắn.

### Xem nội dung chi tiết một phiên chat

```sql
SELECT role, content, created_at
FROM chat_messages
WHERE session_id = '[session-id]'
ORDER BY created_at ASC;
```

Thay `[session-id]` bằng ID của phiên chat muốn xem (lấy từ truy vấn trước đó).

---

## 6. Xử lý sự cố thường gặp

| Vấn đề | Nguyên nhân có thể | Cách khắc phục |
|---|---|---|
| Chatbot không phản hồi | Backend bị dừng (down) | SSH vào VPS, chạy: `systemctl restart botai-backend` |
| Response rất chậm (>10 giây) | OpenAI API đang chậm hoặc quá nhiều request cùng lúc | Kiểm tra [OpenAI Status Page](https://status.openai.com), chờ vài phút rồi thử lại |
| Lỗi kết nối (không mở được trang) | VPS bị dừng hoặc lỗi mạng | Kiểm tra VPS đang chạy hay không. Nếu VPS dừng, restart từ nhà cung cấp VPS |
| Không tìm thấy nội dung mới nạp | Chưa rebuild vector index | Chạy lệnh DROP + CREATE INDEX trên Supabase SQL Editor (xem Bước 5 mục 3) |
| Lỗi "SSL connection closed" | Supabase project bị tạm dừng (pause) do không hoạt động | Vào Supabase Dashboard, nhấn nút **Restore** để khôi phục project |
| Lỗi "Permission denied" khi chạy ingest | File vừa upload thuộc quyền root | Chạy: `chown -R botai:botai /home/botai/botai-backend/repo/backend/data/[folder]/` |
| Frontend hiển thị lỗi trắng | Có thể do Vercel deploy lỗi hoặc cache trình duyệt | Xóa cache trình duyệt (Ctrl+Shift+R). Nếu vẫn lỗi, kiểm tra Vercel Dashboard |

### Xem log backend để chẩn đoán

```bash
ssh root@[VPS-IP]
journalctl -u botai-backend --since "1 hour ago" --no-pager
```

Hoặc xem log trực tiếp (real-time):

```bash
journalctl -u botai-backend -f
```

Nhấn `Ctrl+C` để thoát chế độ xem real-time.

---

## 7. Quản lý API Key

Hệ thống sử dụng ba dịch vụ bên ngoài cần API Key. Các key này được lưu trong file `.env` trên VPS tại:

```
/home/botai/botai-backend/repo/backend/.env
```

### 7.1. OpenAI API Key

OpenAI cung cấp mô hình AI (GPT) để tạo câu trả lời.

| Thông tin | Chi tiết |
|---|---|
| **Dashboard** | https://platform.openai.com/api-keys |
| **Xem mức sử dụng** | https://platform.openai.com/usage |
| **Chi phí ước tính** | ~$5-20/tháng tùy lượng sử dụng |
| **Biến môi trường** | `OPENAI_API_KEY` |

**Quy trình đổi API Key:**

1. Vào https://platform.openai.com/api-keys
2. Tạo key mới (nhấn "Create new secret key")
3. Sao chep key mới (chỉ hiển thị một lần)
4. SSH vào VPS:
   ```bash
   ssh root@[VPS-IP]
   nano /home/botai/botai-backend/repo/backend/.env
   ```
5. Tìm dòng `OPENAI_API_KEY=...`, thay bằng key mới
6. Lưu file (Ctrl+O, Enter, Ctrl+X)
7. Restart backend:
   ```bash
   systemctl restart botai-backend
   ```

### 7.2. Supabase

Supabase cung cấp database (PostgreSQL) và vector storage.

| Thông tin | Chi tiết |
|---|---|
| **Dashboard** | https://supabase.com/dashboard |
| **Gói hiện tại** | Free tier |
| **Giới hạn Free tier** | 500MB database, 1GB file storage |
| **Biến môi trường** | `SUPABASE_URL`, `SUPABASE_KEY` |

**Lưu ý quan trọng:**

- Supabase Free tier sẽ **tự động tạm dừng (pause)** project nếu không có hoạt động trong 7 ngày.
- Khi bị pause, chatbot sẽ không hoạt động và hiển thị lỗi "SSL connection closed".
- **Cách khắc phục:** Vào Supabase Dashboard, chọn project, nhấn nút **Restore project**.
- Để tránh bị pause: đảm bảo có ít nhất 1 lượt sử dụng chatbot mỗi tuần, hoặc nâng cấp lên gói Pro ($25/tháng).

### 7.3. LlamaCloud API Key

LlamaCloud hỗ trợ xử lý tài liệu khi nạp vào knowledge base.

| Thông tin | Chi tiết |
|---|---|
| **Dashboard** | https://cloud.llamaindex.ai/ |
| **Biến môi trường** | `LLAMA_CLOUD_API_KEY` |
| **Khi nào cần** | Chỉ cần khi nạp tài liệu mới (chạy `ingest_docs.py`). Không cần cho chức năng chat thông thường. |

---

## 8. Backup & Khôi phục

### 8.1. Export dữ liệu

Sử dụng script `export_data.py` để xuất toàn bộ dữ liệu:

```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/export_data.py
```

Script sẽ tạo file export trong thư mục hiện tại. Tải file về máy cá nhân qua SFTP để lưu trữ an toàn.

### 8.2. Backup tự động (Supabase)

| Gói | Backup |
|---|---|
| **Free tier** | Không có backup tự động. Sử dụng `export_data.py` hoặc SQL export thủ công. |
| **Pro tier** ($25/tháng) | Backup tự động hàng ngày. Vào Dashboard -> Settings -> Database -> Backups để xem và khôi phục. |

### 8.3. Backup thủ công qua SQL export

Trên Supabase Dashboard:

1. Vào **SQL Editor**
2. Chạy lệnh export cho từng bảng cần backup
3. Tải kết quả về dưới dạng CSV

### 8.4. Khôi phục dữ liệu

**Trường hợp 1: Khôi phục từ Supabase backup (gói Pro)**

1. Vào Supabase Dashboard -> Settings -> Database -> Backups
2. Chọn bản backup theo ngày mong muốn
3. Nhấn **Restore**

**Trường hợp 2: Khôi phục từ đầu**

Nếu cần thiết lập lại toàn bộ database:

1. Chạy lại schema SQL:
   ```bash
   su - botai
   cd ~/botai-backend/repo/backend
   set -a; source .env; set +a
   venv/bin/python scripts/setup_supabase.py
   ```
   Hoặc chạy file `supabase_schema.sql` trực tiếp trên Supabase SQL Editor.

2. Nạp lại tài liệu (thực hiện lại quy trình tại [Mục 3](#3-quản-lý-tài-liệu-thêm-tài-liệu-mới-vào-knowledge-base)).

3. Nạp lại glossary:
   ```bash
   venv/bin/python scripts/seed_glossary.py
   ```

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
- Tài liệu kỹ thuật backend: xem thư mục `docs/backend/`
- Tài liệu kỹ thuật frontend: xem thư mục `docs/frontend/`

---

> **Lời khuyên:** Lưu lại tài liệu này và quay lại tra cứu khi cần. Nếu gặp vấn đề không có trong mục "Xử lý sự cố", hãy liên hệ đội ngũ hỗ trợ qua các kênh nêu trên.
