# Giải pháp Retrieval cho WindBot: Sửa đúng 2 Failure Modes

> **Bối cảnh:** 11 file tài liệu Đại học Điện lực, pgvector, CPU-only 8GB RAM, Gemma 4 E2B Q4
> **Vấn đề gốc:** Retrieval không tìm đúng chunk → LLM trả lời sai dù đã có đúng thông tin trong corpus

---

## Chẩn đoán: 2 Failure Modes cụ thể

### Failure 1: Vocabulary Mismatch
Query dùng từ khác với document — cả trong cùng tiếng Việt lẫn cross-lingual.

| Query | Chunk tìm thấy | Chunk bị bỏ sót | Nguyên nhân |
|-------|----------------|-----------------|-------------|
| "hệ thống phanh" | "hệ thống thắng" | "aerodynamic brake (pitch to feather)" | Synonym VN + thuật ngữ EN |

**Tại sao xảy ra:**
- Embedding model (dù multilingual) encode "phanh" và "thắng" vào vùng vector gần nhau → tìm thấy
- Nhưng "pitch to feather" / "aerodynamic brake" ở vùng vector xa → bị bỏ sót
- BM25 thuần túy cũng bỏ sót vì không có keyword "phanh" hay "thắng" trong chunk tiếng Anh

### Failure 2: Concept Gap
Query hỏi component A, nhưng câu trả lời nằm trong mô tả nguyên lý vật lý liên quan đến A.

| Query | Chunk tìm thấy | Chunk bị bỏ sót | Nguyên nhân |
|-------|----------------|-----------------|-------------|
| "hộp số" | "tốc độ quay rotor" | "momen xoắn tỷ lệ nghịch với tốc độ" | Concept liên quan nhưng vocabulary khác |

**Tại sao xảy ra:**
- Embedding "hộp số" gần "tốc độ quay" (cùng ngữ cảnh cơ khí)
- Nhưng "momen xoắn tỷ lệ nghịch" là một nguyên lý vật lý — embedding xa "hộp số" dù khái niệm liên quan chặt

---

## Giải pháp: 5 tầng, triển khai tuần tự

> **Nguyên tắc:** Với chỉ 11 file, nhiều kỹ thuật "đắt" trở nên rất rẻ. Tận dụng điều này.

### Tầng 1: Contextual Chunking (Giải quyết cả 2 failure modes)

**Đây là giải pháp có ROI cao nhất cho bạn.** Kỹ thuật Contextual Retrieval của Anthropic, áp dụng cho 11 file.

**Ý tưởng:** Trước khi embedding, mỗi chunk được augment bằng LLM với ngữ cảnh giải thích từ toàn bộ document gốc.

**Trước:**
```
Chunk: "Hệ thống sử dụng pitch to feather để giảm tốc độ rotor khi gió mạnh quá mức."
```

**Sau khi contextual augment:**
```
Chunk: "[Ngữ cảnh: Đoạn này trích từ tài liệu về hệ thống phanh (braking system) 
của turbine gió. Pitch to feather là một loại phanh khí động học (aerodynamic brake), 
hoạt động bằng cách xoay cánh turbine để giảm lực nâng. Đây là một trong hai loại 
phanh chính cùng với phanh cơ học (mechanical brake/hệ thống thắng).]
Hệ thống sử dụng pitch to feather để giảm tốc độ rotor khi gió mạnh quá mức."
```

**Tại sao giải quyết cả 2 failure modes:**
- **Failure 1:** Chunk bây giờ chứa cả "phanh", "thắng", "brake", "aerodynamic brake", "pitch to feather" → embedding/BM25 match từ mọi biến thể query
- **Failure 2:** Chunk về "momen xoắn" sẽ được augment với context "liên quan đến hộp số, truyền động" → embedding gần "hộp số" hơn

**Triển khai cho WindBot:**

