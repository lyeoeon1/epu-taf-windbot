# Hướng dẫn nạp tài liệu mới vào WindBot

## Tổng quan

WindBot sử dụng pipeline ingestion để chuyển tài liệu kỹ thuật thành vector embeddings, lưu vào Supabase pgvector. Chatbot sẽ tự động sử dụng nội dung mới trong các câu trả lời.

**Dữ liệu được lưu ở 2 nơi:**
- **Vector store** (`vecs.wind_turbine_docs`): Chunks + embeddings cho RAG retrieval
- **Bảng metadata** (`documents_metadata`): Tracking thông tin file (tên, loại, số chunks, ngày nạp)

> **Lưu ý:** Script `ingest_docs.py` chỉ ghi vào vector store. Cần insert metadata thủ công vào bảng `documents_metadata` sau khi ingest (xem bước 5).

## 1. Định dạng hỗ trợ

| Định dạng | Parser | Ghi chú |
|-----------|--------|---------|
| `.pdf` | LlamaParse (OCR) | Hỗ trợ scan, bảng, hình ảnh |
| `.docx` | LlamaParse | Word 2007+ |
| `.doc` | LlamaParse | Word cũ |
| `.pptx` | LlamaParse | PowerPoint |
| `.xlsx` | LlamaParse | Excel |
| `.txt` | SimpleDirectoryReader | Text thuần |
| `.md` | SimpleDirectoryReader | Markdown |
| `.csv` | SimpleDirectoryReader | Bảng CSV |

**Lưu ý:**
- File PDF scan (hình ảnh) vẫn được xử lý nhờ OCR (hỗ trợ cả Tiếng Anh và Tiếng Việt)
- File lớn (>20MB) có thể mất vài phút để xử lý
- Tên file không nên chứa ký tự đặc biệt ngoài `-`, `_`, `.`

## 2. Upload file lên VPS

### Bước 1: Kết nối SFTP

Dùng Termius (hoặc FileZilla, WinSCP) kết nối SFTP tới VPS:
- **Host:** 62.146.236.156
- **User:** root
- **Port:** 22

### Bước 2: Tạo thư mục và upload

Navigate tới: `/home/botai/botai-backend/repo/backend/data/`

Tạo thư mục mới (đặt tên theo ngày, VD: `new_docs_6-4`), rồi kéo file vào.

### Bước 3: Fix quyền sở hữu

Vì upload bằng root nhưng script chạy dưới user `botai`, cần chuyển quyền. Chạy từ **root** (SSH):

```bash
chown -R botai:botai /home/botai/botai-backend/repo/backend/data/<tên-folder>/
```

Ví dụ:
```bash
chown -R botai:botai /home/botai/botai-backend/repo/backend/data/new_docs_6-4/
```

## 3. Chạy ingest

### Chuyển sang user botai và load env

```bash
su - botai
cd ~/botai-backend/repo/backend
set -a; source .env; set +a
```

### Chạy script

```bash
venv/bin/python scripts/ingest_docs.py --dir ./data/<tên-folder>/
```

### Tùy chọn nâng cao

| Option | Giá trị | Mặc định | Mô tả |
|--------|---------|----------|-------|
| `--dir` | đường dẫn | (bắt buộc) | Thư mục chứa tài liệu |
| `--language` | `en` hoặc `vi` | `en` | Ngôn ngữ tài liệu |
| `--tier` | `cost_effective`, `agentic`, `agentic_plus` | `agentic` | Chất lượng parsing (cao hơn = tốn hơn) |

Ví dụ nạp tài liệu Tiếng Việt với tier cao nhất:
```bash
venv/bin/python scripts/ingest_docs.py --dir ./data/new_docs_6-4/ --language vi --tier agentic_plus
```

### Kết quả mong đợi

```
Found 3 files in ./data/new_docs_6-4/
Ingesting 195-fowt-guide-jan24.pdf... OK (196 chunks)
Ingesting Wind-Tecnology (1).docx... OK (50 chunks)
Ingesting AWEA-Operations-and-Maintenance-...2017.pdf... OK (476 chunks)
Done! Total chunks created: 722
```

> Warning `Could not create vector index: replace is set to False` là bình thường — index đã tồn tại, nhưng cần rebuild (xem bước 5).

## 4. Rebuild vector index (BẮT BUỘC)

Sau khi ingest, vector index cũ **không tự động cập nhật** để bao gồm chunks mới. Nếu không rebuild, retriever sẽ **không tìm thấy** nội dung vừa nạp.

Vào **Supabase Dashboard → SQL Editor** và chạy:

```sql
-- Drop index cũ và tạo lại để include toàn bộ vectors
DROP INDEX IF EXISTS vecs.ix_vector_cosine_ops_hnsw_m16_efc64_b494534;
CREATE INDEX ix_vector_cosine_ops_hnsw_m16_efc64_b494534
ON vecs.wind_turbine_docs
USING hnsw (vec vector_cosine_ops)
WITH (m=16, ef_construction=64);
```

