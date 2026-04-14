# WindBot Performance Optimization Phase 2 — Design Spec

## Context

Customer feedback: chatbot response time is too slow (15-20s TTFT). Phase 1 optimization was attempted (4 changes) but reverted because content quality decreased and speed improvement was not noticeable on VPS.

**Root cause analysis from VPS logs:**
- FlashRank reranking: **4-5s** (40% of total) — PyTorch CPU inference, unoptimized
- Sequential search loops: **2-3s** — 8 network calls in series
- Multi-query LLM generation: **3s** — blocks all search from starting
- Greeting goes through full RAG pipeline unnecessarily

**Target:** TTFT < 7s for all query types. Content quality must remain at current level (gpt-4.1-mini baseline).

**Constraints:** Free/local solutions only. VPS: 4 cores, 8GB RAM. No paid API rerankers.

---

## Design

### Change 1: ONNX Runtime Reranker (replaces FlashRank)

**File:** `backend/app/services/reranker.py`

Replace `FlashReranker` with `OnnxReranker`:
- Export `cross-encoder/ms-marco-MiniLM-L-12-v2` to ONNX format using `optimum`
- Quantize to INT8 using `onnxruntime.quantization`
- Use `onnxruntime.InferenceSession` with `CPUExecutionProvider`
- Set `intra_op_num_threads=4` to use all VPS cores
- Batch all (query, passage) pairs into one forward pass
- Warmup with dummy inference at startup

**Interface:** Same as current — `rerank(query, candidates, top_k) -> list[NodeWithScore]`

**File:** `backend/app/dependencies.py` — Change startup to initialize `OnnxReranker` instead of `FlashReranker`

**File:** `backend/app/config.py` — Add `onnx_model_path: str = "models/reranker-int8"` and `reranker_threads: int = 4`

**New file:** `backend/scripts/export_onnx_reranker.py` — One-time script to export + quantize model

**Expected savings:** 4-5s → 0.2-0.5s = **~4s saved**

---

### Change 2: Parallel Search with Speculative Execution

**File:** `backend/app/services/advanced_retriever.py`

Restructure `_retrieve()` into concurrent phases:

```
Phase A (immediate, parallel):
  - Dense search for [original_query, expanded_query]
  - BM25 search for [original_query, expanded_query]
  - Multi-query LLM generation (gpt-4o-mini)
  All 5 tasks run concurrently via ThreadPoolExecutor

Phase B (after multi-query returns):
  - Dense search for [multi_query_1, multi_query_2]
  - BM25 search for [multi_query_1, multi_query_2]
  4 tasks run concurrently

Phase C (after all searches):
  - RRF fusion (unchanged)
  - QA filter + VI boost (unchanged)
  - ONNX reranking (from Change 1)
```

Key implementation details:
- `ThreadPoolExecutor(max_workers=8)` — all tasks are I/O-bound
- Multi-query generation runs in parallel via `concurrent.futures.ThreadPoolExecutor` + `asyncio.run()` (same pattern as current code, just overlapped with Phase A searches)
- Error handling: individual search failures return empty results, pipeline continues

**Expected savings:** Sequential 5-6s → Parallel ~3.3s = **~2-3s saved**

---

### Change 3: Custom WindBotChatEngine + Greeting Fast-path

#### 3a: Greeting Fast-path

**File:** `backend/app/routers/chat.py`

After classification, if `question_type == "GENERAL"` AND message is a short greeting (< 20 chars, matches greeting patterns):
- Skip `get_chat_engine()` and entire RAG pipeline
- Call OpenAI directly with greeting system prompt + last 2 exchanges for context
- Stream tokens via same SSE mechanism
- Save response, generate suggestions — same UX

Greeting detection: reuse existing regex patterns from `QuestionClassifier` + simple length check.

**Expected savings:** 10-13s → 0.5-1s for greetings

#### 3b: Custom WindBotChatEngine

**New file:** `backend/app/services/windbot_engine.py`

Replace `CondensePlusContextChatEngine` with a custom engine that:

1. **For first messages (no history):** Skip condense, go directly to retrieval. Same as current behavior but explicit.