```python
import json
from openai import OpenAI  # hoặc Anthropic SDK

# Với 11 file, tổng ~vài trăm chunks — xử lý 1 lần offline
CONTEXT_PROMPT = """
<document>
{whole_document}
</document>

Đây là một chunk được trích từ document trên:
<chunk>
{chunk_text}
</chunk>

Hãy viết một đoạn ngữ cảnh ngắn (2-4 câu) bằng tiếng Việt để đặt chunk này 
vào bối cảnh của document. Bao gồm:
1. Chunk này thuộc phần/chương nào, nói về chủ đề gì
2. Các thuật ngữ đồng nghĩa (tiếng Việt lẫn tiếng Anh) cho khái niệm chính
3. Các khái niệm liên quan trực tiếp mà người dùng có thể hỏi khi muốn tìm chunk này

Chỉ trả lời đoạn ngữ cảnh, không giải thích thêm.
"""

def contextualize_chunk(whole_doc: str, chunk: str) -> str:
    """Thêm context cho 1 chunk. Chạy offline 1 lần."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Rẻ, đủ tốt cho task này
        messages=[{
            "role": "user", 
            "content": CONTEXT_PROMPT.format(
                whole_document=whole_doc, 
                chunk_text=chunk
            )
        }],
        max_tokens=200
    )
    context = response.choices[0].message.content
    return f"[Ngữ cảnh: {context}]\n{chunk}"
```

**Chi phí ước tính:** 11 file × ~50 chunks/file × ~1000 tokens/call = ~550K tokens ≈ **$0.08 với GPT-4o-mini**. Chạy 1 lần duy nhất.

---

### Tầng 2: Domain Synonym Dictionary (Giải quyết Failure 1)

Xây từ điển đồng nghĩa chuyên ngành điện gió. Với 11 file, làm thủ công + LLM hỗ trợ rất nhanh.

```python
WIND_TURBINE_SYNONYMS = {
    # Phanh
    "phanh": ["thắng", "brake", "braking system", "hệ thống phanh", 
              "hệ thống thắng", "hãm"],
    "phanh khí động học": ["aerodynamic brake", "pitch to feather", 
                           "feathering", "pitch brake"],
    "phanh cơ học": ["mechanical brake", "disc brake", "phanh đĩa", 
                     "caliper brake"],
    
    # Hộp số / Truyền động
    "hộp số": ["gearbox", "transmission", "bộ truyền động", "hộp tốc độ",
               "bộ tăng tốc", "speed increaser"],
    "momen xoắn": ["torque", "moment xoắn", "lực xoắn", "mô-men"],
    "tỷ số truyền": ["gear ratio", "transmission ratio", "tỉ số truyền"],
    
    # Máy phát
    "máy phát": ["generator", "máy phát điện", "alternator"],
    "stator": ["stato", "phần tĩnh", "cuộn dây stator"],
    "rotor": ["rô-to", "phần quay", "rotor turbine"],
    
    # Cánh turbine
    "cánh": ["blade", "cánh turbine", "cánh quạt", "airfoil"],
    "góc pitch": ["pitch angle", "góc nghiêng cánh", "góc đặt cánh"],
    
    # Tháp / Kết cấu
    "tháp": ["tower", "trụ", "cột tháp"],
    "nacelle": ["vỏ máy", "cabin", "buồng máy", "gondola"],
    "hub": ["đầu trục", "moayơ", "bộ phận trung tâm"],
    
    # Điều khiển
    "SCADA": ["hệ thống giám sát", "supervisory control"],
    "yaw": ["xoay đầu", "xoay hướng gió", "yaw system", "hệ thống yaw"],
    
    # Điện
    "biến tần": ["inverter", "converter", "bộ biến đổi tần số"],
    "lưới điện": ["power grid", "grid", "hệ thống điện"],
}

def expand_query_with_synonyms(query: str, synonym_dict: dict) -> list[str]:
    """Mở rộng query với các từ đồng nghĩa domain-specific."""
    expanded_terms = set()
    query_lower = query.lower()
    
    for key, synonyms in synonym_dict.items():
        # Check cả key lẫn synonyms
        all_terms = [key] + synonyms
        for term in all_terms:
            if term.lower() in query_lower:
                expanded_terms.update(all_terms)
                break
    
    if not expanded_terms:
        return [query]
    
    # Tạo expanded queries
    expanded_queries = [query]  # Giữ query gốc
    synonym_string = " ".join(expanded_terms)
    expanded_queries.append(f"{query} {synonym_string}")
    
    return expanded_queries
```

