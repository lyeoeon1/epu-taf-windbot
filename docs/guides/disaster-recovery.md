# Disaster Recovery Guide — WINDBOT

> Tài liệu hướng dẫn khôi phục hệ thống WINDBOT khi gặp sự cố.
> Cập nhật: 2026-04-15

## Tổng quan hệ thống

| Thành phần | Công nghệ | Địa chỉ / Vị trí |
|---|---|---|
| Frontend | Next.js (Vercel) | https://windbot.vercel.app |
| Backend | FastAPI + Gunicorn (systemd) | VPS — service `botai-backend` |
| Database | Supabase PostgreSQL + pgvector | Supabase Dashboard |
| LLM | OpenAI `gpt-4.1-mini` | api.openai.com |
| Code | Git repository | `/home/botai/botai-backend/repo/` |
| User | `botai` | VPS |

---

## 1. Ma trận sự cố

| # | Sự cố | Mức độ | Thời gian phục hồi | Rủi ro mất dữ liệu | Ghi chú |
|---|---|---|---|---|---|
| 1 | Backend down | Cao | 5–15 phút | Không | Service crash hoặc OOM |
| 2 | Database mất kết nối | Cao | 10–30 phút | Không (nếu DB còn) | Connection string sai, Supabase pause |
| 3 | VPS hỏng hoàn toàn | Nghiêm trọng | 1–3 giờ | Không (code trên Git, data trên Supabase) | Cần provision VPS mới |
| 4 | Supabase bị pause | Trung bình | 5–10 phút | Không | Free tier tự pause sau 7 ngày không hoạt động |
| 5 | OpenAI outage | Trung bình | Không kiểm soát | Không | Phụ thuộc OpenAI khắc phục |
| 6 | Mất dữ liệu (DB) | Nghiêm trọng | 1–4 giờ | Có | Cần restore từ backup hoặc re-ingest |
| 7 | Vercel down | Thấp | Không kiểm soát | Không | Frontend tĩnh, hiếm khi xảy ra |
| 8 | API key hết hạn / bị revoke | Trung bình | 5–10 phút | Không | OpenAI hoặc Supabase key |

---

## 2. Quy trình phục hồi

### 2.1 Backend down

**Triệu chứng:** Frontend trả lỗi 502/503, API không phản hồi.

**Bước 1 — SSH vào VPS:**

```bash
ssh botai@<VPS_IP>
```

**Bước 2 — Kiểm tra trạng thái service:**

```bash
sudo systemctl status botai-backend
```

Nếu thấy `inactive (dead)` hoặc `failed`, tiếp tục bước 3.

**Bước 3 — Xem log để xác định nguyên nhân:**

```bash
sudo journalctl -u botai-backend --since "1 hour ago" --no-pager | tail -100
```

Các nguyên nhân thường gặp:
- **OOM killed**: kiểm tra `dmesg | grep -i oom`
- **Port conflict**: `sudo lsof -i :8000`
- **Python error**: lỗi import, thiếu dependency

**Bước 4 — Restart service:**

```bash
sudo systemctl restart botai-backend
```

**Bước 5 — Xác minh hoạt động:**

```bash
# Chờ 5 giây để service khởi động
sleep 5
sudo systemctl status botai-backend
curl -s http://localhost:8000/health | python3 -m json.tool
```

Nếu vẫn fail, kiểm tra file `.env` và dependencies:

```bash
cd /home/botai/botai-backend/repo/
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart botai-backend
```

---

### 2.2 Database mất kết nối

**Triệu chứng:** Backend trả lỗi 500, log hiển thị `connection refused` hoặc `timeout`.

**Bước 1 — Kiểm tra Supabase Dashboard:**

Truy cập https://supabase.com/dashboard → chọn project → kiểm tra trạng thái:
- Nếu project bị **Paused** → xem mục 2.4
- Nếu project **Active** → tiếp tục bước 2

**Bước 2 — Kiểm tra connection string trong `.env`:**

```bash
ssh botai@<VPS_IP>
cd /home/botai/botai-backend/repo/
grep -i "supabase\|database\|postgres" .env
```

So sánh với thông tin trong Supabase Dashboard → Settings → Database → Connection string.

**Bước 3 — Test kết nối trực tiếp:**

```bash
cd /home/botai/botai-backend/repo/
source .venv/bin/activate
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
result = client.table('documents').select('id').limit(1).execute()
print('OK — connected, rows:', len(result.data))
"
```

