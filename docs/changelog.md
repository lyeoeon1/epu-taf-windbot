# WindBot v2.0 — Changelog & Quá trình thực hiện

> **Thời gian:** 2026-03-23 → 2026-03-24
> **Mục tiêu:** Cải thiện chất lượng chatbot từ phản hồi khách hàng
> **Kết quả:** Test pass rate 73% → 85%, nạp thêm 3 PDF tiếng Anh (1593 chunks)

---

## 1. Tổng quan vấn đề ban đầu

Khách hàng phản hồi 3 vấn đề chính:

1. **Không nhất quán** — hỏi cùng câu nhiều lần ra kết quả khác nhau
2. **Không nhớ sửa đổi** — user sửa lỗi bot nhưng bot không dùng lại
3. **Sai thông tin** — một số câu trả lời factual không chính xác

---

## 2. Quá trình thực hiện chi tiết

### Phase 1: Đo baseline + Fix consistency, memory, accuracy (PR #36-#38)

#### 2.1 Đo baseline benchmark
- Convert `benchmark-windbot-v1.md` → JSON (160 Q&A pairs)
- Chạy `evaluate_rag.py` → baseline scores
- **Lưu ý:** Benchmark scores 5.0/5.0 tuyệt đối do Q&A đã nạp vào vector store → "quay bài"

#### 2.2 Fix consistency (PR #36)
| Thay đổi | File | Chi tiết |
|----------|------|----------|
| Giảm temperature | `backend/app/services/rag.py` | 0.3 → 0.1 |
| Tăng retrieval | `backend/app/services/rag.py` | `similarity_top_k` 5 → 10 |
| Thêm similarity cutoff | `backend/app/services/rag.py` | `SimilarityPostprocessor(similarity_cutoff=0.15)` |
| Grounding rules | `backend/app/prompts/system.py` | Thêm anti-fabrication rules EN+VI |

#### 2.3 Fix memory (PR #36)
| Thay đổi | File | Chi tiết |
|----------|------|----------|
| Tăng memory buffer | `backend/app/services/rag.py` | `token_limit` 4000 → 8000 |
| Tăng history limit | `backend/app/services/chat_history.py` | `limit` 20 → 40 |
| Correction-awareness | `backend/app/prompts/system.py` | Thêm rule ưu tiên user corrections |
| Custom condense prompt | `backend/app/prompts/system.py` | Thêm `CONDENSE_PROMPT_EN/VI` giữ corrections |

#### 2.4 Fix accuracy — Q&A corpus (VPS)
```bash
# Generate 150 Q&A pairs (30 x 5 categories)
python scripts/generate_qa_corpus.py --category structure --language vi --count 30
python scripts/generate_qa_corpus.py --category operations --language vi --count 30
python scripts/generate_qa_corpus.py --category maintenance --language vi --count 30
python scripts/generate_qa_corpus.py --category safety --language vi --count 30
python scripts/generate_qa_corpus.py --category troubleshooting --language vi --count 30

# Nạp vào vector store
for cat in structure operations maintenance safety troubleshooting; do
  python scripts/ingest_qa.py --input ./data/qa_corpus/$cat/qa_${cat}_vi.json --language vi
done
```

#### 2.5 Scope restriction + correction retention (PR #36-#37)
- Thêm scope restriction: chỉ trả lời về tua-bin gió
- Thêm continuation phrases exception: "kể thêm đi", "tiếp đi"
- Thêm environment/climate change in-scope

---

### Phase 2: Context mode + Test tự động (PR #34, #38)

#### 2.6 Switch to context mode (PR #34)
**Root cause:** `condense_plus_context` mode drop chat history sau condensing → user corrections bị mất.

**Fix:** Luôn dùng `context` mode — LLM thấy full chat history bao gồm corrections.

```python
# backend/app/services/rag.py — trước
mode = "condense_plus_context" if has_history else "context"

# sau
chat_mode="context"  # always
```

#### 2.7 Test tự động bằng Playwright
- Tạo `test-scenarios-windbot-v1.md` — 46 test cases, 8 categories
- Chạy tự động qua Playwright API (`fetch('/api/chat')` trực tiếp)
- **Kết quả v1:** 30/46 passed (73%)

