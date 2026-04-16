# Báo cáo kiểm thử Pipeline Nạp tài liệu (Ingestion Test Report)

> Tài liệu này là bằng chứng cho KPI **"Cập nhật dữ liệu thành công theo hướng dẫn, không lỗi"** trong biên bản nghiệm thu.
>
> Cập nhật lần cuối: Tháng 4/2026

---

## 1. Methodology

### 1.1. Phương pháp kiểm thử

Chúng tôi kiểm thử pipeline nạp tài liệu bằng **2 phương pháp**:

**(A) Tests thực tế trên production (manual)** — Đã ingest các batch tài liệu thật vào Supabase, ghi nhận kết quả trong `docs/deployment/ingestion-guide.md`, mục "Lịch sử nạp tài liệu".

**(B) Tests tự động (script)** — `backend/scripts/test_ingestion.py` chạy end-to-end 5 bước:

1. **Environment check** — Xác nhận OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_CONNECTION_STRING đã set.
2. **Supabase connectivity** — Kết nối và query các bảng `documents_metadata`, `chunk_fts`.
3. **Document parsing** — Parse file markdown test (không cần LlamaCloud API).
4. **Ingest roundtrip** — Tạo chunks vào `vecs.wind_turbine_docs`, query lại để verify retrievable.
5. **Cleanup** — Xóa test chunks, không để lại rác.

### 1.2. Tiêu chí PASS

| Bước | PASS khi |
|---|---|
| Environment | Tất cả 4 env vars đã set + 4 Python packages import OK |
| Supabase | Query thành công 2 bảng, không error SSL/connection |
| Parse | Document có text, metadata gồm language + domain + filename |
| Ingest | `num_chunks > 0`, query vector store tìm được chunks bằng test_tag |
| Cleanup | Tất cả test chunks đã xóa |

### 1.3. Cách chạy

```bash
# Trên VPS
ssh root@103.82.39.253
su - botai
cd ~/botai/repo/backend
source venv/bin/activate
set -a; source .env; set +a

# Full test
python scripts/test_ingestion.py

# Chỉ validate setup (không ingest)
python scripts/test_ingestion.py --dry-run
```

---

## 2. Lịch sử nạp tài liệu thực tế (Production)

Dữ liệu dưới đây được trích từ logs production và `docs/deployment/ingestion-guide.md`, mục "Lịch sử nạp tài liệu".

### 2.1. Bảng tổng hợp

| Ngày | Batch | Số file | Số chunks | Lỗi fatal | Tỷ lệ thành công |
|---|---|---|---|---|---|
| 11/02/2026 | Initial — Dien Gio 1-6.pdf | 1 | 50 | 0 | 100% |
| 11/02/2026 | Batch 2 — Dien Gio 2-6, 3-6, 4-6, 5-6 | 4 | 164 | 0 | 100% |
| 24/03/2026 | Wind Energy Handbook | 1 | 743 | 0 | 100% |
| 24/03/2026 | R06-004 Wind Energy Design | 1 | 102 | 0 | 100% |
| 24/03/2026 | windenergyengineering turbines | 1 | 748 | 0 | 100% |
| 06/04/2026 | EPU/TAF batch — 195-fowt-guide-jan24 | 1 | 196 | 0 | 100% |
| 06/04/2026 | EPU/TAF batch — Wind-Tecnology | 1 | 50 | 0 | 100% |
| 06/04/2026 | EPU/TAF batch — AWEA O&M 2017 | 1 | 476 | 0 | 100% |
| **Tổng** | **8 batches** | **11 files** | **2,529+ chunks** | **0** | **100%** |

### 2.2. Evidence

Có thể verify trên Supabase SQL Editor:

```sql
-- Tổng số vectors hiện có
SELECT COUNT(*) as total_vectors FROM vecs."wind_turbine_docs";
-- Expected: >= 2529

-- Vectors theo file
SELECT metadata->>'filename' as filename, COUNT(*) as chunks
FROM vecs."wind_turbine_docs"
GROUP BY metadata->>'filename'
ORDER BY chunks DESC;
```

### 2.3. Các sự cố không-fatal đã gặp và xử lý

Trong quá trình ingest production, có gặp một số cảnh báo/lỗi **không-fatal** đã được xử lý:

| Tình huống | Xử lý | Ảnh hưởng |
|---|---|---|
| `Could not create vector index: replace is set to False` | Rebuild index thủ công bằng SQL (documented trong ingestion-guide Bước 5) | Không — rebuild sau ingest là quy trình chuẩn |
| `Permission denied` khi script chạy | `chown -R botai:botai` directory | Không — xử lý tức thì |
| `LLAMA_CLOUD_API_KEY not set` | Load `.env` trước (`set -a; source .env; set +a`) | Không — fix môi trường |
| Warning về deprecated API | Ghi nhận, không block flow | Không |

**Không có trường hợp nào data bị corrupt hoặc ingestion phải rollback.**

---

## 3. Error handling đã test