**Cách build từ điển nhanh:**

```python
# Dùng LLM để extract synonym pairs từ 11 file (chạy 1 lần)
EXTRACT_PROMPT = """
Đọc tài liệu kỹ thuật về turbine gió dưới đây. 
Trích xuất TẤT CẢ các cặp thuật ngữ đồng nghĩa (tiếng Việt ↔ tiếng Anh, 
tiếng Việt ↔ tiếng Việt viết tắt/đầy đủ).

Format JSON:
{"thuật_ngữ_chính": ["đồng_nghĩa_1", "đồng_nghĩa_2", ...]}

Document:
{document_text}
"""
```

---

### Tầng 3: Multi-Query Retrieval (Giải quyết cả 2 failure modes)

Thay vì search 1 query, generate 3-5 biến thể rồi search tất cả, merge kết quả.

```python
MULTI_QUERY_PROMPT = """
Bạn là trợ lý chuyên về kỹ thuật turbine gió / điện gió.
Người dùng hỏi: "{query}"

Hãy viết 3 câu hỏi khác nhau để tìm kiếm tài liệu, mỗi câu tiếp cận 
từ một góc độ khác:
1. Câu hỏi dùng thuật ngữ đồng nghĩa (cả tiếng Việt lẫn Anh)
2. Câu hỏi về nguyên lý/cơ chế liên quan
3. Câu hỏi mở rộng về hệ thống chứa thành phần đó

Trả lời chỉ 3 câu hỏi, mỗi câu trên 1 dòng, không đánh số.
"""

# Ví dụ cho query "hệ thống phanh":
# → "Các loại brake và cơ chế thắng trong turbine gió"
# → "Pitch to feather và aerodynamic braking hoạt động thế nào"  
# → "Hệ thống an toàn và bảo vệ quá tốc trong wind turbine"

# Ví dụ cho query "hộp số":
# → "Gearbox, bộ truyền động và transmission trong turbine"
# → "Mối quan hệ giữa momen xoắn, tốc độ quay và tỷ số truyền"
# → "Truyền công suất từ rotor qua hộp số đến máy phát điện"
```

**Pipeline hoàn chỉnh:**

```python
async def multi_query_retrieve(query: str, top_k: int = 5) -> list[Chunk]:
    # 1. Generate multiple queries
    alt_queries = generate_alt_queries(query)  # 3 queries
    
    # 2. Expand mỗi query với synonym dict
    all_queries = []
    for q in [query] + alt_queries:
        all_queries.extend(expand_query_with_synonyms(q, WIND_TURBINE_SYNONYMS))
    
    # 3. Search tất cả queries (parallel)
    all_chunks = set()
    for q in all_queries:
        # Dense search
        dense_results = await vector_search(q, top_k=top_k)
        # BM25 search  
        bm25_results = await bm25_search(q, top_k=top_k)
        all_chunks.update(dense_results + bm25_results)
    
    # 4. Deduplicate + Rerank
    unique_chunks = deduplicate(all_chunks)
    reranked = rerank(query, unique_chunks, top_k=top_k)
    
    return reranked
```

---

### Tầng 4: Hybrid Search + Reranking (Tăng precision)

**Hybrid Search** kết hợp dense vector search (semantic) với BM25 (keyword). Áp dụng trực tiếp trên pgvector.

```sql
-- pgvector: Dense search
SELECT id, content, embedding <=> query_embedding AS distance
FROM chunks
ORDER BY distance
LIMIT 20;

-- pg_trgm hoặc tsvector: BM25-style keyword search
SELECT id, content, ts_rank(tsv, to_tsquery('vietnamese', 'hệ & thống & phanh')) AS rank
FROM chunks
WHERE tsv @@ to_tsquery('vietnamese', 'hệ & thống & phanh')
ORDER BY rank DESC
LIMIT 20;
```

**Reciprocal Rank Fusion (RRF) để merge:**

