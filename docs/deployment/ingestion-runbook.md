# Runbook — Vận hành pipeline nạp tài liệu

> Runbook này là checklist thực thi mỗi khi cần nạp tài liệu mới vào knowledge base.
> Dùng cùng với `ingestion-guide.md` (hướng dẫn chi tiết) và `test_ingestion.py` (script test).
>
> Cập nhật lần cuối: Tháng 4/2026

---

## Mục lục

1. [Pre-ingest checklist](#1-pre-ingest-checklist)
2. [Quy trình ingest](#2-quy-trình-ingest)
3. [Post-ingest verification](#3-post-ingest-verification)
4. [Error recovery](#4-error-recovery)
5. [Escalation](#5-escalation)

---

## 1. Pre-ingest checklist

Hoàn thành các check sau **TRƯỚC KHI** bắt đầu ingest.

### 1.1. Hạ tầng

- [ ] **Disk space** trên VPS ≥ 5GB
  ```bash
  df -h /
  # Ensure "Avail" column >= 5G
  ```

- [ ] **Memory** available ≥ 1GB
  ```bash
  free -h
  # "available" column >= 1G
  ```

- [ ] **Backend service** đang chạy
  ```bash
  systemctl status botai-backend
  # Expected: active (running)
  ```

### 1.2. Dịch vụ bên ngoài

- [ ] **Supabase project** không bị pause
  - Vào https://supabase.com/dashboard → project WINDBOT
  - Status phải là **Active** (không phải Paused)

- [ ] **API keys** còn hợp lệ
  - OpenAI: https://platform.openai.com/usage (không vượt budget)
  - LlamaCloud: https://cloud.llamaindex.ai/ (nếu nạp PDF/DOCX)

### 1.3. Validation script

- [ ] Chạy dry-run để verify setup:
  ```bash
  ssh root@[VPS-IP]
  su - botai
  cd ~/botai/repo/backend
  source venv/bin/activate
  set -a; source .env; set +a
  python scripts/test_ingestion.py --dry-run
  ```
  - Expected: `SUMMARY: 8/8 checks passed`
  - Nếu FAIL → xem [mục 4. Error recovery](#4-error-recovery) hoặc `ingestion-guide.md`

### 1.4. Tài liệu cần ingest

- [ ] File đã được review về nội dung (không có thông tin nhạy cảm, bản quyền)
- [ ] Tên file tuân thủ convention (chỉ a-z, A-Z, 0-9, `-`, `_`, `.`)
- [ ] Kích thước mỗi file < 50MB (file lớn hơn cần chia nhỏ)
- [ ] Ngôn ngữ tài liệu xác định rõ (`en` hoặc `vi`)

---

## 2. Quy trình ingest

Làm theo thứ tự, không được bỏ bước.

### Bước 1: Upload file lên VPS (qua SFTP)

- Host: `[VPS-IP]`, User: `root`, Port: 22
- Directory: `/home/botai/botai/repo/backend/data/`
- Tạo subfolder mới (VD: `new_docs_2026-04-16`)
- Upload files vào subfolder

### Bước 2: Fix quyền sở hữu

**Chạy từ user root:**
```bash
chown -R botai:botai /home/botai/botai/repo/backend/data/new_docs_2026-04-16/
```

### Bước 3: Chạy ingest script

**Chuyển sang user botai:**
```bash
su - botai
cd ~/botai/repo/backend
source venv/bin/activate
set -a; source .env; set +a

# Ingest
python scripts/ingest_docs.py --dir ./data/new_docs_2026-04-16/ --language vi --tier agentic
```

**Options:**
- `--language`: `en` hoặc `vi` (bắt buộc match với nội dung)
- `--tier`: `cost_effective` (rẻ, cơ bản) / `agentic` (mặc định, cân bằng) / `agentic_plus` (cao cấp, đắt)

**📝 Ghi nhận:** Lưu output của script (số chunks mỗi file) để insert metadata ở Bước 5.

### Bước 4: Rebuild vector index

**Vào Supabase Dashboard → SQL Editor**, chạy:

```sql
DROP INDEX IF EXISTS vecs.ix_vector_cosine_ops_hnsw_m16_efc64_b494534;
CREATE INDEX ix_vector_cosine_ops_hnsw_m16_efc64_b494534
ON vecs.wind_turbine_docs
USING hnsw (vec vector_cosine_ops)
WITH (m=16, ef_construction=64);
```

> Lưu ý: Tên index có thể khác tùy môi trường. Kiểm tra bằng:
> ```sql
> SELECT indexname FROM pg_indexes
> WHERE tablename = 'wind_turbine_docs' AND schemaname = 'vecs';
> ```

### Bước 5: Insert metadata

**Trong Supabase SQL Editor:**

```sql
INSERT INTO documents_metadata (filename, file_type, language, num_chunks, ingested_at) VALUES
  ('wind_handbook.pdf', 'pdf', 'vi', 196, NOW()),
  ('maintenance.docx', 'docx', 'vi', 50, NOW());
  -- Thay tên file, file_type, num_chunks theo kết quả Bước 3
```

### Bước 6: Restart backend

**Thoát về root, restart:**
```bash
exit
systemctl restart botai-backend
```

---

## 3. Post-ingest verification

Sau khi ingest xong, **bắt buộc** verify các bước sau.

### 3.1. Backend healthy

```bash
curl -s http://127.0.0.1:8001/api/health
# Expected: {"status":"ok","version":"0.1.0"}

systemctl status botai-backend
# Expected: active (running)
```

### 3.2. Chunks đã vào vector store

Vào Supabase SQL Editor:

```sql
-- Tổng số vectors (phải tăng lên)
SELECT COUNT(*) FROM vecs."wind_turbine_docs";

-- Vectors theo file (phải thấy file mới)
SELECT metadata->>'filename' as filename, COUNT(*) as chunks
FROM vecs."wind_turbine_docs"
GROUP BY metadata->>'filename'
ORDER BY chunks DESC;

-- Metadata mới nhất
SELECT filename, num_chunks, ingested_at
FROM documents_metadata
ORDER BY ingested_at DESC
LIMIT 10;
```

### 3.3. Test chatbot

Truy cập https://windbot.vercel.app, hỏi câu hỏi liên quan đến nội dung tài liệu vừa nạp.
- Chatbot phải trả lời được dựa trên nội dung mới
- Nguồn (citations) phải reference đến filename vừa nạp

### 3.4. Ghi nhận vào lịch sử

Cập nhật `docs/deployment/ingestion-guide.md`, mục "Lịch sử nạp tài liệu" với:
- Ngày nạp
- Tên file
- Số chunks
- Ghi chú (batch nào, nguồn từ đâu)

---

## 4. Error recovery

Bảng xử lý lỗi theo triệu chứng:

| Triệu chứng | Bước | Giải pháp |
|---|---|---|
| `Error: ... is not a valid directory` | Bước 3 | Kiểm tra `ls ./data/[folder]/` — đường dẫn có đúng không |
| `Permission denied` khi ingest | Bước 3 | Thoát về root, chạy `chown -R botai:botai [path]/` |
| `Command 'python' not found` | Bước 3 | Dùng `source venv/bin/activate` hoặc `venv/bin/python` trực tiếp |
| `LLAMA_CLOUD_API_KEY not set` | Bước 3 | Chạy `set -a; source .env; set +a` trước ingest |
| `FAILED: ...` cho 1 file | Bước 3 | Script tự động bỏ qua file lỗi, tiếp tục file khác. Kiểm tra file lỗi (corrupt? format không hỗ trợ?) |
| `SSL connection has been closed` | Bước 3 | Supabase bị pause → vào dashboard → Restore → restart backend → retry |
| `botai is not in the sudoers file` | Bước 6 | Thoát về root (`exit`) rồi chạy `systemctl restart` |
| Chatbot không trả lời được với tài liệu mới | Bước 4 | Chưa rebuild vector index — chạy lại Bước 4 |
| Backend crash sau restart | Bước 6 | `journalctl -u botai-backend --since "5 min ago"` xem log lỗi |

### 4.1. Rollback khi ingest sai tài liệu

Nếu nạp nhầm tài liệu:

```sql
-- Tìm chunks của file cần xóa
SELECT id FROM vecs."wind_turbine_docs"
WHERE metadata->>'filename' = 'wrong_file.pdf';

-- Xóa chunks (backup trước nếu cần)
DELETE FROM vecs."wind_turbine_docs"
WHERE metadata->>'filename' = 'wrong_file.pdf';

-- Xóa metadata record
DELETE FROM documents_metadata WHERE filename = 'wrong_file.pdf';

-- Rebuild index (Bước 4)
-- Restart backend (Bước 6)
```

### 4.2. Khôi phục sau sự cố ingest

Nếu ingest bị crash giữa chừng:
1. Kiểm tra số chunks đã tạo: `SELECT COUNT(*) FROM vecs."wind_turbine_docs" WHERE metadata->>'filename' = '[file]';`
2. Nếu < số chunks kỳ vọng → xóa partial chunks (SQL như 4.1) → retry ingest
3. Nếu = số chunks kỳ vọng → ingest đã xong, chỉ cần rebuild index + metadata

---

## 5. Escalation

### Khi nào liên hệ hỗ trợ (trong thời gian SLA)

Liên hệ kênh hỗ trợ trong các trường hợp sau:

- **Critical** (response ≤4h):
  - Backend không start được sau khi ingest
  - Supabase báo lỗi không xác định, không có trong bảng ở mục 4
  - Toàn bộ chatbot ngừng hoạt động sau ingest

- **Normal** (response ≤2 ngày làm việc):
  - Ingest thành công nhưng chatbot không tìm thấy nội dung mới
  - Có file ingest bị FAIL, không biết nguyên nhân
  - Performance giảm sau khi ingest batch lớn

- **Minor** (response ≤5 ngày làm việc):
  - Muốn tư vấn cách tối ưu ingest pipeline
  - Muốn đổi model embedding/chunking strategy
  - Câu hỏi chung về quy trình

### Thông tin cần cung cấp khi báo lỗi

```
- Ngày giờ ingest
- Lệnh đã chạy (copy full command)
- Output script (copy full output, bao gồm error message)
- Backend logs: journalctl -u botai-backend --since "1 hour ago"
- File bị lỗi (nếu có): tên, kích thước, format
- Bước nào trong runbook bị FAIL
```

Xem thêm: `docs/handover/sla.md`, `docs/guides/disaster-recovery.md`

---

## Tài liệu liên quan

| Tài liệu | Mục đích |
|---|---|
| `docs/deployment/ingestion-guide.md` | Hướng dẫn chi tiết + lịch sử ingest |
| `docs/evaluation/ingestion-test-report.md` | Báo cáo kiểm thử (bằng chứng KPI) |
| `backend/scripts/test_ingestion.py` | Script test tự động |
| `backend/scripts/ingest_docs.py` | Script ingest chính |
| `docs/guides/disaster-recovery.md` | Phục hồi sự cố hệ thống |
| `docs/handover/sla.md` | Thỏa thuận hỗ trợ |
