# WINDBOT — Hướng dẫn quản trị nâng cao

> Tài liệu dành cho nhân viên kỹ thuật EPU/TAF có kinh nghiệm SSH và Linux cơ bản.
> Hướng dẫn cơ bản: xem `docs/guides/admin-guide.md`
> Cập nhật lần cuối: Tháng 4/2026

---

## Mục lục

1. Truy cập VPS qua SSH
2. Quy trình nạp tài liệu chi tiết
3. Quản lý thuật ngữ (nâng cao)
4. Truy vấn lịch sử chat (SQL)
5. Xử lý sự cố nâng cao
6. Quản lý API Key (kỹ thuật)
7. Backup & Khôi phục nâng cao
8. Bảo mật cơ bản

---

## 1. Truy cập VPS qua SSH

### Kết nối
```bash
ssh root@[VPS-IP]
```

### Chuyển sang user botai
```bash
su - botai
cd ~/botai-backend/repo/backend
```

### Thư mục quan trọng
| Đường dẫn | Nội dung |
|---|---|
| /home/botai/botai-backend/repo/ | Root dự án |
| /home/botai/botai-backend/repo/backend/ | Backend FastAPI |
| /home/botai/botai-backend/repo/backend/.env | Biến môi trường (API keys) |
| /home/botai/botai-backend/repo/backend/data/ | Thư mục chứa tài liệu |
| /home/botai/botai-backend/repo/backend/scripts/ | Scripts tiện ích |
| /home/botai/botai-backend/repo/deploy/ | Scripts triển khai |

### Load biến môi trường
```bash
set -a; source .env; set +a
```

---

## 2. Quy trình nạp tài liệu chi tiết

### Bước 1: Chuẩn bị file
- Định dạng hỗ trợ: PDF, DOCX, DOC, PPTX, XLSX, TXT, MD, CSV
- PDF scan được hỗ trợ OCR (Tiếng Việt + English)
- Tên file: chỉ dùng a-z, A-Z, 0-9, `-`, `_`, `.`
- File >20MB có thể mất vài phút

### Bước 2: Upload file lên VPS qua SFTP
Dùng Termius/FileZilla/WinSCP:
- Host: [VPS-IP], User: root, Port: 22
- Navigate: /home/botai/botai-backend/repo/backend/data/
- Tạo folder mới (VD: new_docs_2026-04-15)
- Upload files vào folder

### Bước 3: Fix quyền sở hữu
```bash
# Chạy từ root (không phải botai)
chown -R botai:botai /home/botai/botai-backend/repo/backend/data/[folder-name]/
```

### Bước 4: Chạy script nạp tài liệu
```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/ingest_docs.py --dir ./data/[folder-name]/
```

Options:
| Option | Giá trị | Mặc định | Mô tả |
|---|---|---|---|
| --dir | đường dẫn | (bắt buộc) | Thư mục chứa tài liệu |
| --language | en hoặc vi | en | Ngôn ngữ tài liệu |
| --tier | cost_effective, agentic, agentic_plus | agentic | Chất lượng parsing |

Ví dụ nạp tài liệu tiếng Việt:
```bash
venv/bin/python scripts/ingest_docs.py --dir ./data/new_docs/ --language vi --tier agentic
```

### Bước 5: Rebuild vector index (BẮT BUỘC)
Vào Supabase Dashboard → SQL Editor:
```sql
-- Kiểm tra tên index hiện tại
SELECT indexname FROM pg_indexes
WHERE tablename = 'wind_turbine_docs' AND schemaname = 'vecs';

-- Drop và tạo lại index
DROP INDEX IF EXISTS vecs.ix_vector_cosine_ops_hnsw_m16_efc64_b494534;
CREATE INDEX ix_vector_cosine_ops_hnsw_m16_efc64_b494534
ON vecs.wind_turbine_docs
USING hnsw (vec vector_cosine_ops)
WITH (m=16, ef_construction=64);
```

> Nếu tên index khác, dùng lệnh SELECT ở trên để kiểm tra.