```python
def reciprocal_rank_fusion(
    dense_results: list, 
    sparse_results: list, 
    k: int = 60,
    dense_weight: float = 0.8,  # Ưu tiên semantic
    sparse_weight: float = 0.2   # Keyword bổ sung
) -> list:
    """Merge dense + sparse results bằng RRF."""
    scores = {}
    
    for rank, chunk in enumerate(dense_results):
        scores[chunk.id] = scores.get(chunk.id, 0) + \
            dense_weight * (1 / (k + rank + 1))
    
    for rank, chunk in enumerate(sparse_results):
        scores[chunk.id] = scores.get(chunk.id, 0) + \
            sparse_weight * (1 / (k + rank + 1))
    
    sorted_ids = sorted(scores, key=scores.get, reverse=True)
    return [get_chunk(id) for id in sorted_ids]
```

**Reranking (CPU-friendly):**

```python
# Option 1: FlashRank — lightweight, chạy tốt trên CPU
from flashrank import Ranker
ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")

# Option 2: Cross-encoder từ sentence-transformers
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
# Model nhỏ ~80MB, inference ~50ms/query trên CPU

def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    pairs = [(query, chunk.content) for chunk in chunks]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in ranked[:top_k]]
```

---

### Tầng 5: HyDE — Hypothetical Document Embedding (Giải quyết Failure 2)

Thay vì embed query ngắn, generate một "document giả" trả lời query, rồi dùng embedding của document đó để search. Document giả không cần đúng — chỉ cần viết giống style tài liệu.

```python
HYDE_PROMPT = """
Bạn là giảng viên kỹ thuật điện gió tại Đại học Điện lực.
Hãy viết một đoạn văn ngắn (3-5 câu) bằng tiếng Việt, trả lời câu hỏi sau 
theo phong cách tài liệu kỹ thuật. Bao gồm cả thuật ngữ tiếng Anh khi phù hợp.

Câu hỏi: {query}
"""

# Query: "hộp số"
# HyDE output: "Hộp số (gearbox/speed increaser) trong turbine gió có nhiệm vụ 
#   tăng tốc độ quay từ rotor (~15-20 rpm) lên tốc độ phù hợp với máy phát điện 
#   (~1500 rpm). Tỷ số truyền (gear ratio) thường từ 1:80 đến 1:100. Theo nguyên lý
#   bảo toàn công suất, khi tốc độ tăng thì momen xoắn (torque) giảm tỷ lệ nghịch,
#   tức P = T × ω, do đó momen xoắn ở trục ra nhỏ hơn nhiều so với trục vào."

# Embedding của đoạn này SẼ gần chunk chứa "momen xoắn tỷ lệ nghịch với tốc độ"
# → Giải quyết Failure 2
```

**Khi nào dùng HyDE vs Multi-Query:**
- HyDE tốt khi: query ngắn, concept gap lớn (Failure 2)
- Multi-Query tốt khi: query có thể interpret nhiều cách, vocabulary mismatch (Failure 1)
- **Tốt nhất: dùng cả hai song song, merge kết quả**

---

## Pipeline Đề xuất Hoàn chỉnh

```
User query: "hệ thống phanh"
    │
    ├─── [1] Synonym Expansion
    │    → "hệ thống phanh thắng brake braking hãm"
    │
    ├─── [2] Multi-Query Generation (LLM)
    │    → "Các loại brake trong turbine gió"
    │    → "Pitch to feather aerodynamic braking"
    │    → "Hệ thống an toàn bảo vệ quá tốc"
    │
    ├─── [3] HyDE Document Generation (LLM)
    │    → "Hệ thống phanh turbine gió gồm 2 loại chính:
    │        phanh khí động học (pitch to feather)..."
    │
    ▼
    [4] Parallel Search (cho mỗi query variant ở trên)
    ├── Dense search (pgvector) → top 20 mỗi query
    └── BM25 search (tsvector) → top 20 mỗi query
    │
    ▼
    [5] Merge + Deduplicate (RRF)
    → ~30-40 unique chunks
    │
    ▼
    [6] Rerank (Cross-encoder, CPU)
    → top 5 chunks
    │
    ▼
    [7] LLM Generate Answer (Gemma / GPT-4o-mini)
    → Câu trả lời chính xác, có cả aerodynamic brake
```