**Bước 4 — Nếu connection string thay đổi, cập nhật `.env` và restart:**

```bash
nano /home/botai/botai-backend/repo/.env
# Sửa SUPABASE_URL, SUPABASE_KEY, DATABASE_URL
sudo systemctl restart botai-backend
```

---

### 2.3 VPS hỏng hoàn toàn

**Triệu chứng:** Không SSH được, VPS provider báo server down, không thể khôi phục.

**Bước 1 — Provision VPS mới** (Ubuntu 22.04+ khuyến nghị):

Đặt VPS mới từ provider. Ghi nhận IP mới.

**Bước 2 — Tạo user và cấu hình cơ bản:**

```bash
ssh root@<NEW_VPS_IP>

# Tạo user botai
adduser botai
usermod -aG sudo botai

# Cấu hình firewall
ufw allow OpenSSH
ufw allow 8000
ufw enable
```

**Bước 3 — Cài đặt dependencies:**

```bash
su - botai

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx
```

**Bước 4 — Clone repo và setup môi trường:**

```bash
mkdir -p /home/botai/botai-backend
cd /home/botai/botai-backend
git clone <REPO_URL> repo
cd repo

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Bước 5 — Khôi phục file `.env`:**

Copy file `.env` từ backup hoặc tạo lại từ template:

```bash
cp .env.example .env
nano .env
# Điền các giá trị:
#   SUPABASE_URL=https://xxx.supabase.co
#   SUPABASE_KEY=eyJ...
#   OPENAI_API_KEY=sk-...
#   DATABASE_URL=postgresql://...
```

**Bước 6 — Tạo systemd service:**

```bash
sudo tee /etc/systemd/system/botai-backend.service > /dev/null <<'EOF'
[Unit]
Description=WINDBOT Backend (FastAPI + Gunicorn)
After=network.target