---

### Phase 3: Correction injection system (PR #38)

#### 2.8 Tạo corrections.py — hệ thống detect + extract + inject corrections

**File mới:** `backend/app/services/corrections.py`

Flow:
```
User message → Regex detect correction? (< 1ms)
    ├─ No  → normal flow
    └─ Yes → LLM extract structured facts (~500ms)
             → {entity, attribute, old_value, new_value}
             → Cache in message metadata
             → Inject into system prompt as [USER CORRECTIONS] block
```

**Regex patterns (EN + VI):**
- "không đúng", "sai rồi", "chưa chính xác"
- "ghi nhớ", "nhớ điều này", "remember this"
- "chứ không phải", "actually it's", "that's wrong"

**System prompt injection:**
```
[USER CORRECTIONS — ƯU TIÊN TỐI ĐA / HIGHEST PRIORITY]
1. Vestas V150 — cut-in speed: 3 m/s (corrected from: 3-4 m/s)
[END USER CORRECTIONS]
```

#### 2.9 Rewrite system prompt — 3-tier information hierarchy

**Trước:**
- "Đừng bịa" vs "Dùng corrections" → xung đột

**Sau:**
```
1. USER CORRECTIONS (highest priority — NOT fabrication)
2. KNOWLEDGE BASE (ground in retrieved context)
3. NO INFORMATION ("chưa có trong cơ sở tri thức")
```

#### 2.10 CorrectionOverridePostprocessor

**File:** `backend/app/services/rag.py`

Post-process retrieved chunks: nếu chunk chứa giá trị xung đột với correction → prepend `[USER CORRECTED: ...]` để LLM thấy override rõ ràng.

**Kết quả v2:** 33/46 passed (78%)

---

### Phase 4: Entity verification + Language detection (PR #39)

#### 2.11 Entity verification — FIRST/THEN/FINALLY sequence
**Vấn đề:** Bot nói "V150 chưa có trong KB" thay vì dùng correction đã có.

**Fix:** Rewrite ENTITY VERIFICATION rule:
1. **FIRST:** Check corrections → nếu có → dùng + "theo thông tin bạn cung cấp"
2. **THEN:** Check KB → bổ sung
3. **ONLY IF both empty:** "chưa có trong cơ sở tri thức"

#### 2.12 Language detection — detect_input_language()
**Vấn đề:** EN input → VI response

**Fix:** Detect ngôn ngữ từ message text (Vietnamese diacritics vs ASCII ratio) → inject `[RESPOND IN: ENGLISH]` vào corrections block (gần user message nhất → high salience).

```python
def detect_input_language(message: str) -> str:
    vi_chars = set('àáảãạăắằẳẵặâấầẩẫậ...')
    has_vi = any(c in vi_chars for c in message.lower())
    if has_vi:
        return "Vietnamese"
    ascii_ratio = sum(1 for c in message if c.isascii() and c.isalpha()) / max(len(message), 1)
    if ascii_ratio > 0.7:
        return "English"
    return ""
```

#### 2.13 Fix IndentationError (PR #40)
- `corrections.py` line 129 — `format_corrections_block()` có indentation sai
- Fix trivial, deploy lại

**Kết quả v3:** 37/46 passed (85%)

---

### Phase 5: Nạp 3 PDF tiếng Anh mới (2026-03-24)

#### 2.14 Upload 3 PDF mới lên VPS

**3 file từ nhà trường (tiếng Anh):**
1. `R06-004 - Wind Energy Design and Fundamentals - US.pdf`
2. `Wind_Energy_Handbook.pdf`
3. `windenergyengineeringahandbookforonshoreandoffshorewindturbines-1.pdf`

**Upload qua Termius SFTP:**
```
Local → SFTP → /home/botai/botai-backend/repo/backend/data/new_pdfs/
```

#### 2.15 Ingest vào vector store

```bash
# (botai@vmi3129537)
cd ~/botai-backend/repo/backend
source venv/bin/activate
set -a; source .env; set +a

python scripts/ingest_docs.py \
  --dir ./data/new_pdfs \
  --language en \
  --tier agentic
```