**Lưu ý quan trọng:**
- Bước [1] là lookup bảng (0ms)
- Bước [2]+[3] là 2 LLM calls — có thể chạy parallel (~1-2s với API)
- Bước [4] là multiple DB queries (~50-100ms)
- Bước [6] là cross-encoder inference (~50ms trên CPU)
- **Tổng latency thêm: ~2-3s** (chấp nhận được cho chatbot)

---

## Cải thiện Chunking cho 11 file

### Chiến lược chunking đề xuất

Với tài liệu kỹ thuật điện gió (có cấu trúc chương/mục/tiểu mục rõ ràng):

```python
def smart_chunk(document: str, max_tokens: int = 512, overlap: int = 50) -> list:
    """
    Chunking chiến lược cho tài liệu kỹ thuật.
    Ưu tiên giữ nguyên cấu trúc section.
    """
    # 1. Split theo heading structure (## hoặc regex section number)
    sections = split_by_headings(document)
    
    chunks = []
    for section in sections:
        if count_tokens(section) <= max_tokens:
            # Section đủ nhỏ → giữ nguyên
            chunks.append(section)
        else:
            # Section quá lớn → split theo paragraph, giữ heading
            heading = extract_heading(section)
            paragraphs = section.split("\n\n")
            current_chunk = heading + "\n\n"
            
            for para in paragraphs:
                if count_tokens(current_chunk + para) > max_tokens:
                    chunks.append(current_chunk)
                    current_chunk = heading + "\n\n" + para  # Giữ heading ở mỗi chunk
                else:
                    current_chunk += "\n\n" + para
            
            if current_chunk.strip() != heading.strip():
                chunks.append(current_chunk)
    
    return chunks
```

**Mẹo quan trọng:** Luôn giữ heading/tiêu đề section ở đầu mỗi chunk. Điều này giúp cả embedding lẫn BM25 hiểu chunk nằm trong ngữ cảnh nào.

---

## Đánh giá: Dùng Benchmark 130 cặp Q&A

Bạn đã có 130 cặp Q&A — đây là tài sản cực kỳ quý. Dùng nó để đo impact của từng tầng:

```python
def evaluate_retrieval(qa_pairs, retriever, top_k=5):
    """Đo retrieval quality trên benchmark."""
    hits = 0
    total = len(qa_pairs)
    
    for q, expected_answer in qa_pairs:
        retrieved_chunks = retriever.search(q, top_k=top_k)
        retrieved_text = " ".join([c.content for c in retrieved_chunks])
        
        # Check xem answer có nằm trong retrieved chunks không
        # (dùng LLM judge hoặc keyword overlap)
        if answer_is_in_context(expected_answer, retrieved_text):
            hits += 1
    
    recall = hits / total
    return recall

# Đo baseline trước
baseline_recall = evaluate_retrieval(qa_pairs, baseline_retriever)
print(f"Baseline retrieval recall: {baseline_recall:.2%}")

# Đo sau khi thêm contextual chunks
ctx_recall = evaluate_retrieval(qa_pairs, contextual_retriever)
print(f"Contextual retrieval recall: {ctx_recall:.2%}")

# Đo sau khi thêm multi-query + rerank
full_recall = evaluate_retrieval(qa_pairs, full_pipeline_retriever)
print(f"Full pipeline recall: {full_recall:.2%}")
```

---

## Thứ tự Triển khai Khuyến nghị

| Thứ tự | Giải pháp | Effort | Impact dự kiến | Giải quyết |
|--------|-----------|--------|----------------|------------|
| 1 | Contextual Chunking | 2-3 giờ (chạy 1 lần offline) | **Cao nhất** — giảm failure 35-49% | Cả 2 failures |
| 2 | Domain Synonym Dict | 1-2 giờ (thủ công + LLM extract) | Trung bình — catch exact match cases | Failure 1 |
| 3 | Hybrid Search (BM25 + Dense) | 2-4 giờ (thêm tsvector vào pgvector) | Cao — BM25 catch keyword mà dense bỏ sót | Failure 1 |
| 4 | Reranking (FlashRank/Cross-encoder) | 1-2 giờ | Trung bình — cải thiện precision top-5 | Cả 2 |
| 5 | Multi-Query + HyDE | 3-4 giờ | Cao — giải quyết concept gap triệt để | Failure 2 |