### Bước 6: Restart backend
```bash
exit  # về root
systemctl restart botai-backend
systemctl status botai-backend
curl -s http://localhost:8000/api/health
```

### Bước 7: Cập nhật metadata
Vào Supabase SQL Editor:
```sql
INSERT INTO documents_metadata (filename, file_type, language, num_chunks, ingested_at)
VALUES
('ten-file.pdf', 'pdf', 'vi', [so-chunks], NOW());
```
Thay tên file, loại, ngôn ngữ, số chunks theo kết quả ingest thực tế.

### Bước 8: Kiểm tra
```sql
-- Tổng số vectors
SELECT COUNT(*) as total_vectors FROM vecs."wind_turbine_docs";

-- Vectors theo file
SELECT metadata->>'filename' as filename, COUNT(*) as chunks
FROM vecs."wind_turbine_docs"
GROUP BY metadata->>'filename'
ORDER BY chunks DESC;

-- Metadata
SELECT filename, file_type, num_chunks, ingested_at
FROM documents_metadata
ORDER BY ingested_at DESC;
```

Test chatbot: hỏi câu hỏi liên quan đến nội dung vừa nạp.

---

## 3. Quản lý thuật ngữ (nâng cao)

### Thêm thuật ngữ bằng script
```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/seed_glossary.py
```
> Chỉnh sửa file script hoặc dữ liệu trước khi chạy.

### Thêm trực tiếp qua SQL
```sql
INSERT INTO glossary (term_en, term_vi, definition_en, definition_vi, category)
VALUES (
  'nacelle',
  'vỏ tua-bin',
  'The housing at the top of the tower that contains the generator and gearbox',
  'Phần vỏ bọc trên đỉnh tháp chứa máy phát điện và hộp số',
  'structure'
);
```

Categories hợp lệ: structure, components, operations, maintenance, safety, troubleshooting, general

---

## 4. Truy vấn lịch sử chat (SQL)

### Xem 20 phiên chat gần nhất
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

### Xem chi tiết một phiên chat
```sql
SELECT role, content, created_at
FROM chat_messages
WHERE session_id = '[session-id]'
ORDER BY created_at ASC;
```

### Thống kê sử dụng
```sql
-- Tổng số phiên chat
SELECT COUNT(*) as total_sessions FROM chat_sessions;

-- Tổng số tin nhắn
SELECT COUNT(*) as total_messages FROM chat_messages;

-- Số phiên chat theo ngày (7 ngày gần nhất)
SELECT DATE(created_at) as ngay, COUNT(*) as so_phien
FROM chat_sessions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY ngay DESC;
```

---

## 5. Xử lý sự cố nâng cao

### Xem log backend
```bash
# Log 1 giờ gần nhất
journalctl -u botai-backend --since "1 hour ago" --no-pager

# Log real-time (Ctrl+C để thoát)
journalctl -u botai-backend -f

# Log theo thời gian cụ thể
journalctl -u botai-backend --since "2026-04-15 10:00" --until "2026-04-15 12:00"
```

### Quản lý systemd service
```bash
systemctl status botai-backend   # Xem trạng thái
systemctl restart botai-backend  # Restart
systemctl stop botai-backend     # Dừng
systemctl start botai-backend    # Khởi động
systemctl enable botai-backend   # Bật auto-start khi boot
```

### Kiểm tra tài nguyên
```bash
df -h          # Disk space
free -h        # Memory
top -bn1       # CPU/memory processes
```

