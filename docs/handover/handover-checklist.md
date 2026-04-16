# CHECKLIST BÀN GIAO DỰ ÁN WINDBOT

**Dự án:** AI Chatbot Tua-bin Gió (WINDBOT)

---

## Danh sách hạng mục bàn giao

| STT | Hạng mục | Chi tiết | Trạng thái | Ghi chú |
|-----|----------|----------|------------|---------|
| 1 | Source code Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 | ☐ | Git repository |
| 2 | Source code Backend | FastAPI, LlamaIndex, Python 3.10+ | ☐ | Git repository |
| 3 | Database schema | supabase_schema.sql + migrations | ☐ | |
| 4 | Deploy scripts | deploy.sh, setup-vps.sh, botai-backend.service | ☐ | Thư mục deploy/ |
| 5 | Knowledge Base — PDF Documents | 5 file PDF gốc + 3 batch bổ sung (25 + 2900+ chunks) | ☐ | Vector store trên Supabase |
| 6 | Knowledge Base — Q&A Corpus | 150 cặp Q&A, 5 categories | ☐ | |
| 7 | Knowledge Base — Glossary | 87 thuật ngữ, 7 categories | ☐ | |
| 8 | Tài liệu kiến trúc | docs/architecture/ | ☐ | |
| 9 | Tài liệu triển khai | docs/deployment/ | ☐ | |
| 10 | Tài liệu đánh giá | docs/evaluation/ (benchmark, test scenarios) | ☐ | |
| 11 | Hướng dẫn quản trị | docs/guides/admin-guide.md | ☐ | Tiếng Việt |
| 12 | Hướng dẫn correction | docs/guides/correction-learning.md | ☐ | |
| 13 | Hướng dẫn migration | docs/guides/migration-guide.md | ☐ | |
| 13a | Hướng dẫn quản trị nâng cao | docs/guides/admin-guide-advanced.md | ☐ | Cho nhân viên kỹ thuật |
| 13b | Kế hoạch phục hồi sự cố | docs/guides/disaster-recovery.md | ☐ | |
| 13c | Tài liệu API (OpenAPI spec) | backend/openapi.yaml | ☐ | Chuẩn OpenAPI 3.0.3, import được vào Postman/Swagger |
| 13d | Hướng dẫn sử dụng API | docs/api/api-guide.md | ☐ | Tiếng Việt, kèm examples curl/Python/JS |
| 13e | Báo cáo kiểm thử ingestion | docs/evaluation/ingestion-test-report.md | ☐ | Bằng chứng KPI "cập nhật không lỗi" |
| 13f | Runbook vận hành ingestion | docs/deployment/ingestion-runbook.md | ☐ | Checklist + error recovery |
| 14 | Dataset Card | docs/dataset-card.md | ☐ | Chuẩn Hugging Face |
| 15 | Yêu cầu nghiệp vụ | docs/product-requirements.md + .xlsx | ☐ | |
| 16 | Nhật ký thay đổi | docs/changelog.md | ☐ | |
| 17 | Biên bản bàn giao | docs/handover/handover-report.md | ☐ | Cần ký xác nhận |
| 18 | Thỏa thuận hỗ trợ (SLA) | docs/handover/sla.md | ☐ | Cần ký xác nhận |
| 19 | Script export data | backend/scripts/export_data.py | ☐ | |
| 19a | File cấu hình mẫu | backend/.env.example | ☐ | Template biến môi trường |
| 19b | Script test ingestion | backend/scripts/test_ingestion.py | ☐ | End-to-end verification, 12 checks |
| 20 | Access credentials | API keys (OpenAI, Supabase, LlamaCloud), VPS SSH | ☐ | Bàn giao trực tiếp |
| 21 | Buổi đào tạo | Theo outline docs/handover/training-outline.md | ☐ | 3-3.5 giờ |
| 22 | Biên bản ký xác nhận | Cả hai bên ký | ☐ | |

---

## Xác nhận bên giao

| | |
|---|---|
| **Ký tên** | _________________ |
| **Họ và tên** | _________________ |
| **Ngày** | ____/____/________ |

---

## Xác nhận bên nhận

| | |
|---|---|
| **Ký tên** | _________________ |
| **Họ và tên** | _________________ |
| **Ngày** | ____/____/________ |