**Tổng thời gian:** ~10-15 giờ dev. Nhưng chỉ cần bước 1 + 3 đã có thể cải thiện **rất đáng kể**.

---

## Embedding Model cho Tiếng Việt

Một yếu tố ít ai đề cập: chất lượng embedding model ảnh hưởng rất lớn đến retrieval tiếng Việt.

### Models đề xuất (chạy được trên CPU 8GB):

| Model | Kích thước | Tiếng Việt | Ghi chú |
|-------|-----------|------------|---------|
| `bkai-foundation-models/vietnamese-bi-encoder` | ~400MB | Tốt nhất cho VN | Train trên PhoBERT, benchmark Legal Retrieval VN |
| `intfloat/multilingual-e5-small` | ~470MB | Tốt | Multilingual, asymmetric retrieval tốt |
| `BAAI/bge-m3` | ~2.3GB | Rất tốt | Hybrid dense+sparse trong 1 model, nhưng nặng |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | ~470MB | Khá | Lightweight, nhanh trên CPU |

**Khuyến nghị:** Thử `vietnamese-bi-encoder` của BKAI (Đại học Bách khoa Hà Nội) trước — model này train trên dữ liệu pháp luật Việt Nam nên hiểu synonym tiếng Việt tốt hơn các model multilingual generic. Nếu kết quả chưa đủ, chuyển sang `multilingual-e5-small`.

### Fine-tune embedding cho domain điện gió (Optional, Advanced)

Với 130 cặp Q&A, bạn có thể fine-tune embedding model:

```python
from sentence_transformers import SentenceTransformer, InputExample, losses

# Training data từ benchmark
train_examples = []
for q, a in qa_pairs:
    # Positive pair: query + chunk chứa answer
    relevant_chunk = find_chunk_containing(a)
    train_examples.append(InputExample(texts=[q, relevant_chunk], label=1.0))
    
    # Negative pair: query + random chunk
    random_chunk = get_random_chunk()
    train_examples.append(InputExample(texts=[q, random_chunk], label=0.0))

model = SentenceTransformer("intfloat/multilingual-e5-small")
train_loss = losses.CosineSimilarityLoss(model)
model.fit(
    train_objectives=[(DataLoader(train_examples, batch_size=16), train_loss)],
    epochs=3,
    warmup_steps=10
)
model.save("windbot-embedding-v1")
```

---

## Tài nguyên Trực tiếp Liên quan

### Code & Cookbooks
- **Anthropic Contextual Retrieval Cookbook**: https://github.com/anthropics/anthropic-cookbook/blob/main/skills/contextual-embeddings/guide.ipynb
- **NirDiamant/RAG_Techniques** (GitHub, 40K+ stars): Notebooks cho HyDE, Multi-Query, Reranking — copy-paste ready
- **Palo Alto Networks Synonym-aware RAG blog**: Case study thực tế xử lý vocabulary mismatch trong enterprise

### Vietnamese-specific
- **BKAI Vietnamese Bi-encoder**: https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder
- **Paper "Towards Comprehensive Vietnamese RAG"**: https://arxiv.org/html/2403.01616v2 — Datasets và models cho Vietnamese RAG
- **PyVi (Vietnamese tokenizer)**: Hỗ trợ word segmentation cho BM25 index tiếng Việt

### Cộng đồng hỏi đáp
- **r/RAG** — Subreddit chuyên RAG, real-world debugging discussions
- **r/LocalLLaMA** — Self-hosted LLM + RAG trên hardware hạn chế (rất relevant cho setup CPU-only)
- **RAGHub** (github.com/Andrew-Jang/RAGHub) — Catalog tool mới nhất, link từ r/RAG

---

*Tài liệu này tập trung 100% vào vấn đề retrieval của WindBot. Mỗi giải pháp đều có code mẫu và có thể triển khai trực tiếp trên stack hiện tại (FastAPI + pgvector + CPU-only).*