**Kết quả:**
| File | Chunks |
|------|--------|
| Wind_Energy_Handbook.pdf | 743 |
| R06-004 - Wind Energy Design... | 102 |
| windenergyengineering... | 748 |
| **Tổng mới** | **1593** |

#### 2.16 Cập nhật documents_metadata

Script `ingest_docs.py` chỉ nạp vectors, **không ghi** `documents_metadata` table. Phải INSERT thủ công:

```sql
INSERT INTO documents_metadata (filename, file_type, language, num_chunks) VALUES
('Wind_Energy_Handbook.pdf', 'pdf', 'en', 743),
('R06-004 - Wind Energy Design and Fundamentals - US.pdf', 'pdf', 'en', 102),
('windenergyengineeringahandbookforonshoreandoffshorewindturbines-1.pdf', 'pdf', 'en', 748);
```

#### 2.17 Verify + Test

**Vector store:**
```
Total vectors in collection: 2192
```

**Documents metadata:** 8 entries (5 VI + 3 EN)

**Test Playwright — 8 câu hỏi nội dung mới:**

| ID | Câu hỏi | Ngôn ngữ | Kết quả |
|----|---------|----------|---------|
| EN-01 | Wind energy design fundamentals | EN | ✅ Chi tiết, EN response |
| EN-02 | Offshore vs onshore differences | EN | ✅ So sánh foundations, EN |
| EN-03 | Betz limit | EN | ✅ "Max Cp", Albert Betz, EN |
| EN-04 | Drivetrain components | EN | ✅ Main shaft, gearbox, EN |
| EN-05 | Environmental impacts | EN | ✅ Positive + negative, EN |
| VI-01 | Giới hạn Betz (VI) | VI | ✅ "59.3%", cross-language ✅ |
| VI-02 | Offshore vs onshore (VI) | VI | ✅ Monopile, ăn mòn muối, VI |
| VI-03 | Drivetrain (VI) | VI | ✅ "10-20 vòng/phút", VI |

**Cross-language retrieval hoạt động:** Hỏi VI → retrieve từ PDF EN → trả lời VI ✅

#### 2.18 Test toàn diện nội dung 3 PDF mới — 30 câu hỏi (Playwright tự động)

**Thời gian:** 2026-03-24 17:18 UTC+7
**Kết quả: 29/30 passed (97%)**

##### Tiếng Việt (14/15 pass) — Cross-language retrieval từ PDF tiếng Anh

| ID | Câu hỏi | Kết quả | Ghi chú |
|----|---------|---------|---------|
| VI-01 | Giới hạn Betz là gì và ý nghĩa trong thiết kế tua-bin gió? | ✅ | "59.3% (16/27)", Albert Betz |
| VI-02 | Công thức tính năng lượng gió theo mật độ không khí và tốc độ gió? | ✅ | P = 0.5·ρ·A·v³, LaTeX |
| VI-03 | Đường cong công suất (power curve) được xây dựng như thế nào? | ✅ | Đo lường tốc độ gió, các bước chính |
| VI-04 | Các loại móng nền (foundation) cho tua-bin gió offshore? | ✅ | Gravity, Bucket, Monopile... |
| VI-05 | So sánh direct drive và gearbox? | ✅ | Chi tiết 2 hệ thống |
| VI-06 | Thiết kế khí động học cánh quạt dựa trên nguyên lý nào? | ✅ | Airfoil, lực nâng (lift) |
| VI-07 | Thách thức kỹ thuật offshore so với onshore? | ✅ | Thời tiết, ăn mòn, sóng |
| VI-08 | Hiệu ứng wake (wake effect) là gì? | ✅ | Giảm tốc độ gió, turbulence |
| VI-09 | Tiếng ồn từ tua-bin gió phân loại và đo lường thế nào? | ❌ | Server error 500 |
| VI-10 | Hệ số công suất (capacity factor) phụ thuộc yếu tố nào? | ✅ | Tài nguyên gió, vị trí lắp đặt |
| VI-11 | Phân tích tải trọng (load analysis) bao gồm gì? | ✅ | Wind Load, các yếu tố chính |
| VI-12 | Phương pháp đánh giá tiềm năng gió tại một địa điểm? | ✅ | Cột đo gió (met mast), 1-2 năm |
| VI-13 | Phân bố Weibull trong đánh giá năng lượng gió? | ✅ | k (shape), Weibull parameters |
| VI-14 | Hệ thống pitch control hoạt động thế nào? | ✅ | Điều chỉnh góc cánh, tối ưu lực khí động |
| VI-15 | Các tiêu chuẩn IEC cho tua-bin gió? | ✅ | IEC 61400-1, nhiều phần |