### Backend restart liên tục (crash loop)
1. Xem log: `journalctl -u botai-backend --since "10 min ago" --no-pager`
2. Kiểm tra .env: `cat /home/botai/botai-backend/repo/backend/.env | head -5` (xác nhận keys tồn tại)
3. Kiểm tra disk: `df -h` (đảm bảo >10% free)
4. Kiểm tra memory: `free -h` (đảm bảo có RAM trống)
5. Thử chạy thủ công để xem lỗi chi tiết:
```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
6. Đọc error message, xử lý, restart systemd

### Kiểm tra kết nối Supabase
```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
python3 -c "
from supabase import create_client
from app.config import settings
client = create_client(settings.supabase_url, settings.supabase_service_key)
result = client.table('chat_sessions').select('id').limit(1).execute()
print(f'OK: {len(result.data)} rows')
"
```

---

## 6. Quản lý API Key (kỹ thuật)

### Vị trí file .env
```
/home/botai/botai-backend/repo/backend/.env
```

### Chỉnh sửa .env
```bash
ssh root@[VPS-IP]
nano /home/botai/botai-backend/repo/backend/.env
```
- Tìm dòng cần sửa, thay giá trị mới
- Lưu: Ctrl+O → Enter → Ctrl+X
- Restart: `systemctl restart botai-backend`

### Quy trình đổi OpenAI API Key
1. Vào https://platform.openai.com/api-keys
2. Tạo key mới ("Create new secret key")
3. Copy key (chỉ hiển thị 1 lần!)
4. SSH vào VPS, edit .env
5. Thay dòng `OPENAI_API_KEY=sk-...` bằng key mới
6. Lưu file, restart backend
7. Test: `curl -s http://localhost:8000/api/health`
8. Xóa key cũ trên OpenAI dashboard

### Thiết lập spending limit (OpenAI)
1. Vào https://platform.openai.com/account/limits
2. Set "Monthly budget" (VD: $50/tháng)
3. Bật email notification khi đạt threshold

---

## 7. Backup & Khôi phục nâng cao

### Export metadata (hàng tuần)
```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
venv/bin/python scripts/export_data.py --output-dir ./backups/
```

### Export full (bao gồm vector embeddings)
```bash
venv/bin/python scripts/export_data.py --output-dir ./backups/ --include-vectors
```
> Lưu ý: File vector export có thể lớn (hàng trăm MB).

### Khôi phục toàn bộ từ đầu

1. **Setup database:**
   Chạy `supabase_schema.sql` trên Supabase SQL Editor

2. **Chạy migrations:**
   ```sql
   -- File: backend/migrations/add_global_corrections.sql
   -- File: backend/migrations/add_message_feedback.sql
   -- File: backend/supabase_migrations/001_add_fts.sql
   -- File: backend/supabase_migrations/002_fts_add_language.sql
   ```

3. **Nạp lại tài liệu:**
   ```bash
   su - botai
   cd ~/botai-backend/repo/backend
   set -a; source .env; set +a
   venv/bin/python scripts/ingest_docs.py --dir ./data/[folder]/ --language vi
   ```

4. **Seed glossary:**
   ```bash
   venv/bin/python scripts/seed_glossary.py
   ```

5. **Rebuild vector index** (xem mục 2, Bước 5)

6. **Restart backend:**
   ```bash
   exit
   systemctl restart botai-backend
   ```

### Supabase Pro: Restore từ backup
1. Dashboard → Settings → Database → Backups
2. Chọn bản backup theo ngày
3. Nhấn Restore

---

## 8. Bảo mật cơ bản

### Quyền file .env
```bash
chmod 600 /home/botai/botai-backend/repo/backend/.env
chown botai:botai /home/botai/botai-backend/repo/backend/.env
```

### SSH key authentication (khuyến nghị)
Trên máy local:
```bash
ssh-keygen -t ed25519
ssh-copy-id root@[VPS-IP]
```
Sau đó disable password login:
```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
```
Restart SSH: `systemctl restart sshd`

### Firewall cơ bản
```bash
ufw allow 22/tcp    # SSH
ufw allow 8000/tcp  # Backend API
ufw enable
ufw status
```

### Lịch đổi API key
- Khuyến nghị: đổi API key mỗi 3-6 tháng
- Đổi ngay nếu nghi ngờ key bị lộ
- Không bao giờ commit .env vào Git

---

> **Tài liệu liên quan:**
> - Hướng dẫn cơ bản: `docs/guides/admin-guide.md`
> - Phục hồi sự cố: `docs/guides/disaster-recovery.md`
> - Hướng dẫn migration: `docs/guides/migration-guide.md`
