# DRY-RUN BÀN GIAO — KỊCH BẢN CHẠY THỬ

**Mục đích:** Chạy thử toàn bộ quy trình bàn giao trước ngày H để phát hiện lỗi, thiếu sót, và luyện tập.
**Thời gian:** ~1-2 giờ
**Ai chạy:** Nhóm phát triển (tự đóng vai cả 2 bên)

---

## Phần A: Test hệ thống production (30 phút)

### A1. Frontend
- [ ] Truy cập https://windbot.vercel.app — trang load bình thường
- [ ] Hỏi tiếng Việt: "Tua-bin gió gồm những bộ phận gì?" — nhận response streaming
- [ ] Hỏi tiếng Anh: "What is a wind turbine nacelle?" — response bằng tiếng Anh
- [ ] Hỏi follow-up: "Chi tiết hơn" — chatbot hiểu context
- [ ] Kiểm tra follow-up suggestions hiển thị (3 gợi ý)
- [ ] Kiểm tra dark/light mode hoạt động
- [ ] Test trên mobile (responsive)

### A2. Backend API
- [ ] Health check: `curl -s http://[VPS-IP]:8001/api/health` → response OK
- [ ] API docs: mở `http://[VPS-IP]:8001/docs` trong trình duyệt → Swagger UI hiển thị
- [ ] Glossary: `curl -s http://[VPS-IP]:8001/api/glossary | head -20` → danh sách thuật ngữ

### A3. Database (Supabase)
- [ ] Login Supabase Dashboard → project WINDBOT hiển thị, không bị pause
- [ ] Table Editor → `chat_sessions` có dữ liệu
- [ ] Table Editor → `glossary` có 87 thuật ngữ
- [ ] SQL Editor → chạy: `SELECT COUNT(*) FROM vecs."wind_turbine_docs";` → có vectors

### A4. VPS
- [ ] SSH: `ssh root@[VPS-IP]` → kết nối thành công
- [ ] Service: `systemctl status botai-backend` → active (running)
- [ ] Disk: `df -h` → >20% free space
- [ ] Memory: `free -h` → có RAM trống

### A5. Credentials (kiểm tra tất cả vẫn valid)
- [ ] OpenAI: vào https://platform.openai.com/api-keys → key active
- [ ] Supabase: dashboard accessible, project not paused
- [ ] LlamaCloud: vào https://cloud.llamaindex.ai/ → key active
- [ ] Vercel: vào https://vercel.com/dashboard → project visible

---

## Phần B: Test quy trình nạp tài liệu (20 phút)

Đây là phần quan trọng nhất — demo này sẽ diễn ra trong buổi bàn giao.

- [ ] Chuẩn bị 1 file PDF mẫu nhỏ (1-2 trang)
- [ ] SFTP upload lên VPS: `/home/botai/botai-backend/repo/backend/data/test_dryrun/`
- [ ] Fix quyền: `chown -R botai:botai /home/botai/botai-backend/repo/backend/data/test_dryrun/`
- [ ] Chạy ingest:
  ```bash
  su - botai
  cd ~/botai-backend/repo/backend
  set -a; source .env; set +a
  venv/bin/python scripts/ingest_docs.py --dir ./data/test_dryrun/ --language vi
  ```
- [ ] Ghi nhận số chunks output
- [ ] Rebuild vector index (Supabase SQL Editor)
- [ ] Restart backend: `systemctl restart botai-backend`
- [ ] Test chatbot: hỏi câu liên quan đến nội dung vừa nạp → chatbot trả lời được
- [ ] **Cleanup:** Xóa test data nếu không muốn giữ (optional)

---

## Phần C: Test export data (10 phút)

- [ ] Chạy export:
  ```bash
  su - botai
  cd ~/botai-backend/repo/backend
  set -a; source .env; set +a
  venv/bin/python scripts/export_data.py --output-dir ./export_dryrun/
  ```
- [ ] Kiểm tra output: `ls export_dryrun/export_*/`
- [ ] Mở `export_summary.txt` → có đủ 6 bảng, row counts hợp lý
- [ ] **Cleanup:** `rm -rf export_dryrun/`

---

## Phần D: Dry-run kịch bản buổi bàn giao (30 phút)

Đóng vai cả bên giao và bên nhận, chạy qua kịch bản.

