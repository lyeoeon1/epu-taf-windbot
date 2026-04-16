# Troubleshooting Map — Lỗi → File:dòng

> Bảng tra **dành cho người sửa code** WINDBOT: gặp triệu chứng X, mở thẳng
> file:dòng Y. Bổ sung cho `admin-guide.md` (hướng vận hành — restart service,
> đọc log) và `admin-guide-advanced.md` (SSH, systemd).
>
> Tất cả file:dòng đã verify trên branch `lyeoeon1/deliverables-plan` ngày
> 2026-04-16. Sau mỗi lần refactor lớn, hãy soát lại file này (chạy
> `grep -n` các function name để cập nhật).

---

## Mục lục

1. [Citation & retrieval](#1-citation--retrieval)
2. [Bot trả lời sai ngôn ngữ / cụt giữa chừng](#2-bot-trả-lời-sai-ngôn-ngữ--cụt-giữa-chừng)
3. [API errors (401, 429, 500, 503)](#3-api-errors-401-429-500-503)
4. [Performance & cost](#4-performance--cost)
5. [Deploy & smoke fail](#5-deploy--smoke-fail)
6. [Khi sửa, nhớ chạy gì để khỏi break](#6-khi-sửa-nhớ-chạy-gì-để-khỏi-break)

---

## 1. Citation & retrieval

### 1.1. Citation số sai / lệch source / nhảy lung tung

**Triệu chứng:** User thấy `[3]` nhưng nội dung click vào lại là tài liệu khác,
hoặc citation đánh số `[1] [3] [7]` thay vì `[1] [2] [3]`.

**Bắt đầu sửa ở:**
- `backend/app/routers/chat.py:38-108` — `renumber_citations` (đảm bảo số liên
  tục theo thứ tự xuất hiện)
- `backend/app/routers/chat.py:100-127` — `verify_citations` (kiểm tra
  keyword overlap, drop/swap citation sai)
- `backend/app/routers/chat.py:144` — magic threshold `if len(overlap) >= 2`
  quyết định "giữ hay drop". Đổi ngưỡng = đảo lộn nhiều answer (xem mục 4.3).

**Reproduce + verify:**
```bash
cd backend && python scripts/test_citations.py
# Expect 28/28 pass — nếu fail, behavior đã thay đổi
```

> Đụng pipeline này **luôn chạy `test_citations.py` trước và sau** khi sửa.
> Đây là logic phức tạp nhất trong dự án (xem audit ở plan).

---

### 1.2. Search result kém / thiếu chunk Việt / thừa Q&A

**Triệu chứng:** Bot trả lời nông; search top-k toàn tài liệu tiếng Anh dù
có bản tiếng Việt; hoặc Q&A pairs do AI tự sinh đè lên handbook.

**Bắt đầu sửa ở:**
- `backend/app/services/advanced_retriever.py` — Phase A/B/C pipeline
  (multi-query → dense + BM25 → RRF fusion → QA filter → VI boost → rerank)
- `backend/app/services/qa_chunk.py` — quy tắc detect Q&A chunks (single
  source of truth, dùng cả ở `advanced_retriever` và `rag.py`)
- `backend/app/config.py` — toggle nhanh không cần sửa code:
  - `enable_multi_query`, `enable_advanced_retrieval`
  - `enable_vi_priority`, `vi_score_boost`, `vi_reserved_slots`
  - `dense_weight`, `sparse_weight`, `rerank_top_k`

**Reproduce + verify:**
```bash
# Kiểm tra QA filter còn đúng
cd backend && python scripts/test_qa_chunk.py        # 9/9 pass

# Smoke chạy chuỗi search end-to-end
python scripts/smoke.py http://localhost:8001 -v
```

---

## 2. Bot trả lời sai ngôn ngữ / cụt giữa chừng

### 2.1. Bot trả lời nhầm tiếng Việt ↔ Anh

**Triệu chứng:** User hỏi tiếng Việt, bot trả lời tiếng Anh (hoặc ngược lại);
hoặc trộn lẫn 2 ngôn ngữ trong cùng câu trả lời.

**Bắt đầu sửa ở:**
- `backend/app/prompts/system.py` — system prompt theo ngôn ngữ
- `backend/app/services/corrections.py:92` — `detect_input_language(message)`
  (regex phân loại Việt/Anh dựa trên dấu)
- `backend/app/routers/chat.py` — chỗ gọi `detect_input_language` để build
  `corrections_block` với `user_language_hint`

> Nếu user gửi câu hỏi mix (`"Yaw control là gì?"`) và detect sai → cân nhắc
> tăng ngưỡng dấu tiếng Việt trong `detect_input_language`.

---

### 2.2. Câu trả lời cụt giữa chừng (SSE bị ngắt)

**Triệu chứng:** Frontend hiển thị nửa câu rồi dừng; không thấy event `done`.

**Bắt đầu sửa ở:**
- `backend/app/routers/chat.py:481-594` — `event_generator` (closure 7-cấp,
  thread + async + queue + sentinel). **Phức tạp, đụng cẩn thận.** Nếu chỉ
  cần thêm event mới (vd `metrics`), thêm `yield f"data: ..."` không cần
  refactor.
- `src/hooks/use-chat.ts:103, 165, 193` — 3 chỗ `} catch {}` empty đang
  swallow lỗi parse SSE im lặng. Khi debug, thay tạm bằng
  `} catch (e) { console.warn("SSE parse failed:", e); }` để xem nguyên nhân.

**Reproduce:**
- Hỏi câu dài (>500 từ trả lời) → bấm F12 → Network tab → xem stream events.

---

## 3. API errors (401, 429, 500, 503)

### 3.1. "401 Invalid X-Admin-Key" khi gọi `/api/ingest`

**Triệu chứng:** `curl /api/ingest` trả `{"detail": "Invalid or missing X-Admin-Key."}`.

**Bắt đầu sửa ở:**
- `backend/app/dependencies.py` — hàm `verify_admin_key` (dùng
  `secrets.compare_digest` chống timing attack)
- File `.env` trên server: biến `ADMIN_API_KEY` phải khớp header client gửi

**Sinh khoá mới:**
```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
# Copy vào ADMIN_API_KEY trong /home/botai/repo/backend/.env
sudo systemctl restart botai-backend
```

> Nếu trả `503 "Admin endpoints disabled"` → server chưa cấu hình
> `ADMIN_API_KEY` (rỗng). Đây là behavior cố ý: endpoint admin tắt mặc định.

---

### 3.2. "429 Too Many Requests" trên `/api/chat`

**Triệu chứng:** User bị block sau khi gửi liên tục nhiều câu hỏi.

**Bắt đầu sửa ở:**
- `backend/app/limiter.py` — singleton `Limiter` đọc IP qua header
  `X-Forwarded-For` (left-most). Nếu sau Cloudflare/Ngrok mà IP detect sai
  → check tunnel có forward header không.
- `.env`: biến `CHAT_RATE_LIMIT` (mặc định `30/minute`). Định dạng slowapi:
  `"60/minute"`, `"1000/hour"`, `"10/second"`.

**Verify rate limit hoạt động:**
```bash
for i in {1..40}; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8001/api/chat \
    -H "Content-Type: application/json" \
    -d '{"session_id":"00000000-0000-0000-0000-000000000000","message":"hi","language":"en"}'
done | sort | uniq -c
# Expect: 30 lần "200" hoặc "5xx" + 10 lần "429"
```

---

### 3.3. "503 Vector store not initialized"

**Triệu chứng:** Mọi endpoint cần index trả `{"detail": "Vector store not initialized..."}`.

**Bắt đầu sửa ở:**
- `backend/app/dependencies.py:19-25` — `get_index` raise 503 khi
  `app_state["index"]` vắng mặt
- Startup lifespan ở `backend/app/main.py` đã fail. Đọc log:
  ```bash
  sudo journalctl -u botai-backend -n 100 | grep STARTUP
  ```
- Thường nguyên nhân: `SUPABASE_*` env vars sai/thiếu trong `.env`

**Verify Supabase reachable:**
```bash
curl -s "$SUPABASE_URL/rest/v1/" -H "apikey: $SUPABASE_SERVICE_KEY" | head
```

---

### 3.4. 500 Internal Server Error trên `/api/chat`

**Triệu chứng:** Streaming bắt đầu xong dừng giữa chừng, hoặc trả 500 ngay.

**Bắt đầu sửa ở:**
- `backend/app/routers/chat.py:340` — endpoint `chat()`. Block try/except
  ở giữa function bắt `httpcore/httpx` errors riêng (503), còn lại 500.
- Xem traceback đầy đủ: `journalctl -u botai-backend -n 200 | grep -A 30 "Chat endpoint failed"`

---

## 4. Performance & cost

### 4.1. OpenAI bill tăng đột ngột

**Bắt đầu kiểm tra theo thứ tự:**

1. **Rate limit có đang đúng không?** — xem mục 3.2. Nếu `CHAT_RATE_LIMIT`
   bị set quá rộng (`1000/minute`) → spam dễ.
2. **BM25 có đang fail âm thầm không?** — log
   `BM25 reliability: X failures over Y calls (Z%)` mỗi 100 request, tạo bởi
   `backend/app/routers/chat.py:296` `_record_bm25_attempt`. Nếu Z > 10%, dense
   search phải ôm context lớn hơn → mỗi câu hỏi đắt hơn.
3. **Multi-query đang sinh bao nhiêu variant?** — `multi_query_count` ở
   `backend/app/config.py`. Mỗi variant = thêm 1 LLM call (~$0.001-0.003).

---

### 4.2. Bot trả lời chậm (TTFT > 10s)

**Bắt đầu sửa ở:**
- `backend/app/services/advanced_retriever.py` — Phase A/B/C có speculative
  execution. Tắt `enable_multi_query` ở `config.py` để giảm TTFT ~3s.
- `backend/app/config.py` — tắt `enable_hyde` (đã tắt sẵn vì +10s).
- Reranker: xem ONNX model có load được không (`/api/health/debug`
  trả `reranker_available`). Nếu False → fallback FlashRank slow.

---

### 4.3. Citation logic strict quá / lỏng quá

**Triệu chứng:** Bot kèm citation hợp lý nhưng bị drop hết (strict);
hoặc giữ citation rác không liên quan content (lỏng).

**Bắt đầu sửa ở:**
- `backend/app/routers/chat.py:144` — `if len(overlap) >= 2`. Đây là magic
  number — không có lý do toán học, chỉ là cảm tính.
  - Tăng lên `>= 3`: drop nhiều citation hơn (strict)
  - Giảm xuống `>= 1`: giữ nhiều citation hơn (lỏng)
- `backend/app/routers/chat.py:81-97` — `_extract_keywords` (regex `\w{2,}` +
  stopwords). Bug đã biết: `gear-box` tách thành `gear` + `box`, không match
  `gearbox`. Xem `test_citations.py` test "hyphen splits word".

> Sau mỗi lần đổi threshold/keyword extractor, **bắt buộc update
> `test_citations.py`** cho khớp expectation mới.

---

## 5. Deploy & smoke fail

### 5.1. `deploy.sh` fail ở bước smoke

**Triệu chứng:** systemctl restart OK nhưng smoke báo `FAIL` cho 1 endpoint.

**Bắt đầu sửa:**
- Đọc dòng `FAIL  POST /api/X — ...` để biết endpoint nào sai
- Xem traceback backend:
  ```bash
  sudo journalctl -u botai-backend -n 100
  ```
- Re-run smoke thủ công với verbose:
  ```bash
  /home/botai/repo/backend/venv/bin/python \
    /home/botai/repo/backend/scripts/smoke.py http://127.0.0.1:8001 -v
  ```

**Bypass khẩn (rollback emergency):**
```bash
SKIP_SMOKE=1 sudo bash /home/botai/repo/deploy/deploy.sh
```

> Chỉ dùng `SKIP_SMOKE=1` khi deploy để revert một bug cũ; không dùng để
> cố tình giấu test fail.

---

### 5.2. Cần thay đổi format Q&A corpus

**Triệu chứng:** Muốn QA chunks dùng prefix khác (`Câu hỏi:` thay `Q:`),
hoặc đổi đường dẫn `qa_corpus/` sang `qna/`.

**Bắt đầu sửa ở (chỉ 1 chỗ duy nhất sau P3):**
- `backend/app/services/qa_chunk.py` — sửa logic detect
- `backend/scripts/ingest_qa.py:47, 57, 66, 76` — sửa format ghi vào
  Supabase cho khớp

**Verify:**
```bash
cd backend && python scripts/test_qa_chunk.py
# Update test cases trong test_qa_chunk.py cho khớp format mới
```

---

## 6. Khi sửa, nhớ chạy gì để khỏi break

| Khi đụng vào... | Chạy trước & sau |
|---|---|
| Citation logic (`chat.py:38-127`) | `python backend/scripts/test_citations.py` (28/28) |
| `qa_chunk.py` hoặc `ingest_qa.py` | `python backend/scripts/test_qa_chunk.py` (9/9) |
| Bất kỳ router/service backend | `python backend/scripts/smoke.py http://localhost:8001 -v` (5/5) |
| Ingest pipeline | `python backend/scripts/test_ingestion.py` (end-to-end) |
| Trước mỗi `git push` lên `epu-taf-windbot` | Cả 4 lệnh trên |

> Cài đặt git hook tự động (optional):
> ```bash
> # .git/hooks/pre-push
> #!/bin/bash
> cd backend && python scripts/test_citations.py && python scripts/test_qa_chunk.py
> ```

---

## Liên quan

- `docs/guides/admin-guide.md` — hướng dẫn vận hành (restart, log, backup)
- `docs/guides/admin-guide-advanced.md` — SSH, systemd, SQL queries
- `docs/guides/disaster-recovery.md` — recovery plan khi sự cố nghiêm trọng
- `docs/deployment/ingestion-runbook.md` — checklist nạp tài liệu mới
- `docs/api/api-guide.md` — chi tiết từng API endpoint (request/response)
