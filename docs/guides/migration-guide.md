# Hướng dẫn Migration LLM — WINDBOT AI Chatbot

> Tài liệu này hướng dẫn EPU/TAF cách chuyển đổi LLM backend nếu cần (giảm chi phí, data sovereignty, hoặc tự chủ hạ tầng).

---

## 1. Tại sao cần cân nhắc migration?

Hệ thống hiện tại sử dụng **OpenAI API** làm LLM backend. Điều này hoạt động tốt nhưng có một số điểm cần lưu ý:

- **Phụ thuộc OpenAI API**: chi phí tính theo usage (token), không cố định hàng tháng.
- **Chi phí ước tính**: khoảng **$5–20/tháng** cho mức sử dụng chatbot hiện tại (tùy lượng câu hỏi).
- **Data sovereignty**: mọi câu hỏi của người dùng được gửi qua OpenAI servers (ngoài Việt Nam). Nếu trường/tổ chức yêu cầu dữ liệu phải ở on-premise, đây là vấn đề.
- **Rủi ro vendor lock-in**: nếu OpenAI thay đổi pricing, discontinue model, hoặc thay đổi Terms of Service.

---

## 2. Tổng quan kiến trúc hiện tại

| Thành phần | Giá trị hiện tại |
|---|---|
| LLM | `gpt-4.1-mini` qua OpenAI API |
| Embedding | `text-embedding-3-small` (1536 dimensions) |
| Framework | LlamaIndex (hỗ trợ nhiều LLM backends) |
| Vector store | Supabase pgvector |
| Config file | `backend/app/config.py` — field `llm_model` |
| RAG service | `backend/app/services/rag.py` |

Nhờ sử dụng **LlamaIndex**, việc đổi LLM backend tương đối đơn giản vì framework đã abstract hóa lớp LLM.

---

## 3. Option 1: Đổi model OpenAI khác

**Đơn giản nhất** — chỉ cần thay đổi config, không cần sửa code.

### Models available

| Model | Chi phí (tương đối) | Chất lượng | Tốc độ |
|---|---|---|---|
| `gpt-4o` | Cao | Rất tốt | Nhanh |
| `gpt-4o-mini` | Thấp | Tốt | Rất nhanh |
| `gpt-4-turbo` | Cao | Rất tốt | Trung bình |
| `gpt-3.5-turbo` | Rất thấp | Trung bình | Rất nhanh |

### Steps

1. **Edit file `.env`:**

```bash
LLM_MODEL=gpt-4o
```

2. **Restart backend:**

```bash
systemctl restart botai-backend
```

3. **Test chatbot** — hỏi vài câu tiếng Việt về năng lượng gió để kiểm tra chất lượng.

> **Lưu ý:** Không cần re-ingest tài liệu vì embedding model không thay đổi.

---

## 4. Option 2: Self-hosted với Ollama (Khuyến nghị cho on-premise)

**Ollama** cho phép chạy LLM trên máy local/server. Miễn phí, không tốn API, dữ liệu hoàn toàn ở on-premise.

### Yêu cầu phần cứng

- **GPU (khuyến nghị):** NVIDIA với 8GB+ VRAM (ví dụ: RTX 3060, RTX 4060 trở lên)
- **CPU-only:** Có thể chạy được nhưng chậm hơn đáng kể
- **RAM:** Tối thiểu 16GB cho model 7-8B

### Steps

**Bước 1: Cài đặt Ollama**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Bước 2: Tải model**

```bash
# Model 8B — cân bằng tốt giữa chất lượng và tốc độ (~4.7GB)
ollama pull llama3.1:8b

# Model 70B — chất lượng tốt nhất, cần >48GB RAM
ollama pull llama3.1:70b

# Qwen 2.5 — hỗ trợ tiếng Việt tốt
ollama pull qwen2.5:7b
```

**Bước 3: Test model**

```bash
ollama run llama3.1:8b "What is a wind turbine?"
```

**Bước 4: Cài đặt LlamaIndex Ollama integration**

```bash
pip install llama-index-llms-ollama llama-index-embeddings-ollama
```

**Bước 5: Thêm config mới**

Trong `backend/app/config.py`, thêm các field:

```python
llm_provider: str = "ollama"  # "openai" or "ollama"
ollama_base_url: str = "http://localhost:11434"
ollama_model: str = "llama3.1:8b"
```

**Bước 6: Sửa code khởi tạo LLM**

Trong `backend/app/services/rag.py`, thay đổi phần khởi tạo LLM:

