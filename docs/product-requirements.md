# TÀI LIỆU MÔ TẢ NGHIỆP VỤ SẢN PHẨM — AI CHATBOT TUA-BIN GIÓ (WINDBOT)

**Dự án:** Qualcomm VR Lab | **Phiên bản:** 2.1 | **Ngày cập nhật:** 06/04/2026 | **Trạng thái:** ✅ Đã đáp ứng | ⚠️ Một phần | ❌ Chưa có

---

## Tài liệu nghiệp vụ

### A) PHÂN TÍCH YÊU CẦU

#### 1. Thu thập và chuẩn hóa tài liệu kỹ thuật tua-bin gió (FAQs, sơ đồ, linh kiện, quy trình vận hành/bảo trì, v.v.)

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Hệ thống ingestion tài liệu đã hoàn chỉnh — hỗ trợ định dạng PDF, DOCX, PPTX, XLSX, TXT, MD, CSV thông qua LlamaParse (OCR Tiếng Anh + Tiếng Việt) và SimpleDirectoryReader. Metadata tài liệu được lưu vào bảng documents_metadata trên Supabase. Đã nạp 5 file PDF tài liệu kỹ thuật tua-bin gió (25 chunks) vào vector store. Đã generate và nạp 150 cặp Q&A (30 pairs x 5 categories: structure, operations, maintenance, safety, troubleshooting).

Còn thiếu: Bộ dataset hiện tại vẫn hạn chế (25 chunks + 150 Q&A). Cần thêm tài liệu thực tế từ EPU/TAF (FAQs chi tiết, sơ đồ kỹ thuật gốc, hướng dẫn vận hành cụ thể theo model).

Cần làm: Thu thập thêm tài liệu từ EPU/TAF, chuẩn hóa định dạng, nạp vào hệ thống qua pipeline ingest_docs.py.

**Ghi chú:** Phụ thuộc vào nguồn tài liệu từ đối tác EPU/TAF cung cấp. Hạ tầng kỹ thuật đã sẵn sàng tiếp nhận.

---

#### 2. Xác định các kịch bản Q&A chính và phân tích nội dung đào tạo liên quan đến tua-bin gió: cấu trúc, linh kiện, vận hành, bảo trì, an toàn, xử lý sự cố

**Giải pháp / Thực trạng:** ✅ Đã đáp ứng

Thực trạng: Đã xây dựng hoàn chỉnh:
- System prompt chuyên biệt cho domain tua-bin gió (backend/app/prompts/system.py), hỗ trợ song ngữ Việt-Anh với 12 quy tắc (scope restriction, information hierarchy, entity verification, correction handling, anti-fabrication, language matching...).
- Q&A corpus 150 cặp phân loại theo 5 chủ đề (structure, operations, maintenance, safety, troubleshooting), đã nạp vào vector store.
- Benchmark 160 câu hỏi (benchmark-windbot-v1.md) để đánh giá chất lượng RAG.
- Bộ test tự động 46 test cases (test-scenarios-windbot-v1.md) đạt **85% pass rate** (37/46) qua 3 vòng cải tiến.
- Tính năng gợi ý 3 câu hỏi tiếp theo (follow-up suggestions) đã hoạt động, relevant, <80 ký tự.

**Ghi chú:** Nên phối hợp với chuyên gia vận hành tua-bin gió của EPU/TAF để mở rộng Q&A corpus với nội dung thực tế hơn.

---

