# WINDBOT API — Hướng dẫn sử dụng

> Tài liệu này giải thích cách sử dụng WINDBOT API, bổ sung cho file spec chuẩn `backend/openapi.yaml` (OpenAPI 3.0).
> Cập nhật lần cuối: Tháng 4/2026

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Quick start](#2-quick-start)
3. [Chi tiết từng endpoint](#3-chi-tiết-từng-endpoint)
4. [Server-Sent Events (SSE) cho /api/chat](#4-server-sent-events-sse-cho-apichat)
5. [Error handling](#5-error-handling)
6. [Swagger UI & nhập OpenAPI spec](#6-swagger-ui--nhập-openapi-spec)

---

## 1. Tổng quan

### Base URL

| Môi trường | URL |
|---|---|
| Local development | `http://localhost:8001` |
| VPS (qua SSH tunnel) | `http://127.0.0.1:8001` |
| Production (qua reverse proxy Vercel) | `https://windbot.vercel.app` |

### Authentication

Hiện tại API **không yêu cầu authentication** — chạy nội bộ sau reverse proxy, chỉ frontend Vercel được phép gọi qua CORS whitelist.

Nếu muốn thêm authentication, xem `docs/guides/migration-guide.md`, mục "Security hardening".

### CORS

Frontend Vercel được whitelist trong `backend/app/main.py`. Domain khác sẽ bị chặn.

### Content-Type

- Request: `application/json` (hoặc `multipart/form-data` cho `/api/ingest`)
- Response: `application/json` (hoặc `text/event-stream` cho `/api/chat`)

### API Documentation trực tiếp

Backend FastAPI tự sinh Swagger UI tại:

```
http://localhost:8001/docs         (local)
http://127.0.0.1:8001/docs         (VPS)
```

---

## 2. Quick start

### Kiểm tra backend

```bash
curl -s http://localhost:8001/api/health
# {"status":"ok","version":"0.1.0"}
```

### Hỏi chatbot (streaming SSE)

```bash
# Bước 1: Tạo phiên chat
SESSION=$(curl -s -X POST http://localhost:8001/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","language":"vi"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Session: $SESSION"

# Bước 2: Gửi câu hỏi (SSE)
curl -N -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"message\":\"Tua-bin gió là gì?\",\"language\":\"vi\"}"
```

### Tra cứu glossary

```bash
# Tìm theo từ khóa tiếng Anh
curl -s "http://localhost:8001/api/glossary?term=nacelle&language=en"

# Lọc theo category
curl -s "http://localhost:8001/api/glossary?category=structure"
```

### Nạp tài liệu

```bash
curl -X POST http://localhost:8001/api/ingest \
  -F "files=@wind_handbook.pdf" \
  -F "language=vi" \
  -F "tier=agentic"
```

---

## 3. Chi tiết từng endpoint

### 3.1. `GET /api/health` — Kiểm tra trạng thái

Response:
```json
{"status": "ok", "version": "0.1.0"}
```

**Khi nào dùng:** Health check trong monitoring/alerting.

---

### 3.2. `POST /api/chat/sessions` — Tạo phiên chat

Request body:
```json
{
  "title": "Hỏi về bảo trì tua-bin",
  "language": "vi"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Hỏi về bảo trì tua-bin",
  "language": "vi",
  "created_at": "2026-04-16T10:30:00Z"
}
```

**Python example:**
```python
import requests

response = requests.post(
    "http://localhost:8001/api/chat/sessions",
    json={"title": "Test", "language": "vi"}
)
session_id = response.json()["id"]
```

**JavaScript example:**
```javascript
const response = await fetch('http://localhost:8001/api/chat/sessions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({title: 'Test', language: 'vi'})
});
const {id: sessionId} = await response.json();
```

---

### 3.3. `POST /api/chat` — Gửi tin nhắn (SSE streaming)

Request body:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Tua-bin gió là gì?",
  "language": "vi"
}
```

**Response:** Server-Sent Events stream. Xem [mục 4](#4-server-sent-events-sse-cho-apichat).

**Python example (streaming):**
```python
import json
import httpx

with httpx.stream(
    "POST",
    "http://localhost:8001/api/chat",
    json={
        "session_id": session_id,
        "message": "Tua-bin gió là gì?",
        "language": "vi"
    },
    timeout=60.0,
) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            if "token" in event:
                print(event["token"], end="", flush=True)
            elif event.get("done"):
                print()  # newline
            elif "sources" in event:
                print(f"Sources: {event['sources']}")
            elif "suggestions" in event:
                print(f"Suggestions: {event['suggestions']}")
```

**JavaScript example (browser with fetch):**
```javascript
const response = await fetch('http://localhost:8001/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: sessionId,
    message: 'Tua-bin gió là gì?',
    language: 'vi'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, {stream: true});
  const lines = buffer.split('\n\n');
  buffer = lines.pop(); // Keep incomplete line

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      if (event.token) process.stdout.write(event.token);
      if (event.done) console.log();
      if (event.sources) console.log('Sources:', event.sources);
      if (event.suggestions) console.log('Suggestions:', event.suggestions);
    }
  }
}
```

---

### 3.4. `GET /api/chat/sessions/{session_id}/messages` — Lấy lịch sử

Response:
```json
[
  {
    "id": "msg-001",
    "role": "user",
    "content": "Tua-bin gió là gì?",
    "metadata": {},
    "created_at": "2026-04-16T10:30:00Z"
  },
  {
    "id": "msg-002",
    "role": "assistant",
    "content": "Tua-bin gió là thiết bị chuyển đổi năng lượng gió...",
    "metadata": {
      "language": "vi",
      "question_type": "TECHNICAL",
      "sources": [{"id": 1, "filename": "wind_handbook.pdf", "page": 12, "score": 0.85}]
    },
    "created_at": "2026-04-16T10:30:05Z"
  }
]
```

---

### 3.5. `POST /api/ingest` — Nạp tài liệu

**Content-Type:** `multipart/form-data`

Fields:
- `files` (required): Một hoặc nhiều file
- `language` (optional, default: `en`): `en` hoặc `vi`
- `tier` (optional, default: `agentic`): `cost_effective` / `agentic` / `agentic_plus`

Response:
```json
[
  {"status": "success", "chunks_created": 196, "filename": "wind_handbook.pdf"},
  {"status": "success", "chunks_created": 50, "filename": "maintenance_guide.docx"}
]
```

**Python example:**
```python
import requests

files = [
    ('files', open('doc1.pdf', 'rb')),
    ('files', open('doc2.docx', 'rb')),
]
data = {'language': 'vi', 'tier': 'agentic'}

response = requests.post(
    "http://localhost:8001/api/ingest",
    files=files,
    data=data,
)
print(response.json())
```

> **Lưu ý:** Sau khi nạp, cần rebuild vector index trên Supabase. Xem `docs/deployment/ingestion-guide.md`.

---

### 3.6. `GET /api/glossary` — Tìm kiếm thuật ngữ

Query parameters:

| Param | Type | Mô tả |
|---|---|---|
| `term` | string | Từ khóa tìm kiếm (partial match) |
| `category` | string | `structure`, `components`, `operations`, `maintenance`, `safety`, `troubleshooting`, `general` |
| `language` | string | `en` hoặc `vi` (mặc định: `en`) |

Response:
```json
[
  {
    "id": "glo-001",
    "term_en": "nacelle",
    "term_vi": "vỏ tua-bin",
    "definition_en": "The housing at the top of the tower...",
    "definition_vi": "Phần vỏ bọc trên đỉnh tháp...",
    "category": "structure",
    "abbreviation": null,
    "related_terms": ["tower", "hub"]
  }
]
```

---

### 3.7. `GET /api/glossary/{term_id}` — Chi tiết thuật ngữ

Response: Single `GlossaryEntry` object (xem 3.6).

---

### 3.8. `POST /api/feedback` — Gửi phản hồi

Request body:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_content": "Câu trả lời về công suất tua-bin",
  "feedback_tags": ["vote_positive", "accurate", "helpful"],
  "feedback_text": "Thông tin rõ ràng và đầy đủ"
}
```

**Tags hỗ trợ:**
- Tích cực: `vote_positive`, `accurate`, `helpful`, `easy_to_understand`
- Tiêu cực: `vote_negative`, `inaccurate`, `unhelpful`, `hard_to_understand`

**Phản hồi tích cực** sẽ kích hoạt cơ chế promote corrections trong phiên lên global (cross-session).

Response (status 201):
```json
{"status": "ok", "id": "fb-001"}
```

---

## 4. Server-Sent Events (SSE) cho `/api/chat`

### Format event

Mỗi event có dạng:
```
data: <JSON>\n\n
```

### Luồng events

1. **Tokens** (nhiều event):
   ```
   data: {"token": "Tua"}

   data: {"token": "-bin"}

   data: {"token": " gió"}
   ```

2. **Done signal** (1 event):
   ```
   data: {"done": true}
   ```

3. **Sources** (optional, sau done):
   ```
   data: {"sources": [{"id": 1, "text": "...", "filename": "wind_handbook.pdf", "page": 12, "score": 0.85}], "content": "..."}
   ```
   - `sources` chứa các nguồn tài liệu được cite trong câu trả lời
   - `content` là full response text với citations `[N]` đã renumber sequential (1, 2, 3...)

4. **Suggestions** (optional, sau done):
   ```
   data: {"suggestions": ["Các bộ phận chính?", "Công suất là gì?", "Cách bảo trì?"]}
   ```
   - Luôn có đúng 3 gợi ý câu hỏi tiếp theo

### Xử lý phía client

**Quy trình đề xuất:**
1. Hiển thị từng token ngay khi nhận được (realtime streaming)
2. Khi nhận `done: true` → ẩn loading indicator, cho phép user gõ tiếp
3. Khi nhận `sources` → render citations `[N]` thành links
4. Khi nhận `suggestions` → hiển thị 3 nút gợi ý

### Lưu ý quan trọng

- **Không buffer** ở reverse proxy (Nginx: `X-Accel-Buffering: no`)
- **Timeout** client nên ≥60s (câu trả lời dài có thể mất lâu)
- Nếu `/api/chat` trả về **503**, client nên retry sau 2-5 giây
- Khi connection bị đứt giữa chừng, câu hỏi đã được lưu vào DB — có thể reload từ `/api/chat/sessions/{id}/messages`

---

## 5. Error handling

### HTTP Status codes

| Code | Mô tả | Hành động |
|---|---|---|
| 200 | Success | — |
| 201 | Created (feedback) | — |
| 400 | Bad request (schema validation lỗi) | Kiểm tra request body |
| 404 | Not found (glossary term) | — |
| 422 | Unprocessable entity (Pydantic validation) | Kiểm tra type các field |
| 500 | Internal server error | Xem logs backend |
| 503 | Service unavailable (transient) | Retry sau 2-5s |

### Error response format

```json
{"detail": "Service temporarily unavailable. Please retry."}
```

### Các lỗi thường gặp

**`SSL connection has been closed unexpectedly`** trong logs
- Nguyên nhân: Supabase bị pause (free tier, 7 ngày không hoạt động)
- Fix: Vào Supabase Dashboard → Restore project → Restart backend

**`500: An internal error occurred`**
- Kiểm tra logs: `journalctl -u botai-backend --since "10 min ago"`
- Thường do: OpenAI API timeout, API key hết quota, lỗi model

**`503: Service temporarily unavailable`**
- Transient network error
- Client nên retry sau 2-5s

Xem thêm: `docs/guides/disaster-recovery.md`

---

## 6. Swagger UI & nhập OpenAPI spec

### Swagger UI live (backend đang chạy)

```
http://localhost:8001/docs
```

Cho phép:
- Xem tất cả endpoints interactive
- Test request trực tiếp từ browser
- Xem schemas đầy đủ

### Nhập OpenAPI spec vào công cụ khác

**Postman:**
1. Mở Postman → File → Import
2. Chọn file `backend/openapi.yaml`
3. Tất cả endpoints được import thành collection

**Insomnia:**
1. Create → Import from File
2. Chọn `backend/openapi.yaml`

**Redoc (static HTML docs):**
```bash
npx @redocly/cli build-docs backend/openapi.yaml -o api-docs.html
```

**Generate client SDK:**
```bash
# Python client
openapi-generator-cli generate -i backend/openapi.yaml -g python -o ./clients/python

# TypeScript/Axios client
openapi-generator-cli generate -i backend/openapi.yaml -g typescript-axios -o ./clients/typescript
```

### Validate spec

```bash
pip install openapi-spec-validator
openapi-spec-validator backend/openapi.yaml
# Expected: no output (valid)
```

---

## Tài liệu liên quan

| Tài liệu | Mục đích |
|---|---|
| `backend/openapi.yaml` | Spec chuẩn OpenAPI 3.0 |
| `docs/architecture/rag-retrieval.md` | Giải thích RAG pipeline |
| `docs/deployment/ingestion-guide.md` | Quy trình nạp tài liệu chi tiết |
| `docs/deployment/ingestion-runbook.md` | Runbook vận hành ingestion |
| `docs/guides/disaster-recovery.md` | Xử lý sự cố |
| `docs/guides/admin-guide-advanced.md` | Quản trị nâng cao |