```python
if settings.llm_provider == "ollama":
    from llama_index.llms.ollama import Ollama
    llm = Ollama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.1
    )
else:
    llm = OpenAI(model=settings.llm_model, temperature=0.1)
```

**Bước 7: (Tùy chọn) Đổi embedding model sang Ollama**

```python
from llama_index.embeddings.ollama import OllamaEmbedding

embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434"
)
```

> **QUAN TRONG:** Nếu đổi embedding model, embedding dimensions sẽ khác (không còn 1536). Bạn **PHẢI re-ingest toàn bộ tài liệu** vào vector store. Xem thêm mục "Lưu ý quan trọng" bên dưới.

**Bước 8: Restart và test**

```bash
systemctl restart botai-backend
```

---

## 5. Option 3: vLLM (Production-scale self-hosted)

**vLLM** phù hợp cho production với traffic cao. Ưu điểm chính:

- Throughput cao hơn Ollama
- Cung cấp **OpenAI-compatible API** — gần như drop-in replacement, không cần sửa nhiều code

### Yêu cầu

- **GPU bắt buộc** (NVIDIA, CUDA support)
- RAM và VRAM phù hợp với model size

### Steps

**Bước 1: Cài đặt vLLM**

```bash
pip install vllm
```

**Bước 2: Khởi chạy API server**

```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --port 8001
```

**Bước 3: Cấu hình `.env`**

Vì vLLM cung cấp OpenAI-compatible API, chỉ cần trỏ OpenAI client sang vLLM server:

```bash
OPENAI_API_BASE=http://localhost:8001/v1
OPENAI_API_KEY=dummy
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**Bước 4: Restart backend**

```bash
systemctl restart botai-backend
```

> **Ưu điểm lớn:** Không cần sửa code backend vì vLLM tương thích API format của OpenAI.

---

## 6. So sánh các option

| Tiêu chí | OpenAI API | Ollama | vLLM |
|---|---|---|---|
| Chi phí | $5–20/tháng | Free (+ điện/server) | Free (+ điện/server) |
| Chất lượng | Tốt nhất | Tốt (llama3.1 70b) | Tốt (llama3.1 70b) |
| Tốc độ | Nhanh | Trung bình | Nhanh |
| Data sovereignty | Không | Có | Có |
| Setup difficulty | Dễ nhất | Trung bình | Khó hơn |
| GPU cần | Không | Khuyến nghị | Bắt buộc |
| Maintenance | Không | Cần update model | Cần update model |

---

## 7. Lưu ý quan trọng

1. **Đổi embedding model = PHẢI re-ingest tài liệu.** Mỗi embedding model tạo vectors với dimensions khác nhau (ví dụ: OpenAI `text-embedding-3-small` = 1536 dims, `nomic-embed-text` = 768 dims). Vectors cũ và mới không tương thích.

2. **Test kỹ chất lượng** sau khi migration. Hỏi ít nhất 20-30 câu hỏi tiếng Việt về năng lượng gió và so sánh chất lượng trả lời.

3. **Backup data trước khi migration:**
   ```bash
   # Backup Supabase database
   pg_dump -h <supabase-host> -U postgres -d postgres > backup_before_migration.sql
   ```

4. **System prompt có thể cần điều chỉnh.** Mỗi model có behavior khác nhau — prompt hoạt động tốt với GPT-4 có thể cần tinh chỉnh cho Llama 3.1.

5. **Chất lượng tiếng Việt khác nhau tùy model.** Luôn test với câu hỏi tiếng Việt:
   - "Tuabin gió hoạt động như thế nào?"
   - "Bảo trì tuabin gió cần những gì?"
   - "Năng lượng gió ở Việt Nam phát triển ra sao?"

---

## 8. Khuyến nghị

| Giai đoạn | Khuyến nghị | Lý do |
|---|---|---|
| **Ngắn hạn** | Giữ OpenAI API | Ổn định, chất lượng tốt nhất, chi phí chấp nhận được |
| **Trung hạn** | Thử Ollama + `llama3.1:8b` trên server phụ | Đánh giá chất lượng và khả năng self-host trước khi commit |
| **Dài hạn** | Nếu quyết định self-host, dùng vLLM cho production | Throughput tốt, OpenAI-compatible API dễ chuyển đổi |

> **Tóm lại:** Không cần vội migration nếu chi phí OpenAI API vẫn chấp nhận được. Nhưng nên thử nghiệm Ollama song song để có phương án dự phòng khi cần.