2. **For follow-up messages:** Run condense in parallel with initial retrieval:
   - Start retrieving with raw user message immediately
   - Simultaneously condense question using chat history
   - When condensed query ready, start second retrieval pass
   - Merge both result sets via existing RRF
   - Rerank against the condensed query

3. **Native async pipeline:** The engine exposes `async stream_chat()` that the router can await directly, eliminating the `asyncio.to_thread(chat_engine.stream_chat)` overhead.

4. **Reuse LlamaIndex components:**
   - `CompactAndRefine` response synthesizer for context formatting + streaming
   - `ChatMemoryBuffer` for memory management
   - Same system prompt, condense prompt, postprocessors

**File:** `backend/app/services/rag.py` — Modify `get_chat_engine()` to return `WindBotChatEngine`

**File:** `backend/app/routers/chat.py` — Switch from `asyncio.to_thread(stream_chat)` to `await engine.astream_chat()`

**Expected savings for follow-ups:** 1-2s (condense overlapped with initial retrieval)

---

## Combined Impact

| Scenario | Current | After | Target |
|---|---|---|---|
| Greeting | 10-13s | **0.5-1s** | < 7s |
| First RAG message | 10-13s | **4-5.5s** | < 7s |
| Follow-up message | 12-16s | **4.5-6s** | < 7s |

**Breakdown for first RAG message after all changes:**
- Classification + corrections: 1-2s (unchanged, already parallelized)
- Phase A: max(search_original, multi_query_gen) = max(0.5s, 3s) = 3s
- Phase B: search multi-query variants = 0.3-0.5s
- ONNX reranking: 0.2-0.5s
- LLM first token: 0.5s
- **Total: ~4-5.5s**

---

## Implementation Order

1. **Change 1:** ONNX Reranker — highest impact, isolated, easy to validate
2. **Change 2:** Parallel Search — second highest impact, builds on existing code
3. **Change 3a:** Greeting Fast-path — quick win, isolated
4. **Change 3b:** Custom Engine — most complex, but needed for follow-up optimization

After each change: deploy to VPS, measure TTFT with real queries, validate quality.

---

## Files to Modify

| File | Changes |
|---|---|
| `backend/app/services/reranker.py` | Replace FlashReranker with OnnxReranker |
| `backend/app/services/advanced_retriever.py` | Parallel search phases, restructure _retrieve() |
| `backend/app/services/windbot_engine.py` | **New** — Custom async chat engine |
| `backend/app/routers/chat.py` | Greeting fast-path, async engine integration |
| `backend/app/services/rag.py` | Return WindBotChatEngine from get_chat_engine() |
| `backend/app/config.py` | ONNX model path, reranker threads config |
| `backend/app/dependencies.py` | Initialize OnnxReranker at startup |
| `backend/scripts/export_onnx_reranker.py` | **New** — One-time ONNX export script |
| `backend/requirements.txt` | Add onnxruntime, optimum, transformers |

---

## Verification Plan

1. **ONNX Reranker validation:**
   - Run `backend/scripts/evaluate_retrieval_only.py` with both FlashRank and ONNX, compare NDCG@10
   - Compare reranking output for 10 test queries (should be identical for FP32, <0.5% diff for INT8)
   - Measure reranking time on VPS: target < 0.5s for 30 candidates

2. **Parallel search validation:**
   - Add timing logs for each search phase
   - Verify same candidates produced (order may differ, but set should be identical)
   - Measure total search phase time: target < 3.5s

3. **Greeting fast-path validation:**
   - Test with "xin chào", "hello", "chào bạn" — should bypass RAG, TTFT < 1s
   - Test that non-greeting short messages still go through RAG

4. **End-to-end validation:**
   - Run the same 10 test questions from the A/B test session
   - Compare response quality with gpt-4.1-mini baseline (session `2ccd12c5`)
   - Measure TTFT for each: all should be < 7s
   - Playwright automated test for regression

5. **VPS deployment:**
   - `cd /home/botai/repo && git pull && pip install -r requirements.txt && sudo systemctl restart botai-backend`
   - Monitor logs for errors during first 10 minutes
   - Run 5 test queries to confirm functionality