Pipeline có cơ chế xử lý 7 loại lỗi được documented trong `docs/deployment/ingestion-guide.md`, mục "Xử lý lỗi thường gặp":

| Lỗi | Cơ chế xử lý | Test case |
|---|---|---|
| Đường dẫn sai | `os.path.isdir()` check, exit với error message | Manual: test với `--dir ./nonexistent` → exit code 1 |
| Permission denied | Fix bằng `chown`, script không bị crash | Production-tested 06/04/2026 |
| Python không có venv | Script báo lỗi rõ, hướng dẫn dùng `venv/bin/python` | Manual |
| `LLAMA_CLOUD_API_KEY not set` | Script báo lỗi rõ khi gọi LlamaCloud | Manual |
| File format lỗi | Try/except mỗi file — các file khác tiếp tục | Manual: thử ingest file corrupt |
| `SSL connection closed` | Supabase retry logic trong `supabase_retry.py` | Production-tested khi Supabase restore |
| `sudo` permission | User botai không có sudo → hướng dẫn thoát về root | Production |

---

## 4. Tests tự động (Script Results)

### 4.1. Dry-run (validate setup only)

Script `test_ingestion.py --dry-run` kiểm tra 3 bước đầu mà không tạo data:

**Kết quả mẫu:**
```
======================================================================
WINDBOT Ingestion Pipeline Verification
======================================================================
Mode: DRY-RUN (setup only)
Test fixture: /tmp/test_ingestion_a1b2c3d4.md
Test tag: testrun_a1b2c3d4

[1/5] Environment & dependencies check
  ✓ ENV OPENAI_API_KEY: PASS — set
  ✓ ENV SUPABASE_URL: PASS — set
  ✓ ENV SUPABASE_SERVICE_KEY: PASS — set
  ✓ ENV SUPABASE_CONNECTION_STRING: PASS — set
  ✓ Dependencies import: PASS — vecs, supabase, llama_index OK

[2/5] Supabase connectivity
  ✓ Query documents_metadata: PASS — 1 rows sampled
  ✓ Query chunk_fts: PASS — 1 rows sampled

[3/5] Document parsing
  ✓ Parse test file: PASS — 1 document(s), 612 chars
  ✓ Metadata enriched: PASS — language/domain/filename set

[DRY-RUN] Skipping ingest roundtrip and cleanup.

======================================================================
SUMMARY: 8/8 checks passed
======================================================================
```

### 4.2. Full end-to-end

Script `test_ingestion.py` (không có `--dry-run`) chạy đủ 5 bước, bao gồm tạo và xóa test chunks.

**Expected output:**
```
[1/5] Environment & dependencies check — 5 PASS
[2/5] Supabase connectivity — 2 PASS
[3/5] Document parsing — 2 PASS
[4/5] Ingest + query roundtrip — 2 PASS (Ingest creates N chunks, Query finds test chunks)
[5/5] Cleanup — 1 PASS (Remove test chunks)

SUMMARY: 12/12 checks passed
```

### 4.3. Khi nào nên chạy

- **Trước mỗi lần ingest batch lớn:** `--dry-run` để verify setup
- **Sau deploy/update code:** full test để verify pipeline còn hoạt động
- **Khi có sự cố nghi ngờ:** full test + xem chỗ nào FAIL

---

## 5. Kết luận — Đáp ứng KPI nghiệm thu

### 5.1. KPI: "Cập nhật dữ liệu thành công theo hướng dẫn, không lỗi"

| Tiêu chí | Bằng chứng | Đáp ứng? |
|---|---|---|
| Có hướng dẫn cập nhật rõ ràng | `docs/deployment/ingestion-guide.md` (200+ dòng, 9 bước) | ✅ |
| Cập nhật thành công | 8 batches, 11 files, 2,529+ chunks, 0 lỗi fatal | ✅ |
| Có xử lý lỗi | 7 loại lỗi documented + test case | ✅ |
| Có test tự động | `backend/scripts/test_ingestion.py` — 12 checks | ✅ |
| Có runbook vận hành | `docs/deployment/ingestion-runbook.md` | ✅ |

### 5.2. Recommendations sau bàn giao

- **Hàng tháng:** Chạy `test_ingestion.py` để verify pipeline vẫn hoạt động
- **Trước khi ingest batch mới:** Chạy `--dry-run` để catch vấn đề setup sớm
- **Ghi nhận** mỗi lần ingest vào `docs/deployment/ingestion-guide.md` (lịch sử) để duy trì audit trail

---

## Tài liệu liên quan

| Tài liệu | Mục đích |
|---|---|
| `docs/deployment/ingestion-guide.md` | Hướng dẫn chi tiết nạp tài liệu |
| `docs/deployment/ingestion-runbook.md` | Runbook vận hành (pre-check → execute → verify → error recovery) |
| `backend/scripts/test_ingestion.py` | Script test tự động |
| `backend/scripts/ingest_docs.py` | Script ingest chính |
| `backend/app/services/ingestion.py` | Implementation pipeline |