[Service]
User=botai
Group=botai
WorkingDirectory=/home/botai/botai-backend/repo
Environment="PATH=/home/botai/botai-backend/repo/.venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/home/botai/botai-backend/repo/.env
ExecStart=/home/botai/botai-backend/repo/.venv/bin/gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable botai-backend
sudo systemctl start botai-backend
```

**Bước 7 — Xác minh:**

```bash
sudo systemctl status botai-backend
curl -s http://localhost:8000/health
```

**Bước 8 — Cập nhật DNS / Vercel environment:**

- Cập nhật IP mới trong Vercel → Settings → Environment Variables → `NEXT_PUBLIC_API_URL`
- Redeploy frontend trên Vercel

---

### 2.4 Supabase bị pause

**Triệu chứng:** Backend log hiện `connection refused`. Supabase Dashboard hiển thị "Project paused".

**Bước 1 — Restore project:**

1. Đăng nhập https://supabase.com/dashboard
2. Chọn project WINDBOT
3. Nhấn **Restore project**
4. Chờ 2–5 phút để project khởi động hoàn tất

**Bước 2 — Xác minh database:**

Trong Supabase Dashboard → SQL Editor, chạy:

```sql
SELECT count(*) FROM documents;
SELECT count(*) FROM glossary;
```

**Bước 3 — Restart backend:**

```bash
ssh botai@<VPS_IP>
sudo systemctl restart botai-backend
sleep 5
curl -s http://localhost:8000/health
```

---

### 2.5 OpenAI outage

**Triệu chứng:** Chat trả lỗi 502/503 từ OpenAI, hoặc timeout.

**Bước 1 — Kiểm tra trạng thái OpenAI:**

Truy cập https://status.openai.com/ — xem có incident nào đang xảy ra không.

**Bước 2 — Kiểm tra API trực tiếp:**

```bash
ssh botai@<VPS_IP>
cd /home/botai/botai-backend/repo/
source .venv/bin/activate
python3 -c "
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
r = client.chat.completions.create(
    model='gpt-4.1-mini',
    messages=[{'role':'user','content':'ping'}],
    max_tokens=5
)
print('OK:', r.choices[0].message.content)
"
```

**Bước 3 — Nếu outage kéo dài (> 4 giờ):**

Cân nhắc chuyển tạm sang model khác (nếu backend hỗ trợ):

```bash
# Trong .env, thay đổi model
# OPENAI_MODEL=gpt-4.1-mini  →  OPENAI_MODEL=gpt-4o-mini
nano /home/botai/botai-backend/repo/.env
sudo systemctl restart botai-backend
```

> **Lưu ý:** Chỉ chuyển model khi đã test kỹ. Nhớ chuyển lại sau khi OpenAI khôi phục.

---

### 2.6 Mất dữ liệu (Database)

**Triệu chứng:** Bảng trống, dữ liệu bị xóa, schema hỏng.

**Bước 1 — Kiểm tra backup trên Supabase:**

Supabase Dashboard → Settings → Database → Backups

- Nếu có backup gần → **Restore** từ backup (chỉ khả dụng với plan Pro)
- Nếu không có backup → tiếp tục bước 2

**Bước 2 — Tạo lại schema:**

```bash
ssh botai@<VPS_IP>
cd /home/botai/botai-backend/repo/
source .venv/bin/activate
```

Chạy file SQL tạo schema (trong Supabase SQL Editor hoặc qua psql):

```sql
-- Bật extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Bảng documents
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng glossary
CREATE TABLE IF NOT EXISTS glossary (
    id BIGSERIAL PRIMARY KEY,
    term TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bảng conversations
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index cho vector search
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

**Bước 3 — Re-ingest tài liệu:**

```bash
cd /home/botai/botai-backend/repo/
source .venv/bin/activate
python3 -m app.ingest --source ./data/documents/
```

**Bước 4 — Seed glossary:**

```bash
python3 -m app.seed_glossary --file ./data/glossary.csv
```

**Bước 5 — Rebuild vector index:**

Trong Supabase SQL Editor:

```sql
REINDEX INDEX idx_documents_embedding;
```

**Bước 6 — Xác minh:**

```sql
SELECT count(*) FROM documents;
SELECT count(*) FROM glossary;
SELECT count(*) FROM documents WHERE embedding IS NOT NULL;
```

---

### 2.7 Vercel down

**Triệu chứng:** https://windbot.vercel.app không truy cập được, nhưng API backend vẫn hoạt động.

**Bước 1 — Kiểm tra trạng thái Vercel:**

Truy cập https://www.vercel-status.com/

**Bước 2 — Nếu Vercel hoạt động bình thường:**

1. Đăng nhập https://vercel.com/dashboard
2. Chọn project WINDBOT
3. Kiểm tra tab **Deployments** — xem deployment gần nhất có lỗi không
4. Nếu deployment lỗi → nhấn **Redeploy** trên commit gần nhất thành công

**Bước 3 — Nếu Vercel outage toàn cầu:**

Chờ Vercel khắc phục. Theo dõi tại https://www.vercel-status.com/. Không có hành động nào khác có thể thực hiện.

---

### 2.8 API key hết hạn hoặc bị revoke

**Triệu chứng:** Backend log hiện `401 Unauthorized` hoặc `Invalid API key`.

**Bước 1 — Xác định key nào bị lỗi:**

```bash
ssh botai@<VPS_IP>
sudo journalctl -u botai-backend --since "30 min ago" --no-pager | grep -i "401\|unauthorized\|invalid.*key\|api.*key"
```

**Bước 2 — Tạo key mới:**

- **OpenAI:** https://platform.openai.com/api-keys → Create new secret key
- **Supabase:** Supabase Dashboard → Settings → API → Copy `anon` key hoặc `service_role` key

**Bước 3 — Cập nhật `.env`:**

```bash
cd /home/botai/botai-backend/repo/
nano .env
# Cập nhật key tương ứng:
#   OPENAI_API_KEY=sk-proj-...
#   SUPABASE_KEY=eyJ...
```

**Bước 4 — Restart và xác minh:**

```bash
sudo systemctl restart botai-backend
sleep 5
curl -s http://localhost:8000/health
sudo journalctl -u botai-backend --since "1 min ago" --no-pager | tail -20
```

---

## 3. Chiến lược backup

### Lịch backup

| Tần suất | Loại backup | Nội dung | Lưu trữ |
|---|---|---|---|
| Hàng tuần (Chủ nhật) | Metadata export | `documents` (không kèm vector), `glossary`, `conversations` | VPS `/home/botai/backups/` + Git |
| Hàng tháng (ngày 1) | Full export (kèm vectors) | Toàn bộ database kèm cột `embedding` | VPS `/home/botai/backups/` + cloud storage |
| Sau mỗi lần ingest | Log ingest | Ghi nhận: thời gian, số tài liệu, nguồn, người thực hiện | File log `/home/botai/backups/ingest-log.csv` |

### Lệnh backup

**Backup metadata hàng tuần (không kèm vector):**

```bash
#!/bin/bash
# /home/botai/scripts/backup-weekly.sh

BACKUP_DIR="/home/botai/backups"
DATE=$(date +%Y%m%d)
mkdir -p "$BACKUP_DIR"

cd /home/botai/botai-backend/repo/
source .venv/bin/activate

python3 -c "
import os, json, csv
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Export documents (metadata only, no embedding)
docs = client.table('documents').select('id,content,metadata,created_at').execute()
with open('$BACKUP_DIR/documents_${DATE}.json', 'w') as f:
    json.dump(docs.data, f, ensure_ascii=False, indent=2, default=str)

# Export glossary
glossary = client.table('glossary').select('*').execute()
with open('$BACKUP_DIR/glossary_${DATE}.json', 'w') as f:
    json.dump(glossary.data, f, ensure_ascii=False, indent=2, default=str)

# Export conversations
convos = client.table('conversations').select('*').execute()
with open('$BACKUP_DIR/conversations_${DATE}.json', 'w') as f:
    json.dump(convos.data, f, ensure_ascii=False, indent=2, default=str)

print(f'Backup completed: {datetime.now().isoformat()}')
print(f'  documents: {len(docs.data)} rows')
print(f'  glossary: {len(glossary.data)} rows')
print(f'  conversations: {len(convos.data)} rows')
"

# Xóa backup cũ hơn 90 ngày
find "$BACKUP_DIR" -name "*.json" -mtime +90 -delete

echo "Weekly backup done: $DATE"
```

Thêm vào crontab:

```bash
crontab -e
# Chạy mỗi Chủ nhật lúc 2:00 sáng
0 2 * * 0 /home/botai/scripts/backup-weekly.sh >> /home/botai/backups/backup.log 2>&1
```

**Log sau mỗi lần ingest:**

```bash
# Ghi vào ingest-log.csv sau mỗi lần ingest
echo "$(date -Iseconds),<số_tài_liệu>,<nguồn>,<người_thực_hiện>" >> /home/botai/backups/ingest-log.csv
```

---

## 4. Checklist khôi phục toàn bộ từ zero

Dùng checklist này khi cần dựng lại toàn bộ hệ thống từ đầu.

- [ ] 1. Provision VPS mới (Ubuntu 22.04+, tối thiểu 2 vCPU, 4GB RAM)
- [ ] 2. SSH vào VPS bằng root, đổi mật khẩu root
- [ ] 3. Tạo user `botai` với quyền sudo
- [ ] 4. Cấu hình SSH key authentication cho user `botai`
- [ ] 5. Cấu hình firewall (UFW): cho phép SSH, port 8000, port 443
- [ ] 6. Cài đặt `python3`, `python3-venv`, `git`, `nginx`
- [ ] 7. Clone repository về `/home/botai/botai-backend/repo/`
- [ ] 8. Tạo Python virtual environment và cài dependencies
- [ ] 9. Tạo file `.env` với đầy đủ các biến môi trường (Supabase, OpenAI)
- [ ] 10. Kiểm tra Supabase project đang active (restore nếu bị pause)
- [ ] 11. Xác minh kết nối database từ VPS
- [ ] 12. Xác minh OpenAI API key hoạt động
- [ ] 13. Tạo và enable systemd service `botai-backend`
- [ ] 14. Start service và kiểm tra health endpoint (`/health`)
- [ ] 15. Cập nhật IP mới trong Vercel environment variables
- [ ] 16. Redeploy frontend trên Vercel
- [ ] 17. Test end-to-end: mở https://windbot.vercel.app → gửi câu hỏi → xác minh nhận được phản hồi từ LLM

---

## 5. Danh bạ liên hệ khẩn cấp

| Vai trò | Tên | Email | Số điện thoại | Ghi chú |
|---|---|---|---|---|
| Lead Developer | _[điền tên]_ | _[điền email]_ | _[điền SĐT]_ | Liên hệ đầu tiên |
| DevOps | _[điền tên]_ | _[điền email]_ | _[điền SĐT]_ | VPS, deployment |
| VPS Provider Support | — | _[điền email support]_ | _[điền hotline]_ | Ticket qua dashboard |
| Supabase Support | — | support@supabase.io | — | https://supabase.com/dashboard/support |
| OpenAI Support | — | support@openai.com | — | https://help.openai.com |

---

> **Ghi chú cuối:** Tài liệu này cần được cập nhật mỗi khi có thay đổi về hạ tầng, thêm service mới, hoặc sau mỗi sự cố lớn. Mỗi sự cố nên được ghi nhận trong một incident report riêng để cải thiện quy trình.
