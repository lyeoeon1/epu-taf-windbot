# BotAI Deployment Log

Ghi chép quá trình triển khai thực tế trên VPS.

---

## Lần 1 — Ngày: 23/03/2026

### Mục tiêu
Chuyển BotAI backend từ chạy dưới root (single uvicorn + pm2) sang user `botai` riêng + systemd + gunicorn.

### Trạng thái trước khi triển khai
- BotAI chạy dưới **root**, single uvicorn, port 8000, quản lý bởi **pm2**
- Repo tại `/root/botai/`, venv tại `/root/botai/venv/`
- Không có systemd service
- SOOP đã chạy ổn định trên port 8001 (user `soop`, systemd, gunicorn)

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. Commit & push code | `git push -u origin lyeoeon1/vps-multi-app-setup` | ✅ | PR #26 |
| 2. Merge PR | Merge trên GitHub | ✅ | |
| 3. SSH vào VPS | `ssh root@62.146.236.156` | ✅ | |
| 4. Tạo user botai | `useradd -m -s /bin/bash botai` | ✅ | uid=1001 |
| 5. Clone repo | `su - botai` rồi `git clone https://<TOKEN>@github.com/...` | ✅ | Cần GitHub token vì repo private |
| 6. Tạo venv | `python3 -m venv .../backend/venv` | ✅ | |
| 7. Cài dependencies | `pip install -r requirements.txt` | ✅ | |
| 8. Cài gunicorn | `pip install gunicorn` | ✅ | Thiếu trong requirements.txt, cài thêm |
| 9. Copy .env | `cp /root/botai/backend/.env ...` (chạy ở root) | ✅ | User botai không có quyền đọc /root/ |
| 10. Cài systemd service | `cp .../botai-backend.service /etc/systemd/system/` | ✅ | `Created symlink ...` |
| 11. Dừng pm2 backend cũ | `pm2 stop backend && pm2 delete backend && pm2 save` | ✅ | Uvicorn root cũ quản lý bởi pm2, không phải systemd |
| 12. Start service mới | `systemctl restart botai-backend` | ✅ | |
| 13. Verify | `lsof -i :8000`, `systemctl status botai-backend` | ✅ | 4 workers, user botai, active (running) |

### Kết quả
- ✅ **Thành công**
- Service `botai-backend` chạy ổn định dưới user `botai`
- Gunicorn 1 master + 4 workers trên `0.0.0.0:8000`
- Frontend windbot.vercel.app kết nối backend qua `http://62.146.236.156:8000` — hoạt động OK
- Warning `Could not create vector index: replace is set to False` — không ảnh hưởng (index đã tồn tại)

### Vấn đề gặp phải
1. **Repo private** → không clone được bằng `sudo -u botai git clone`. Giải pháp: `su - botai` rồi clone với GitHub token
2. **Gunicorn chưa cài** → service lỗi `status=203/EXEC`. Giải pháp: cài thêm `pip install gunicorn`
3. **Uvicorn root cũ tự restart** → pm2 đang quản lý, kill process không đủ. Giải pháp: `pm2 stop/delete backend`
4. **Copy .env cần quyền root** → user botai không đọc được `/root/`. Giải pháp: chạy `cp` từ root
5. **Gunicorn bind 127.0.0.1** → frontend Vercel không kết nối được (NEXT_PUBLIC_API_URL trỏ trực tiếp vào IP VPS). Giải pháp: đổi bind sang `0.0.0.0:8000`

### Bài học rút ra
1. Thêm `gunicorn` vào `requirements.txt` để không phải cài tay
2. Kiểm tra pm2/supervisor/systemd trước khi kill process — process có thể tự restart
3. Phân biệt rõ lệnh nào chạy ở root, lệnh nào ở user botai
4. Repo private cần setup GitHub token hoặc SSH key cho user mới
5. Kiểm tra cách frontend kết nối backend (IP trực tiếp vs ngrok vs tunnel) trước khi quyết định bind address

---

## Lần 2 — Ngày: 23/03/2026

### Mục tiêu
Nạp knowledge base, glossary, benchmark cho mục 2, 5, 8 (Q&A corpus, kho kiến thức tua-bin gió, dataset card).

### Trạng thái trước khi triển khai
- Backend đã chạy ổn định (Lần 1)
- Chưa có knowledge base chuyên ngành trong vector store
- Chưa có bảng glossary trong Supabase
- Chưa có benchmark đánh giá chất lượng

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. Commit & push code | `git push -u origin lyeoeon1/warsaw-v3` | ✅ | PR #29, +4206 lines, 30 files |
| 2. Merge PR | Merge trên GitHub | ✅ | |
| 3. VPS: git pull | `su - botai` → `cd ~/botai-backend/repo && git pull` | ✅ | |
| 4. Restart backend | `systemctl restart botai-backend` (root) | ✅ | active (running) |
| 5. Tạo bảng glossary | Supabase MCP `apply_migration` | ✅ | Bảng + 2 indexes |
| 6. Seed glossary data | Supabase MCP `execute_sql` (3 batches) | ✅ | 87 thuật ngữ song ngữ |
| 7. Cài llama-index-readers-file | `pip install llama-index-readers-file` (botai) | ✅ | Dependency conflict → fix bằng downgrade |
| 8. Nạp knowledge base processes | `python scripts/ingest_docs.py --dir data/knowledge_base/processes/` | ✅ | 11 chunks (3 files) |
| 9. Nạp knowledge base technical | `python scripts/ingest_docs.py --dir data/knowledge_base/technical/` | ✅ | 14 chunks (3 files) |
| 10. Restart backend | `systemctl restart botai-backend` (root) | ✅ | active (running), health OK |