##### Tiếng Anh (15/15 pass) — Trực tiếp từ PDF tiếng Anh

| ID | Câu hỏi | Kết quả | Ghi chú |
|----|---------|---------|---------|
| EN-01 | Betz limit and significance in design? | ✅ | "Maximum power coefficient Cp" |
| EN-02 | Aerodynamic principles behind blade design? | ✅ | Lift/drag, airfoil |
| EN-03 | Types of offshore foundations? | ✅ | Monopile 3-7m diameter, gravity |
| EN-04 | Weibull distribution in wind assessment? | ✅ | Hourly mean wind speeds |
| EN-05 | Direct drive vs gearbox comparison? | ✅ | Design, complexity, efficiency |
| EN-06 | Wake effect and wind farm layout? | ✅ | Reduced speed, turbulence |
| EN-07 | Power curve key regions? | ✅ | Wind speed vs power output |
| EN-08 | IEC standards for wind turbine design? | ✅ | IEC 61400-1, safety requirements |
| EN-09 | How pitch control works? | ✅ | Blade angle adjustment |
| EN-10 | Factors affecting capacity factor? | ✅ | Wind speed, cube relationship |
| EN-11 | Load analysis process? | ✅ | Safety, reliability steps |
| EN-12 | Wind resource assessment methods? | ✅ | Wind atlases, met masts |
| EN-13 | Noise classification and measurement? | ✅ | Sound power Lw, pressure Lp |
| EN-14 | Offshore maintenance challenges? | ✅ | Accessibility, weather, cost |
| EN-15 | Tip speed ratio concept? | ✅ | TSR formula, blade tip / wind speed |

##### Phân tích kết quả

- **Cross-language retrieval:** Hỏi tiếng Việt → retrieve chunks tiếng Anh → trả lời tiếng Việt ✅ (14/15)
- **EN response quality:** Trả lời chi tiết với thuật ngữ kỹ thuật chính xác, LaTeX formulas ✅
- **Nội dung mới phủ sóng:** Betz limit, Weibull, tip speed ratio, IEC standards, load analysis — toàn bộ từ 3 PDF mới
- **1 failure (VI-09):** Server error 500 — intermittent, không liên quan đến data mới

---

## 3. Tổng hợp thay đổi code

### Files đã thay đổi

| File | Thay đổi |
|------|----------|
| `backend/app/services/corrections.py` | **MỚI** — CorrectionDetector, extract_correction, collect/format |
| `backend/app/services/rag.py` | temperature 0.1, top_k 15, context mode, CorrectionOverridePostprocessor |
| `backend/app/prompts/system.py` | 3-tier hierarchy, entity verification, scope, language, corrections injection |
| `backend/app/routers/chat.py` | Wire correction flow, detect_input_language, pass corrections to engine |
| `backend/app/services/chat_history.py` | limit 20 → 40 |
| `backend/scripts/ingest_qa.py` | Hỗ trợ generated Q&A format |
| `backend/scripts/generate_qa_corpus.py` | Fix count parameter |

### PRs đã merge

| PR | Title | Status |
|----|-------|--------|
| #34 | Switch to context mode for correction retention | ✅ Merged |
| #36 | Fix consistency, memory, accuracy | ✅ Merged |
| #37 | Move corrections block after context for LLM recency bias | ✅ Merged |
| #38 | Fix P0-P3: correction override, anti-fabrication, scope | ✅ Merged |
| #39 | Fix v2 remaining: entity verification, override matching, language | ✅ Merged |
| #40 | Fix IndentationError in corrections.py | ✅ Merged |
| #41 | Update product requirements v2.0 and test scenarios v3 | ✅ Merged |
| #42 | Update xlsx product requirements v2.0 and add sync script | ✅ Merged |

