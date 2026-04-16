# WINDBOT — AI Chatbot Tua-bin Gió

AI Chatbot hỗ trợ kiến thức tua-bin gió, sử dụng RAG (Retrieval-Augmented Generation) với hỗ trợ song ngữ Tiếng Việt & English. Dự án thuộc Qualcomm VR Lab.

**Live demo:** https://windbot.vercel.app

## Tính năng chính

- Chat streaming thời gian thực (SSE)
- Trả lời dựa trên tài liệu với RAG
- Hỗ trợ song ngữ Tiếng Việt & English
- Nạp tài liệu: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV
- Quản lý phiên chat với lịch sử lưu trữ
- Hiển thị Markdown, bảng, công thức toán (LaTeX/KaTeX)
- Hiển thị sơ đồ Mermaid tương tác
- Kho thuật ngữ song ngữ (87 thuật ngữ)
- Gợi ý câu hỏi tiếp theo (follow-up suggestions)
- Hệ thống correction learning

## Kiến trúc hệ thống

```
Người dùng → Frontend (Next.js / Vercel) → Backend API (FastAPI / VPS) → Knowledge Base (Supabase pgvector)
                                                                        → LLM (OpenAI gpt-4.1-mini)
```

| Thành phần | Công nghệ | Hosting |
|------------|-----------|---------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 | Vercel |
| Backend | FastAPI, LlamaIndex, Python 3.10+ | VPS (Gunicorn + systemd) |
| Database | PostgreSQL + pgvector (Supabase) | Supabase Cloud |
| AI Model | OpenAI gpt-4.1-mini | OpenAI API |
| Embedding | text-embedding-3-small (1536 dims) | OpenAI API |
| Parsing | LlamaParse (OCR Tiếng Việt + English) | LlamaCloud |

## Cấu trúc dự án

```
windbot/
├── src/                          # Frontend (Next.js)
│   ├── app/                      # Pages & layouts
│   ├── components/               # Chat UI components
│   ├── hooks/                    # Custom React hooks
│   └── lib/                      # Utilities
├── backend/                      # Backend (FastAPI)
│   ├── app/                      # Application code
│   │   ├── routers/              # API endpoints
│   │   ├── services/             # RAG, chat history, ingestion
│   │   ├── models/               # Pydantic schemas
│   │   ├── prompts/              # System prompts (VI/EN)
│   │   └── config.py             # Settings
│   ├── scripts/                  # CLI tools
│   ├── data/                     # Documents & knowledge base
│   └── supabase_schema.sql       # Database schema
├── deploy/                       # Deployment scripts
├── docs/                         # Tài liệu
│   ├── architecture/             # Kiến trúc hệ thống
│   ├── deployment/               # Hướng dẫn triển khai
│   ├── evaluation/               # Benchmark & test results
│   ├── guides/                   # Hướng dẫn sử dụng
│   │   ├── admin-guide.md        # Hướng dẫn quản trị
│   │   ├── correction-learning.md # Hệ thống correction
│   │   └── migration-guide.md    # Hướng dẫn migration LLM
│   ├── handover/                 # Tài liệu bàn giao
│   │   ├── handover-report.md    # Biên bản bàn giao
│   │   ├── sla.md                # Thỏa thuận hỗ trợ
│   │   ├── handover-checklist.md # Checklist
│   │   └── training-outline.md   # Kế hoạch đào tạo
│   ├── product-requirements.md   # Yêu cầu nghiệp vụ
│   ├── dataset-card.md           # Dataset Card
│   └── changelog.md              # Nhật ký thay đổi
└── README.md
```

## Bắt đầu sử dụng

### Yêu cầu

- Node.js >= 18
- Python >= 3.10
- Supabase account (với pgvector extension)
- OpenAI API key
- LlamaCloud API key

### 1. Cài đặt Database

Chạy file `backend/supabase_schema.sql` trên Supabase Dashboard (SQL Editor).

### 2. Cấu hình môi trường

Copy file mẫu và điền thông tin:

```bash
cp backend/.env.example backend/.env
```

Chỉnh sửa `backend/.env`:

```env
OPENAI_API_KEY=your-key
LLAMA_CLOUD_API_KEY=your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-key
SUPABASE_CONNECTION_STRING=postgresql://...
FRONTEND_URL=http://localhost:3000
BACKEND_PORT=8001
```

### 3. Chạy Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. Chạy Frontend

```bash
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/chat` | Gửi tin nhắn & nhận phản hồi streaming (SSE) |
| POST | `/api/chat/sessions` | Tạo phiên chat mới |
| GET | `/api/chat/sessions/{id}/messages` | Lấy lịch sử tin nhắn |
| POST | `/api/ingest` | Nạp tài liệu |
| GET | `/api/glossary` | Tra cứu thuật ngữ |
| GET | `/api/glossary/{term_id}` | Chi tiết thuật ngữ |
| GET | `/api/health` | Kiểm tra trạng thái |
| GET | `/docs` | API documentation (Swagger UI) |

**API documentation:**
- Swagger UI live: `http://[server]:8001/docs` (auto-generated từ FastAPI)
- OpenAPI spec: `backend/openapi.yaml` (chuẩn OpenAPI 3.0.3)
- Hướng dẫn sử dụng + examples: `docs/api/api-guide.md`

## Tài liệu

| Tài liệu | Đường dẫn | Mô tả |
|-----------|-----------|-------|
| Hướng dẫn quản trị | `docs/guides/admin-guide.md` | Quản lý hệ thống hàng ngày |
| Hướng dẫn triển khai | `docs/deployment/deployment-guide.md` | Deploy production |
| Hướng dẫn API | `docs/api/api-guide.md` | Sử dụng API với examples (curl, Python, JS) |
| Runbook ingestion | `docs/deployment/ingestion-runbook.md` | Vận hành pipeline nạp tài liệu |
| Hướng dẫn nạp tài liệu | `docs/deployment/ingestion-guide.md` | Thêm tài liệu mới |
| Hướng dẫn migration | `docs/guides/migration-guide.md` | Chuyển sang LLM khác |
| Yêu cầu nghiệp vụ | `docs/product-requirements.md` | 19 yêu cầu + trạng thái |
| Biên bản bàn giao | `docs/handover/handover-report.md` | Xác nhận bàn giao |
| Thỏa thuận hỗ trợ | `docs/handover/sla.md` | SLA 3 tháng |

## Chất lượng

- Test suite: 46 test cases, **85% pass rate**
- Benchmark: 150 cặp Q&A, 5 categories
- Consistency: 100%, Bilingual: 100%, Suggestions: 100%
- Knowledge Base: 2900+ chunks, 87 thuật ngữ

## Liên hệ hỗ trợ

Trong thời gian SLA (3 tháng từ ngày bàn giao):
- Email: [placeholder]
- Xem chi tiết: `docs/handover/sla.md`

## License

[Placeholder — to be determined by EPU/TAF agreement]