### Kết quả
- ✅ **Thành công**
- **87 thuật ngữ** glossary trong Supabase (7 categories: structure 15, components 15, maintenance 15, operations 12, troubleshooting 12, general 9, safety 9)
- **25 chunks** knowledge base nạp vào vector store (6 files: 3 processes + 3 technical)
- **150 Q&A benchmark** sẵn sàng chạy đánh giá (benchmark-windbot-v1.md)
- **Dataset card** theo chuẩn Hugging Face (dataset_card.md)
- Frontend windbot.vercel.app hoạt động OK sau restart

### Dữ liệu đã nạp

| Loại | Files | Chunks/Entries | Vị trí |
|------|-------|----------------|--------|
| Knowledge base - Processes | 3 (.md) | 11 chunks | Supabase pgvector |
| Knowledge base - Technical | 3 (.md) | 14 chunks | Supabase pgvector |
| Glossary | 1 (.json) | 87 entries | Supabase table `glossary` |
| Benchmark Q&A | 1 (.md) | 150 pairs | File local (chưa nạp vector) |
| Dataset Card | 1 (.md) | — | File local |

### Vấn đề gặp phải
1. **`llama-index-readers-file` chưa cài** → script ingest báo lỗi. Giải pháp: `pip install llama-index-readers-file`
2. **Dependency conflict** → `llama-index-core` bị nâng từ 0.12 → 0.14, không tương thích với embeddings/llms/vector-stores packages. Giải pháp: downgrade về `<0.13.0`
3. **OpenAI API key 401** → script `ingest_docs.py` không tự load `.env`. Giải pháp: `set -a; source .env; set +a` trước khi chạy
4. **Glossary INSERT quá dài** → Supabase MCP không chấp nhận SQL 35KB. Giải pháp: chia thành 3 batches (30 rows mỗi batch) + insert bổ sung phần bị thiếu

### Bài học rút ra
1. Thêm `llama-index-readers-file` vào `requirements.txt`
2. Pin version chặt cho `llama-index-*` packages để tránh conflict
3. Script ingest nên tự load `.env` (dùng `python-dotenv`)
4. Supabase MCP có giới hạn kích thước SQL — chia batch khi INSERT nhiều rows
5. Kiểm tra `SELECT COUNT(*)` sau mỗi batch INSERT để đảm bảo đủ dữ liệu

---

## Trạng thái hiện tại

| App | User | Port | Process Manager | Service Name |
|-----|------|------|-----------------|--------------|
| BotAI | `botai` | 8000 | systemd | `botai-backend.service` |
| SOOP | `soop` | 8001 | systemd | `soop-backend.service` |

### Lệnh quản lý nhanh

```bash
# BotAI
sudo systemctl status botai-backend
sudo systemctl restart botai-backend
sudo journalctl -u botai-backend -f

# SOOP
sudo systemctl status soop-backend
sudo systemctl restart soop-backend
sudo journalctl -u soop-backend -f
```

---

## Lần 3 — Ngày: 23/03/2026

### Mục tiêu
Cải thiện chất lượng chatbot dựa trên phản hồi khách hàng: (1) tăng consistency, (2) fix memory/correction retention, (3) giảm lỗi factual.

### Nguyên nhân gốc (Root Cause Analysis)

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| Không nhất quán | temperature=0.3 gây variance; similarity_top_k=5 có thể trả chunks khác nhau | temperature→0.1, top_k→10, thêm SimilarityPostprocessor cutoff=0.5 |
| Không nhớ sửa đổi | ChatMemoryBuffer=4000 tokens quá nhỏ; default condense prompt không giữ corrections | memory→8000, history limit→40, custom condense prompt enforce giữ corrections |
| Sai factual | System prompt yếu về grounding; chưa nạp Q&A corpus | Thêm quy tắc "NEVER fabricate", nạp benchmark Q&A vào vector store |

### Code thay đổi

| File | Thay đổi |
|------|----------|
| `backend/app/services/rag.py` | temperature 0.3→0.1, token_limit 4000→8000, similarity_top_k 5→10, thêm SimilarityPostprocessor, thêm custom condense prompt |
| `backend/app/prompts/system.py` | Thêm grounding rules (EN+VI), correction-awareness (EN+VI), condense prompts (EN+VI) |
| `backend/app/services/chat_history.py` | History fetch limit 20→40 |
| `backend/scripts/ingest_qa.py` | Hỗ trợ thêm format Q&A từ generate_qa_corpus.py |

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. Commit & push code | | ⬜ | |
| 2. Merge PR | | ⬜ | |
| 3. VPS: git pull + restart | | ⬜ | |
| 4. Chạy baseline benchmark | `evaluate_rag.py` trước changes | ⬜ | |
| 5. Nạp benchmark Q&A | `ingest_qa.py` | ⬜ | |
| 6. Generate + nạp Q&A corpus | `generate_qa_corpus.py` + `ingest_qa.py` | ⬜ | |
| 7. Chạy post-change benchmark | `evaluate_rag.py` sau changes | ⬜ | |
| 8. So sánh baseline vs after | | ⬜ | Target: ≥3.5/5 |

### Kết quả
- ⬜ Chờ thực hiện

---

<!--
## Template cho lần deploy tiếp theo

## Lần N — Ngày: ___/___/2026

### Mục tiêu
_Mô tả thay đổi_

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. | | ⬜ | |

### Kết quả
- ⬜ Thành công / ❌ Thất bại

### Vấn đề gặp phải

### Bài học rút ra
-->