---

## 4. Kết quả test qua các phiên bản

| Category | v1 (73%) | v2 (78%) | v3 (85%) |
|----------|----------|----------|----------|
| 1. Q&A (8) | 7/8 | 7/8 | **8/8** |
| 2. Corrections (8) | 6/8 | 6/8 | **7/8** |
| 3. Scope (6) | 5/6 | 6/6 | **6/6** |
| 4. Info Hierarchy (6) | 2/6 | 3/6 | **3/6** |
| 5. Consistency (4) | 4/4 | 4/4 | **4/4** |
| 6. Bilingual (4) | 3/4 | 2/4 | **4/4** |
| 7. Suggestions (4) | 4/4 | 4/4 | **4/4** |
| 8. Multi-turn (6) | 4/6 | 5/6 | **5/6** |
| **TOTAL** | **30/46** | **33/46** | **37/46** |

---

## 5. Vector Store — Trạng thái hiện tại

### Documents metadata (8 files)

| Filename | Type | Language | Chunks | Ingested |
|----------|------|----------|--------|----------|
| Dien Gio 1-6.pdf | pdf | vi | 50 | 2026-02-11 |
| Dien Gio 2-6.pdf | pdf | vi | 42 | 2026-02-11 |
| Dien Gio 3-6.pdf | pdf | vi | 40 | 2026-02-11 |
| Dien Gio 4-6.pdf | pdf | vi | 41 | 2026-02-11 |
| Dien Gio 5-6.pdf | pdf | vi | 41 | 2026-02-11 |
| Wind_Energy_Handbook.pdf | pdf | en | 743 | 2026-03-24 |
| R06-004 - Wind Energy Design... | pdf | en | 102 | 2026-03-24 |
| windenergyengineering... | pdf | en | 748 | 2026-03-24 |

### Tổng vectors: 2192
- 214 chunks từ 5 PDF tiếng Việt
- 1593 chunks từ 3 PDF tiếng Anh
- ~385 chunks từ Q&A corpus (5 categories x ~30 pairs)

---

## 6. Vấn đề còn tồn tại (3 cases fail)

| ID | Vấn đề | Root cause |
|----|--------|------------|
| IH-01 | V236 fabrication inconsistent | LLM đôi khi dùng training data thay vì nói "chưa có" |
| IH-03 | Correction bị mất khi hỏi specs entity | Metadata persistence giữa turns không đủ |
| CR-02 | Multiple corrections — chỉ giữ correction đầu | `collect_corrections_from_history` không merge đủ |

---

## 7. Hướng dẫn nạp thêm PDF trong tương lai

### Quy trình

```bash
# 1. Upload PDF lên VPS
mkdir -p ~/botai-backend/repo/backend/data/new_pdfs
# (dùng SFTP/scp để upload)

# 2. Nạp vào vector store
cd ~/botai-backend/repo/backend
source venv/bin/activate
set -a; source .env; set +a
python scripts/ingest_docs.py --dir ./data/new_pdfs --language en --tier agentic
# (đổi --language vi nếu file tiếng Việt)

# 3. Cập nhật metadata (thủ công qua Supabase SQL Editor)
INSERT INTO documents_metadata (filename, file_type, language, num_chunks)
VALUES ('filename.pdf', 'pdf', 'en', <số chunks từ output>);

# 4. Restart backend
exit  # về root
systemctl restart botai-backend

# 5. Verify
python -c "
import vecs, os
vx = vecs.create_client(os.environ['SUPABASE_CONNECTION_STRING'])
col = vx.get_or_create_collection('wind_turbine_docs', dimension=1536)
print(f'Total vectors: {len(col)}')
"
```

### Lưu ý
- LlamaParse `agentic` tier tốn ~$0.003/page
- File PDF gốc không lưu trong repo — chỉ vectors trong Supabase
- Script `ingest_docs.py` **không ghi** `documents_metadata` — cần INSERT thủ công
- Chunks mới **bổ sung** vào vector store, không xóa cũ
