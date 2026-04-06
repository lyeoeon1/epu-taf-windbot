# Hướng dẫn nạp tài liệu mới vào WindBot

## Tổng quan

WindBot sử dụng pipeline ingestion để chuyển tài liệu kỹ thuật thành vector embeddings, lưu vào Supabase pgvector. Chatbot sẽ tự động sử dụng nội dung mới trong các câu trả lời.

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

Tạo thư mục mới (đặt tên theo ngày hoặc batch, VD: `new_docs_6-4`), rồi kéo file vào.

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
[1/3] Processing: Wind-Tecnology (1).docx
  → Created 15 chunks
[2/3] Processing: 195-fowt-guide-jan24.pdf
  → Created 22 chunks
[3/3] Processing: AWEA-Operations-and-Maintenance-Re...2017.pdf
  → Created 45 chunks

Done! Total: 82 chunks ingested.
```

## 4. Sau khi ingest

### Restart backend service

```bash
exit  # thoát về root
systemctl restart botai-backend
```

### Kiểm tra service

```bash
systemctl status botai-backend
curl -s http://localhost:8000/api/health
```

## 5. Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `Error: ... is not a valid directory` | Đường dẫn sai hoặc folder chưa tồn tại | Kiểm tra `ls ./data/<tên-folder>/` |
| `Permission denied` | File thuộc root, botai không đọc được | `chown -R botai:botai <đường-dẫn>/` (chạy từ root) |
| `Command 'python' not found` | Chưa dùng venv Python | Dùng `venv/bin/python` thay vì `python` |
| `LLAMA_CLOUD_API_KEY not set` | Chưa load .env | Chạy `set -a; source .env; set +a` trước |
| `FAILED: ...` cho 1 file | File bị lỗi format | File vẫn tiếp tục xử lý các file còn lại, kiểm tra file lỗi |
| `SSL connection has been closed` | Supabase bị pause | Vào Supabase Dashboard restore project, rồi restart service |

## 6. Quy trình tóm tắt

```
1. Nhận file từ khách hàng
2. SFTP upload vào /home/botai/.../backend/data/<folder-mới>/
3. SSH root: chown -R botai:botai <đường-dẫn>/
4. SSH: su - botai → cd ~/botai-backend/repo/backend
5. Load env: set -a; source .env; set +a
6. Ingest: venv/bin/python scripts/ingest_docs.py --dir ./data/<folder>/
7. Exit về root → systemctl restart botai-backend
8. Test chatbot trên windbot.vercel.app
```