### D1. Setup (mô phỏng 30 phút trước)
- [ ] Mở tất cả tabs cần thiết (windbot, Supabase, OpenAI, SSH)
- [ ] Chuẩn bị USB (hoặc giả lập: zip repo → copy vào USB)
- [ ] Đặt tài liệu in lên bàn (hoặc giả lập: mở file trên màn hình)

### D2. Tổng quan (mô phỏng 5 phút)
- [ ] Nói thử lời giới thiệu: "Xin chào, hôm nay chúng tôi sẽ bàn giao..."
- [ ] Demo chatbot: hỏi 2 câu (Việt + Anh)
- [ ] Giải thích kiến trúc (mở README → phần kiến trúc)

### D3. Quản trị (mô phỏng 10 phút)
- [ ] Demo thêm tài liệu (đã test ở Phần B)
- [ ] Demo xem chat history trên Supabase
- [ ] Demo xem glossary qua API

### D4. Sự cố (mô phỏng 5 phút)
- [ ] Demo restart backend: `systemctl restart botai-backend`
- [ ] Demo xem logs: `journalctl -u botai-backend --since "10 min ago" --no-pager`

### D5. Bàn giao credentials (mô phỏng 5 phút)
- [ ] Đọc qua danh sách credentials cần bàn giao
- [ ] Kiểm tra đã chuẩn bị đủ: VPS, OpenAI, Supabase, LlamaCloud, Vercel, GitHub
- [ ] Giả lập trao USB

### D6. Ký biên bản (mô phỏng 5 phút)
- [ ] Mở file handover-report.md — đọc qua
- [ ] Kiểm tra tất cả thông tin đã điền (không còn placeholder quan trọng)
- [ ] Mở file sla.md — đọc qua
- [ ] Giả lập ký (kiểm tra có đủ chỗ ký)

---

## Phần E: Kiểm tra tài liệu (15 phút)

### E1. Tài liệu hoàn chỉnh
- [ ] `docs/handover/handover-report.md` — không còn placeholder bắt buộc
- [ ] `docs/handover/sla.md` — email + GitHub URL đã điền
- [ ] `docs/handover/handover-checklist.md` — đủ hạng mục
- [ ] `docs/handover/training-outline.md` — thời gian hợp lý
- [ ] `docs/handover/handover-plan.md` — kế hoạch cập nhật
- [ ] `docs/handover/client-preparation.md` — sẵn sàng gửi client
- [ ] `README.md` — email liên hệ đã điền

### E2. Tài liệu kỹ thuật
- [ ] `docs/guides/admin-guide.md` — links hoạt động
- [ ] `docs/guides/admin-guide-advanced.md` — commands chính xác
- [ ] `docs/guides/disaster-recovery.md` — kịch bản đủ
- [ ] `docs/guides/migration-guide.md` — code examples đúng
- [ ] `backend/.env.example` — đủ biến, đúng format
- [ ] `backend/openapi.yaml` — validate với `openapi-spec-validator backend/openapi.yaml` → no errors
- [ ] `docs/api/api-guide.md` — examples curl/Python/JS đúng
- [ ] `docs/deployment/ingestion-runbook.md` — checklist đầy đủ
- [ ] `docs/evaluation/ingestion-test-report.md` — số liệu khớp với Supabase
- [ ] `backend/scripts/test_ingestion.py --dry-run` → all checks PASS

### E3. Repo GitHub
- [ ] Repo `epu-taf-windbot` trên GitHub — accessible
- [ ] Branch `main` — up to date với local
- [ ] Không có secrets committed (grep `.env` trong committed files)

---

## Kết quả Dry-Run

| Phần | Kết quả | Ghi chú |
|------|---------|---------|
| A. Hệ thống production | ☐ PASS / ☐ FAIL | |
| B. Nạp tài liệu | ☐ PASS / ☐ FAIL | |
| C. Export data | ☐ PASS / ☐ FAIL | |
| D. Kịch bản bàn giao | ☐ PASS / ☐ FAIL | |
| E. Tài liệu | ☐ PASS / ☐ FAIL | |

**Tổng:** ☐ SẴN SÀNG BÀN GIAO / ☐ CẦN SỬA

**Ghi chú lỗi phát hiện:**

1. ...
2. ...
3. ...

---

> Chạy dry-run này **ít nhất 3 ngày trước** ngày bàn giao thật để còn thời gian fix lỗi.