> **Lưu ý:** Nếu tên index khác, kiểm tra bằng:
> ```sql
> SELECT indexname FROM pg_indexes
> WHERE tablename = 'wind_turbine_docs' AND schemaname = 'vecs';
> ```

## 5. Restart backend service

Thoát về root rồi restart:

```bash
exit
systemctl restart botai-backend
```

Kiểm tra:

```bash
systemctl status botai-backend
curl -s http://localhost:8000/api/health
```

## 6. Cập nhật metadata trên Supabase

Script ingest chỉ ghi chunks vào vector store, **không tự cập nhật bảng `documents_metadata`**. Cần insert thủ công qua Supabase Dashboard (SQL Editor) hoặc MCP:

```sql
INSERT INTO documents_metadata (filename, file_type, language, num_chunks, ingested_at) VALUES
('195-fowt-guide-jan24.pdf', 'pdf', 'en', 196, NOW()),
('Wind-Tecnology (1).docx', 'docx', 'en', 50, NOW()),
('AWEA-Operations-and-Maintenance-...2017.pdf', 'pdf', 'en', 476, NOW());
```

**Lưu ý:** Thay tên file, file_type, language, và num_chunks theo kết quả ingest thực tế.

## 7. Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `Error: ... is not a valid directory` | Đường dẫn sai hoặc folder chưa tồn tại | Kiểm tra `ls ./data/<tên-folder>/` |
| `Permission denied` | File thuộc root, botai không đọc được | `chown -R botai:botai <đường-dẫn>/` (chạy từ root) |
| `Command 'python' not found` | Chưa dùng venv Python | Dùng `venv/bin/python` thay vì `python` |
| `LLAMA_CLOUD_API_KEY not set` | Chưa load .env | Chạy `set -a; source .env; set +a` trước |
| `FAILED: ...` cho 1 file | File bị lỗi format | Script tiếp tục xử lý các file còn lại, kiểm tra file lỗi |
| `SSL connection has been closed` | Supabase bị pause | Vào Supabase Dashboard restore project, rồi restart service |
| `botai is not in the sudoers file` | Đang dùng user botai chạy sudo | Thoát về root (`exit`) rồi chạy lệnh cần sudo |

## 8. Kiểm tra dữ liệu đã nạp

### Kiểm tra tổng số vectors

```sql
SELECT COUNT(*) as total_vectors FROM vecs."wind_turbine_docs";
```

### Kiểm tra chunks theo file

```sql
SELECT metadata->>'filename' as filename, COUNT(*) as chunks
FROM vecs."wind_turbine_docs"
GROUP BY metadata->>'filename'
ORDER BY chunks DESC;
```

### Kiểm tra metadata

```sql
SELECT filename, file_type, num_chunks, ingested_at
FROM documents_metadata
ORDER BY ingested_at DESC;
```

## 9. Quy trình tóm tắt

```
1.  Nhận file từ khách hàng
2.  SFTP (root) upload vào /home/botai/.../backend/data/<folder-mới>/
3.  SSH root: chown -R botai:botai <đường-dẫn>/
4.  SSH: su - botai → cd ~/botai-backend/repo/backend
5.  Load env: set -a; source .env; set +a
6.  Ingest: venv/bin/python scripts/ingest_docs.py --dir ./data/<folder>/
7.  Ghi nhận số chunks mỗi file từ output
8.  Rebuild vector index trên Supabase SQL Editor (DROP + CREATE INDEX)
9.  Exit về root → systemctl restart botai-backend
10. Insert metadata vào Supabase (SQL Editor hoặc MCP)
11. Test chatbot trên windbot.vercel.app
```

## Lịch sử nạp tài liệu

| Ngày | Files | Chunks | Ghi chú |
|------|-------|--------|---------|
| 11/02/2026 | Dien Gio 1-6.pdf | 50 | Batch đầu tiên |
| 11/02/2026 | Dien Gio 2-6.pdf, 3-6, 4-6, 5-6 | 164 | 4 file |
| 24/03/2026 | Wind_Energy_Handbook.pdf | 743 | Sách tham khảo lớn |
| 24/03/2026 | R06-004 Wind Energy Design.pdf | 102 | |
| 24/03/2026 | windenergyengineering...turbines.pdf | 748 | |
| 06/04/2026 | 195-fowt-guide-jan24.pdf | 196 | Batch từ EPU/TAF |
| 06/04/2026 | Wind-Tecnology (1).docx | 50 | Batch từ EPU/TAF |
| 06/04/2026 | AWEA-Operations-and-Maintenance...2017.pdf | 476 | Batch từ EPU/TAF |
