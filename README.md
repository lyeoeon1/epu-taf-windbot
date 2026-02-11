# BotAI Houston

AI Chatbot hỗ trợ kiến thức tuabin gió, sử dụng RAG (Retrieval-Augmented Generation) với hỗ trợ song ngữ Tiếng Việt & English.

Wind turbine knowledge AI Chatbot powered by RAG (Retrieval-Augmented Generation) with bilingual support (Vietnamese & English).

## Tech Stack

**Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, Radix UI

**Backend:** FastAPI, LlamaIndex, OpenAI (GPT-4o-mini, text-embedding-3-small), Supabase (PostgreSQL + pgvector)

**Parsing:** LlamaParse (LlamaCloud) — hỗ trợ OCR cho PDF, DOCX, PPTX, XLSX

## Tính năng / Features

- Chat streaming theo thời gian thực (SSE) / Real-time streaming chat (SSE)
- Trả lời dựa trên tài liệu với RAG / Document-grounded answers with RAG
- Hỗ trợ song ngữ Tiếng Việt & English / Bilingual support (Vietnamese & English)
- Nạp tài liệu: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV / Document ingestion
- Quản lý phiên chat với lịch sử lưu trữ / Session management with persistent history
- Hiển thị Markdown, bảng, công thức toán (LaTeX/KaTeX) / Markdown, tables, math rendering

## Cấu trúc dự án / Project Structure

```
houston-v1/
├── src/                        # Frontend (Next.js)
│   ├── app/                    # Pages & layouts
│   ├── components/             # Chat UI components
│   └── hooks/                  # Custom React hooks
├── backend/                    # Backend (FastAPI)
│   ├── app/
│   │   ├── routers/            # API endpoints (chat, sessions, ingest, health)
│   │   ├── services/           # RAG, chat history, ingestion logic
│   │   ├── models/             # Pydantic schemas
│   │   ├── prompts/            # System prompts (EN/VI)
│   │   └── config.py           # Settings & env vars
│   ├── scripts/                # CLI tools (batch ingestion)
│   ├── data/                   # Documents folder
│   └── supabase_schema.sql     # Database schema
├── package.json
├── next.config.ts              # API rewrites (proxy to backend)
└── README.md
```

## Bắt đầu / Getting Started

### Yêu cầu / Prerequisites

- Node.js >= 18
- Python >= 3.10
- Tài khoản Supabase (với extension pgvector) / Supabase account (with pgvector extension)
- OpenAI API key
- LlamaCloud API key

### 1. Biến môi trường / Environment Variables

Tạo file `backend/.env`:

```env
OPENAI_API_KEY=your-openai-key
LLAMA_CLOUD_API_KEY=your-llamacloud-key

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key
SUPABASE_CONNECTION_STRING=postgresql://postgres:password@host:5432/postgres

FRONTEND_URL=http://localhost:3000
BACKEND_PORT=8000
```

### 2. Cài đặt Database / Database Setup

Chạy file SQL trên Supabase Dashboard (SQL Editor):

Run the SQL file on Supabase Dashboard (SQL Editor):

```bash
# File: backend/supabase_schema.sql
```

### 3. Chạy Backend / Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại / Backend will run at: `http://localhost:8000`

### 4. Chạy Frontend / Run Frontend

```bash
npm install
npm run dev
```

Frontend sẽ chạy tại / Frontend will run at: `http://localhost:3000`

> API calls từ frontend (`/api/*`) được proxy tới backend (`localhost:8000/api/*`) qua Next.js rewrites.

## Nạp tài liệu / Document Ingestion

### Qua CLI / Via CLI

```bash
cd backend
python scripts/ingest_docs.py --dir ./data --language vi --tier agentic
```

Tùy chọn / Options:
- `--dir` — Thư mục chứa tài liệu / Directory containing documents
- `--language` — `en` hoặc `vi` (mặc định: `en`)
- `--tier` — `cost_effective`, `agentic`, `agentic_plus` (mặc định: `agentic`)

### Qua API / Via API

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@document.pdf" \
  -F "language=vi"
```

## API Endpoints

| Method | Endpoint | Mô tả / Description |
|--------|----------|----------------------|
| POST | `/api/chat` | Gửi tin nhắn & nhận phản hồi streaming / Send message & get streaming response |
| POST | `/api/chat/sessions` | Tạo phiên chat mới / Create new chat session |
| GET | `/api/chat/sessions/{id}/messages` | Lấy lịch sử tin nhắn / Get session messages |
| POST | `/api/ingest` | Nạp tài liệu / Ingest document |
| GET | `/api/health` | Kiểm tra trạng thái / Health check |
