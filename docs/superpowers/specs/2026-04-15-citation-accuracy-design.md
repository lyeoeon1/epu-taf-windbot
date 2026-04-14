# Improve Citation Accuracy — Design Spec

## Problem

Citation accuracy scored 3.6/5 in benchmark. GPT judge reports citations are "decorative" — LLM writes [1][2][3] but numbers don't always match the actual source chunks they reference. Users can click [N] to see source content, so incorrect citations break trust.

## Root Cause

1. System prompt says "cite [N] where N is the Source number" but doesn't explicitly bind [Source N] chunks to [N] citations
2. Context chunks are separated only by [Source N] prefix — no clear boundary between chunks
3. LLM cites by reading order, not by content attribution
4. Question type prompts have zero citation instructions

## Changes

### 1. Improve System Prompt Citation Instructions

**File:** `backend/app/prompts/system.py` (lines 88-101)

Replace the current citation instruction with a more explicit version:

**Current:**
```
- INLINE CITATION FORMAT: When you use information from the context, you MUST cite it 
INLINE immediately after the relevant sentence or clause using [N] where N is the Source 
number shown in the context...
```

**New (Vietnamese prompt):**
```
- TRÍCH DẪN CHÍNH XÁC: Mỗi đoạn context bên dưới bắt đầu bằng "--- [Source N] ---". 
Khi bạn sử dụng thông tin từ đoạn [Source N], bạn PHẢI viết [N] ngay sau câu chứa 
thông tin đó. Quy tắc:
  1. [N] PHẢI trỏ đúng đoạn [Source N] chứa thông tin đó
  2. KHÔNG cite [N] nếu thông tin không nằm trong đoạn [Source N]
  3. Nếu không chắc nguồn, KHÔNG cite — tốt hơn là cite sai
  4. Đặt citation NGAY SAU câu, không gom ở cuối đoạn
  Ví dụ: "Tua-bin gió thường có 3 cánh quạt [2] và công suất lên đến 15 MW [1][5]."
```

**English prompt (similar update):**
```
- PRECISE CITATION: Each context passage below starts with "--- [Source N] ---". 
When you use information from [Source N], you MUST write [N] immediately after the 
sentence containing that information. Rules:
  1. [N] MUST point to the [Source N] passage containing that information
  2. Do NOT cite [N] if the information is NOT in [Source N]
  3. If unsure which source, do NOT cite — better no citation than wrong citation
  4. Place citation RIGHT AFTER the sentence, not grouped at end
```

### 2. Add Clear Source Boundaries in Context

**File:** `backend/app/services/rag.py` (SourceNumberingPostprocessor, lines 118-136)

Change the prefix format from:
```
[Source 1] Wind turbines typically have 3 blades...
```

To:
```
--- [Source 1] (Dien_Gio.pdf, p.29) ---
Wind turbines typically have 3 blades...
--- END Source 1 ---
```

This gives the LLM clear visual boundaries to distinguish sources.

Implementation: modify `_postprocess_nodes()` to:
- Prepend `--- [Source N] (filename, p.page) ---\n` 
- Append `\n--- END Source N ---`

### 3. Add Citation Reminder to Question Type Prompts

**File:** `backend/app/prompts/question_types.py`

Add one line to EACH question type instruction:
```
"- Cite [N] chính xác theo source number. Mỗi số liệu, thông số kỹ thuật phải có [N] trỏ đúng source.\n"
```

## Expected Impact

- citation_accuracy: 3.6 → 4.0-4.5 (clearer instructions + boundaries help LLM cite correctly)
- Other metrics: should not decrease (same retrieval, same content, just better citation format)

## Files to Modify

| File | Change |
|---|---|
| `backend/app/prompts/system.py` | Replace citation instructions (both EN and VI) |
| `backend/app/services/rag.py` | SourceNumberingPostprocessor: add boundaries + metadata |
| `backend/app/prompts/question_types.py` | Add citation reminder to each type |

## Verification

1. Run benchmark: `python scripts/benchmark_runner.py --input data/qa_corpus/benchmark-recent-10.json`
2. Compare citation_accuracy with previous run (3.6 baseline)
3. Check other metrics don't regress
4. Manual spot-check: click [N] on frontend, verify content matches