#### 3. Đánh giá khả năng tích hợp chatbot với Web và VR360

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Tích hợp Web đã hoàn chỉnh — Next.js 16 frontend với streaming SSE, responsive design, dark/light mode. API backend FastAPI đã mở (OpenAPI docs tại /docs). CORS đã cấu hình whitelist. Đã deploy production: Frontend trên Vercel (https://windbot.vercel.app), Backend trên VPS (62.146.236.156:8000) với Gunicorn + systemd.

Còn thiếu: Chưa có đánh giá kỹ thuật chính thức và POC (Proof of Concept) cho VR360. Chưa có tài liệu phân tích feasibility VR.

Cần làm: Lập báo cáo đánh giá tích hợp VR360, thử nghiệm WebXR API / A-Frame với headset Meta Quest hoặc Pico.

**Ghi chú:** Web integration: HOÀN CHỈNH và LIVE. VR360: cần nghiên cứu thêm — đề xuất dùng WebXR API (browser-based, không cần cài app riêng).

---

### B) THIẾT KẾ & PHÁT TRIỂN CHATBOT

#### 4. Xây dựng AI chatbot sử dụng công nghệ NLP để hiểu và phản hồi tự nhiên bằng Tiếng Việt và Tiếng Anh

**Giải pháp / Thực trạng:** ✅ Đã đáp ứng

Thực trạng: Đã đáp ứng đầy đủ — GPT-4o-mini (OpenAI) làm LLM chính với system prompt song ngữ Việt-Anh chuyên biệt cho domain tua-bin gió. Chat history được duy trì trong session với memory buffer 8000 tokens (40 messages). Sử dụng condense_plus_context mode để tự động condense follow-up queries thành standalone questions trước khi retrieval.

Các tính năng NLP đã có:
- RAG (Retrieval-Augmented Generation) với Supabase pgvector, top_k=15, similarity_cutoff=0.15
- **Query condensing tự động** (condense_plus_context mode) — follow-up ngắn/mơ hồ như "có thể có 4 ko?" được reformulate thành "Tua-bin gió có thể có 4 cánh quạt không?" trước khi retrieval
- Streaming response qua SSE (token-by-token)
- Follow-up suggestions (3 câu hỏi gợi ý)
- Correction detection + extraction + system prompt injection (regex detect → LLM extract → metadata cache → inject)
- CorrectionOverridePostprocessor (mark conflicting KB chunks khi user correction tồn tại)
- Language detection tự động (detect_input_language → [RESPOND IN] hint)
- Entity verification với FIRST/THEN/FINALLY sequence (chống fabrication cho specific models)
- **Information hierarchy 4 tầng**: User corrections → Knowledge base → General knowledge fallback (kèm disclaimer) → Từ chối (specific entity không có trong KB)
- **Attribution phân biệt nguồn**: KB → "theo tài liệu chuyên ngành", user corrections → "theo thông tin bạn đã xác nhận", general knowledge → "theo kiến thức chung"
- Temperature 0.1 cho consistency cao

Kết quả test v3: **37/46 (85%)** — Consistency 100%, Bilingual 100%, Suggestions 100%, Q&A 100%, Scope 100%.

Cải tiến v2.1 (06/04/2026): Fix follow-up context loss, general knowledge fallback, entity verification strengthening — đã verify qua dữ liệu người dùng thực trên Supabase.

**Ghi chú:** Sử dụng GPT-4o-mini qua OpenAI API commercial. Query condensing thêm 1 LLM call nhẹ (~$0.0001/request) cho mỗi tin nhắn có history.

---

#### 5. Xây dựng kho kiến thức chuyên biệt về tua-bin gió (thuật ngữ, quy trình, sơ đồ kỹ thuật)

**Giải pháp / Thực trạng:** ✅ Đã đáp ứng

Thực trạng: Kho kiến thức đã xây dựng và đang hoạt động:
- Supabase pgvector (1536 chiều, text-embedding-3-small), collection 'wind_turbine_docs'
- 25 chunks từ 5 file PDF tài liệu kỹ thuật + 150 chunks Q&A corpus (5 categories x 30 pairs)
- Glossary thuật ngữ tua-bin gió Việt-Anh: **87 thuật ngữ**, 7 categories (Structure 15, Components 15, Maintenance 15, Operations 12, Troubleshooting 12, General 9, Safety 9)
- Hỗ trợ render sơ đồ Mermaid tương tác (zoom/pan/drag) và công thức LaTeX/KaTeX trong giao diện
- API endpoint GET /api/glossary cho tra cứu thuật ngữ

**Ghi chú:** Chunk size: 1024 tokens, overlap: 200. Thay đổi chunk size nếu tài liệu kỹ thuật có cấu trúc đặc biệt (bảng, sơ đồ dày đặc).

---

#### 6. Thiết kế giao diện thân thiện, tương thích với web, app và VR

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Giao diện web đã hoàn chỉnh và thân thiện — Next.js 16 + Tailwind CSS 4, responsive mobile-first, dark/light mode, Markdown/LaTeX/Mermaid rendering, loading indicators, copy button, auto-scroll, follow-up suggestions. Deploy trên Vercel (https://windbot.vercel.app). Hiểu được typo và câu hỏi không dấu.

Còn thiếu: Chưa có native mobile app (iOS/Android). Chưa có VR interface. Chưa có Progressive Web App (PWA) manifest.

Cần làm: (1) Thêm PWA manifest để cài web app trên mobile. (2) Phát triển VR UI overlay cho Meta Quest/Pico. (3) Tùy chọn: React Native app nếu cần native experience.

**Ghi chú:** Ưu tiên PWA trước (ít tốn công nhất, dùng được trên cả iOS/Android). Native app và VR UI là giai đoạn tiếp theo.

---

### C) QUẢN LÝ DỮ LIỆU VÀ BẢO MẬT

#### 7. Phát triển chiến lược dữ liệu: thu thập, chuẩn hóa, gán nhãn và cập nhật kiến thức tua-bin gió

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Pipeline ingestion có metadata labeling tự động (filename, file_type, language, num_chunks, ingested_at). Script ingest_docs.py hỗ trợ batch processing theo thư mục. Hỗ trợ 3 tier ingestion (cost_effective, agentic, agentic_plus). Script generate_qa_corpus.py tự động generate Q&A theo category. Script evaluate_rag.py benchmark chất lượng RAG. Đã có labeling category cho Q&A corpus (structure, operations, maintenance, safety, troubleshooting).

Còn thiếu: Chưa có tài liệu chiến lược dữ liệu chính thức. Chưa có quy trình data governance (ai được phép nạp, review, xóa tài liệu).

Cần làm: Viết Data Strategy Document; xây dựng quy trình review tài liệu trước khi nạp.

**Ghi chú:** Nên định nghĩa taxonomy chủ đề (ontology) trước khi nạp tài liệu hàng loạt để đảm bảo nhất quán.

---

#### 8. Xây dựng Dataset Card (nguồn, cấu trúc, quy trình xử lý)

**Giải pháp / Thực trạng:** ✅ Đã đáp ứng

Thực trạng: Đã có file dataset_card.md theo chuẩn Hugging Face với đầy đủ thông tin: nguồn gốc, cấu trúc, quy trình xử lý, thống kê. Bảng documents_metadata trên Supabase tracking filename, file_type, language, num_chunks, ingested_at. Script update_dataset_card.py tự động cập nhật khi nạp batch mới.

**Ghi chú:** Cập nhật dataset_card.md mỗi lần nạp batch tài liệu mới.

---

#### 9. Giao tiếp bảo mật qua HTTPS/TLS

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Frontend deploy trên Vercel — HTTPS/TLS được cấu hình tự động và miễn phí. CORS trong FastAPI đã whitelist URL frontend cụ thể (không dùng wildcard *). Supabase connection sử dụng HTTPS mặc định.

Còn thiếu: Backend API server trên VPS hiện chạy HTTP (port 8000) không qua reverse proxy. Chưa có HSTS headers. Chưa có certificate pinning.

Cần làm: Đặt FastAPI backend sau Nginx/Caddy với SSL termination; thêm HSTS header; document quy trình renew certificate.

**Ghi chú:** Khi deploy production: dùng Nginx + Let's Encrypt (Certbot) hoặc Caddy (tự động HTTPS) làm reverse proxy cho FastAPI backend.

---

#### 10. Thiết lập quy trình cập nhật và kiểm soát versioning dữ liệu

**Giải pháp / Thực trạng:** ❌ Chưa có

Thực trạng: Hiện tại không có cơ chế versioning cho knowledge base. Tài liệu được nạp một chiều (append-only). Không có khả năng rollback, so sánh phiên bản, hoặc track thay đổi theo thời gian.

Còn thiếu: Version tracking cho document collections, rollback support, changelog, audit log của các lần cập nhật.

Cần làm: Thêm trường version và replaced_by vào documents_metadata; xây dựng API endpoint để update/deprecate tài liệu; tạo bảng ingestion_log ghi lại lịch sử thay đổi.

**Ghi chú:** Có thể dùng DVC (Data Version Control) cho file-level versioning hoặc tự build lightweight versioning trong Supabase.

---

#### 11. Đảm bảo quyền sở hữu dữ liệu thuộc về EPU/TAF

**Giải pháp / Thực trạng:** ❌ Chưa có

Thực trạng: Dữ liệu hiện lưu trên Supabase cloud (do nhóm phát triển quản lý). Chưa có cơ chế kỹ thuật hay pháp lý nào đảm bảo quyền sở hữu dữ liệu cho EPU/TAF.

Còn thiếu: Thỏa thuận pháp lý về data ownership (DPA — Data Processing Agreement). Hạ tầng self-hosted hoặc data residency tại Việt Nam. Cơ chế export/migration dữ liệu cho EPU/TAF.

Cần làm: Ký DPA với EPU/TAF; xem xét self-host Supabase hoặc dùng hosting Việt Nam; cung cấp API export toàn bộ dữ liệu cho EPU/TAF.

**Ghi chú:** Đây là yêu cầu pháp lý/hợp đồng, không chỉ kỹ thuật. Cần tư vấn pháp lý và thảo luận với EPU/TAF về hosting location.

---

#### 12. Tuân thủ bảo mật: mã hóa dữ liệu (HTTPS/TLS), ISO 27001 hoặc tương đương

**Giải pháp / Thực trạng:** ❌ Chưa có

Thực trạng: HTTPS/TLS cơ bản đã có (xem yêu cầu #9). Tuy nhiên chưa đáp ứng tiêu chuẩn toàn diện: chưa có authentication/authorization (không có login), chưa có audit log, chưa có rate limiting, chưa có input validation chống injection.

Còn thiếu: User authentication (JWT/OAuth2), role-based access control, audit log đầy đủ, penetration testing, security policy document, ISO 27001 gap analysis.

Cần làm: (1) Thêm auth layer (JWT hoặc Supabase Auth). (2) Rate limiting trên API. (3) Input sanitization. (4) Thuê đơn vị audit bảo mật. (5) Lập roadmap ISO 27001.

**Ghi chú:** ISO 27001 certification là quá trình dài (6–18 tháng). Trước mắt: implement các security controls cơ bản, sau đó có thể hướng đến SOC 2 Type II hoặc ISO 27001.

---

### D) TÍCH HỢP HỆ THỐNG

#### 13. Tích hợp chatbot với Web và VR360 (Meta Quest, Pico)

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Tích hợp Web hoàn chỉnh và LIVE — Next.js frontend giao tiếp với FastAPI backend qua SSE streaming, API proxy đã cấu hình trong next.config.ts. Deploy Vercel (https://windbot.vercel.app) + VPS backend (62.146.236.156:8000) với Gunicorn 4 workers + systemd auto-restart.

Còn thiếu: VR360 integration chưa có. Chưa có SDK/bridge cho Meta Quest hoặc Pico.

Cần làm: (1) Đánh giá approach: WebXR API (browser-based, dễ nhất) vs Unity XR SDK (native performance tốt hơn) vs A-Frame (declarative HTML-like). (2) Xây dựng POC VR scene với wind turbine model. (3) Nhúng chatbot UI dưới dạng VR overlay panel.

**Ghi chú:** Đề xuất approach: WebXR API + Three.js cho web-based VR — chạy được trên trình duyệt Meta Quest và Pico mà không cần cài app riêng.

---

#### 14. Chatbot có khả năng nhận biết ngữ cảnh trong VR (sinh viên chọn linh kiện → chatbot giải thích)

**Giải pháp / Thực trạng:** ❌ Chưa có

Thực trạng: Chưa có VR scene và chưa có cơ chế context awareness từ VR. Backend chat API có hỗ trợ metadata trong request nhưng chưa được dùng cho VR context.

Còn thiếu: VR scene với 3D wind turbine model có interactive components. Event system để khi người dùng click/chọn linh kiện → gửi context đến chatbot. Context injection vào chat session.

Cần làm: Thiết kế event schema (component_id, component_name, action) → gửi qua REST API kèm chat message; backend xử lý context injection vào RAG query; VR frontend gửi event khi chọn linh kiện.

**Ghi chú:** Đây là tính năng differentiator quan trọng nhất của dự án. Cần thiết kế API schema cẩn thận để VR engine và chatbot backend giao tiếp hiệu quả.

---

#### 15. Đảm bảo hiệu năng: FPS ≥72Hz, VR latency ≤0.5s

**Giải pháp / Thực trạng:** ❌ Chưa có

Thực trạng: VR chưa được implement nên không thể đo FPS và VR latency. Web chat latency hiện tại: ~1–3s đến first token (phụ thuộc OpenAI API). Streaming SSE giảm perceived latency cho người dùng.

Còn thiếu: VR rendering engine chưa có. Chưa có benchmark FPS. Chưa có optimization cho VR latency.

Cần làm: Sau khi có VR POC, đo baseline FPS và latency; optimize: (1) Pre-render VR scene assets. (2) Cache common chatbot responses. (3) Edge deployment cho backend gần user. (4) Websocket thay SSE để giảm latency.

**Ghi chú:** FPS ≥72Hz là yêu cầu của VR rendering engine (Three.js/Unity), độc lập với chatbot. VR latency ≤0.5s cho chatbot response rất thách thức — cần cache và streaming response.

---

#### 16. API/SDK mở để thuận tiện mở rộng và nâng cấp

**Giải pháp / Thực trạng:** ✅ Đã đáp ứng

Thực trạng: FastAPI tự động sinh OpenAPI 3.0 documentation tại /docs (Swagger UI) và /redoc (ReDoc). Các endpoint hiện có:
- POST /api/chat (streaming SSE)
- POST /api/chat/sessions (tạo session)
- GET /api/chat/sessions/{id}/messages (lịch sử chat)
- POST /api/ingest (nạp tài liệu)
- GET /api/glossary (tra cứu thuật ngữ)
- GET /api/glossary/{term_id} (chi tiết thuật ngữ)
- GET /api/health (health check)

Đã đáp ứng: API design RESTful, JSON request/response chuẩn, SSE cho streaming, CORS cấu hình đúng.

Nâng cấp thêm: Thêm API versioning (/api/v1/...) để backward compatibility khi nâng cấp. Thêm API key authentication. Tạo SDK client wrapper cho TypeScript/Python.

**Ghi chú:** API versioning nên implement sớm trước khi có bên thứ 3 tích hợp, tránh breaking changes sau này.

---

### E) ĐÀO TẠO VÀ HỖ TRỢ

#### 17. Cung cấp tài liệu kỹ thuật (kiến trúc hệ thống, API, cài đặt, triển khai, hướng dẫn sử dụng) và hướng dẫn cho đội quản lý EPU/TAF

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Đã có:
- README.md (tổng quan kỹ thuật, setup instructions, tech stack)
- deploy-guide.md (hướng dẫn deploy VPS + Vercel chi tiết)
- deploy/DEPLOYMENT_LOG.md (nhật ký triển khai, issues & solutions)
- supabase_schema.sql (setup database)
- dataset_card.md (mô tả dataset theo chuẩn Hugging Face)
- Chatbot_correction_learning_guide.md (hướng dẫn hệ thống correction)
- test-scenarios-windbot-v1.md (46 test cases với kết quả 3 vòng)
- benchmark-windbot-v1.md (160 câu benchmark)

Còn thiếu: Tài liệu API chi tiết cho EPU/TAF (không phải dev docs). Hướng dẫn admin (thêm tài liệu, quản lý session). Video tutorial. Hướng dẫn vận hành hệ thống hàng ngày.

Cần làm: Viết Admin Guide (Tiếng Việt) hướng dẫn EPU/TAF quản lý chatbot; tạo video walkthrough; tổ chức buổi training hands-on.

**Ghi chú:** Tài liệu cho EPU/TAF nên dùng ngôn ngữ phi-kỹ thuật, tập trung vào workflow hàng ngày (thêm tài liệu mới, xem lịch sử chat, xử lý lỗi thường gặp).

---

#### 18. Bàn giao AI model, dataset và training pipeline (nếu có)

**Giải pháp / Thực trạng:** ⚠️ Một phần

Thực trạng: Dự án sử dụng OpenAI GPT-4o-mini qua commercial API (không có model fine-tuned riêng). Dataset ingestion pipeline đã có (ingest_docs.py với LlamaParse). Vector embeddings lưu trong Supabase pgvector. Có scripts: generate_qa_corpus.py, evaluate_rag.py, seed_glossary.py, convert_benchmark_md_to_json.py.

Còn thiếu: Chưa có gói bàn giao chính thức. Chưa export được vector embeddings hiện tại. Chưa có hướng dẫn migrate sang model khác nếu EPU/TAF muốn dùng open-source LLM.

Cần làm: Tạo gói bàn giao gồm: (1) Source code toàn bộ. (2) Export dataset đã ingestion (documents + embeddings). (3) Hướng dẫn cấu hình API keys. (4) Script backup/restore Supabase. (5) Tùy chọn: migrate sang Ollama/vLLM nếu cần on-premise.

**Ghi chú:** Vì dùng OpenAI API, EPU/TAF cần account OpenAI và API key riêng khi tiếp nhận vận hành. Nên cân nhắc option self-hosted LLM (Ollama + Llama 3) để tránh phụ thuộc vendor.

---

#### 19. Hỗ trợ sau triển khai ít nhất 3 tháng, bao gồm sửa lỗi và cập nhật nhỏ

**Giải pháp / Thực trạng:** ❌ Chưa có

Thực trạng: Không có điều khoản hỗ trợ sau triển khai trong codebase (đây là thỏa thuận hợp đồng/dịch vụ, không phải phần mềm).

Còn thiếu: SLA document (Service Level Agreement). Kênh tiếp nhận lỗi (issue tracker, email, hotline). Quy trình xử lý bug report. Lịch cập nhật định kỳ. Monitoring và alerting hệ thống.

Cần làm: (1) Ký phụ lục hợp đồng hỗ trợ 3 tháng với SLA cụ thể. (2) Setup GitHub Issues hoặc Jira cho bug tracking. (3) Cài monitoring (Sentry cho frontend, Loguru/Datadog cho backend). (4) Lịch cập nhật hàng tháng.

**Ghi chú:** Nên định nghĩa SLA rõ ràng: thời gian phản hồi (ví dụ: critical bug ≤4h, normal bug ≤2 ngày làm việc). Đề xuất setup Sentry.io miễn phí cho error tracking tự động.

---

## Chú giải

| Màu nền | Trạng thái | Ý nghĩa |
|---|---|---|
| Xanh lá nhạt | ✅ Đã đáp ứng | Yêu cầu đã được implement đầy đủ trong dự án hiện tại |
| Vàng nhạt | ⚠️ Một phần | Yêu cầu đã implement một phần, còn thiếu hoặc cần bổ sung |
| Đỏ nhạt | ❌ Chưa có | Yêu cầu chưa được implement, cần phát triển từ đầu |

---

## Tổng kết mức độ đáp ứng yêu cầu

| Trạng thái | Số yêu cầu | Tỷ lệ | v1.0 (10/03) | v2.0 (24/03) | v2.1 (06/04) | Thay đổi |
|---|---|---|---|---|---|---|
| ✅ Đã đáp ứng | 5 | 26% | 2 (11%) | 5 (26%) | 5 (26%) | — |
| ⚠️ Một phần | 8 | 42% | 10 (53%) | 8 (42%) | 8 (42%) | — |
| ❌ Chưa có | 6 | 32% | 7 (37%) | 6 (32%) | 6 (32%) | — |
| **TỔNG CỘNG** | **19** | **100%** | | | | |

### Thay đổi so với v1.0:
- **#2 (Q&A kịch bản):** ⚠️ → ✅ — Đã có Q&A corpus 150 pairs, benchmark 160 câu, test suite 46 cases (85% pass)
- **#5 (Kho kiến thức):** ⚠️ → ✅ — Đã nạp 25 chunks + 150 Q&A + 87 glossary terms, đang hoạt động live
- **#8 (Dataset Card):** ❌ → ✅ — Đã có dataset_card.md theo chuẩn Hugging Face

### Cải tiến kỹ thuật chính (v1.0 → v2.0):
- Hệ thống correction detection + extraction + system prompt injection
- CorrectionOverridePostprocessor (override KB khi user correction xung đột)
- Entity verification FIRST/THEN/FINALLY (chống fabrication)
- Language detection tự động (EN/VI response matching)
- Scope restriction + continuation phrase exceptions
- Test pass rate: **73% → 85%** (3 vòng cải tiến)

### Cải tiến kỹ thuật chính (v2.0 → v2.1, 06/04/2026):
- **Query condensing**: Chuyển từ `context` mode sang `condense_plus_context` mode — tự động reformulate follow-up queries mơ hồ (VD: "có thể có 4 ko?" → "Tua-bin gió có thể có 4 cánh quạt không?") trước khi retrieval
- **Fix chat history loading**: History không được load vào engine memory do bug `dict.get(key, [])` — fix bằng cách truyền history qua `ChatMemoryBuffer.from_defaults(chat_history=...)`
- **General knowledge fallback**: Cho phép trả lời từ kiến thức chung với disclaimer khi KB không có thông tin về khái niệm chung (thay vì từ chối hoàn toàn)
- **Entity verification strengthening**: Kiểm tra specific entity/model TRƯỚC general fallback — ngăn LLM bịa specs cho model cụ thể (VD: Vestas V236)
- **Attribution phân biệt nguồn**: "theo tài liệu chuyên ngành" (KB), "theo thông tin bạn đã xác nhận" (user corrections), "theo kiến thức chung" (fallback)
- Đã verify qua dữ liệu người dùng thực trên Supabase (6 test scenarios pass)

---

## Đánh giá chất lượng chatbot (Test v3 — 24/03/2026)

| Category | Tests | Pass Rate | Ghi chú |
|---|---|---|---|
| Knowledge Base Q&A | 8 | **100%** | LaTeX, Mermaid, bilingual đều hoạt động |
| Correction Retention | 8 | **88%** | Single correction ✅, override KB ✅, multi-correction ⚠️ |
| Scope Restriction | 6 | **100%** | Từ chối ngoài phạm vi + chấp nhận biên giới phạm vi |
| Information Hierarchy | 6 | **50%** | Anti-fabrication hoạt động, correction persistence cần cải thiện |
| Consistency | 4 | **100%** | Câu trả lời gần identical qua nhiều session |
| Bilingual Support | 4 | **100%** | EN input → EN response, VI input → VI response |
| Follow-up Suggestions | 4 | **100%** | 3 suggestions, relevant, <80 chars |
| Multi-turn & Edge Cases | 6 | **83%** | Hiểu typo, không dấu, continuation phrases |
| **TỔNG** | **46** | **85%** | **Target ≥85% — ĐẠT** |

## Kiểm tra thực tế v2.1 (06/04/2026) — Dữ liệu người dùng thực từ Supabase

| Test Case | Input | Kết quả | Status |
|---|---|---|---|
| Follow-up context | "turbine có mấy cánh" → "có thể có 4 ko?" | Hiểu context, trả lời đúng về 4 cánh quạt | ✅ |
| Follow-up "còn loại nào khác?" | "pitch control là gì?" → "còn loại nào khác?" | Trả lời về stall control | ✅ |
| Follow-up "còn cut-out thì sao?" | "tốc độ gió cut-in bao nhiêu?" → "còn cut-out thì sao?" | Trả lời chi tiết về cut-out 25 m/s | ✅ |
| Câu rất ngắn "tại sao?" | Sau câu trả lời về cut-out | Giải thích lý do bảo vệ tua-bin | ✅ |
| Câu rất ngắn "chi tiết hơn" | Sau câu trả lời trước | Mở rộng 4 điểm chi tiết | ✅ |
| General knowledge fallback | "tuabin gió có ảnh hưởng đến chim không?" | Trả lời đầy đủ, không từ chối | ✅ |
| Entity verification | "Vestas V236 có thông số kỹ thuật gì?" | "Thông tin cụ thể về Vestas V236 chưa có trong cơ sở tri thức hiện tại" | ✅ |
