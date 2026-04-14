# WindBot Performance Optimization Phase 3 — Design Spec

## Context

Phase 2 reduced TTFT from 15-20s to ~6s (first message) and ~8-10s (follow-up). Target is <5s for all cases. Remaining bottlenecks: multi-query LLM generation (3s), Phase B search (1.5s), and condense step for follow-ups (+2s).

## Changes

### 1. Smart Condense

**File:** `backend/app/services/windbot_engine.py`

Skip the condense LLM call when the follow-up message is already a standalone question. Detection via regex + length check (<1ms):

**Skip condense when ANY:**
- Message length >50 chars (long questions are usually standalone)
- Message length >30 chars AND contains wind-turbine keywords (tuabin, gió, blade, gearbox, nacelle, rotor, tower, pitch, yaw, generator, etc.)
- Message matches COMPARISON regex patterns from QuestionClassifier

**Always condense when ANY:**
- Message length <20 chars
- Contains continuation phrases: "kể thêm", "tiếp đi", "chi tiết hơn", "tell me more", "go on", "elaborate"
- Contains anaphoric references: "nó", "cái đó", "loại này", "it", "that", "this one"

**Expected savings:** ~2s for ~70% of follow-up messages.

### 2. Adaptive Multi-query

**Files:** `backend/app/services/advanced_retriever.py`, `backend/app/services/rag.py`

Pass `question_type` to AdvancedRetriever. Override `enable_multi_query` at runtime based on question type:

| Question Type | Multi-query | Reasoning |
|---|---|---|
| STRUCTURE | OFF | Specific component questions — 1 query sufficient |
| GENERAL | OFF | Greetings/general — no RAG needed |
| PRINCIPLE | ON if query <40 chars, OFF otherwise | Short = ambiguous, long = specific |
| PROCEDURE | OFF | Step-by-step questions are specific |
| COMPARISON | ON | Needs multiple search perspectives |
| TROUBLESHOOT | ON | Needs multiple diagnostic angles |

**Expected savings:** 3-4.5s (multi-query gen + Phase B) for ~60% of questions.

### 3. Pre-compute Original Query Search

**File:** `backend/app/routers/chat.py`

Start dense + BM25 search for the original query immediately when the message arrives, in parallel with classification + save/load + corrections loading. Pass prefetched results to the retriever so Phase A skips the original query search.

Flow:
```
t=0: Message arrives
     ├─ prefetch: dense_search(message) + bm25_search(message)
     ├─ classification (regex/LLM)
     ├─ save_message + get_session_messages
     └─ load corrections
t=1.5s: All parallel tasks done, prefetch results available
t=1.5s: Build chat engine with prefetched results
t=1.5s: AdvancedRetriever skips original query in Phase A
```

**Implementation:** Add `prefetched_results` parameter to AdvancedRetriever. If provided, use them for the original query instead of searching again.

**Expected savings:** ~1-1.5s (overlap search with classification/corrections).

### 4. Embedding Cache

**File:** `backend/app/services/advanced_retriever.py`

LRU cache for query embeddings to avoid redundant OpenAI API calls:

```python
from functools import lru_cache
# Cache 200 query embeddings (~300KB memory)
# Same queries in a session or across sessions get instant embedding
```

Hook into the dense search path: before calling the VectorStoreIndex retriever, check if the embedding is cached. If so, use it directly with pgvector.

**Note:** LlamaIndex's VectorStoreIndex.as_retriever().retrieve() internally calls the embedding model. To intercept this, either:
- (a) Wrap the embedding model with a caching layer, OR
- (b) Call embedding + pgvector search separately (bypass LlamaIndex retriever)

Option (a) is cleaner: create a `CachedOpenAIEmbedding` class that wraps `OpenAIEmbedding` and caches `get_query_embedding()`.

**Expected savings:** 0.5-1s for repeat/similar queries.

## Expected Results

| Scenario | Current | After Phase 3 | Target |
|---|---|---|---|
| Greeting | 2s | 2s | <5s ✅ |
| STRUCTURE (first) | 6s | ~3s | <5s ✅ |
| COMPARISON (first) | 6s | ~5s | <5s ✅ |
| Follow-up (clear) | 8-10s | ~3-5s | <5s ✅ |
| Follow-up (ambiguous) | 8-10s | ~6-7s | <5s ⚠️ |

## Implementation Order

1. **Adaptive Multi-query** — highest impact, isolated change
2. **Smart Condense** — second highest, only affects follow-ups
3. **Pre-compute Search** — requires chat.py + retriever coordination
4. **Embedding Cache** — nice-to-have, smallest impact

## Files to Modify

| File | Changes |
|---|---|
| `backend/app/services/advanced_retriever.py` | Accept question_type + prefetched_results, adaptive multi-query logic |
| `backend/app/services/windbot_engine.py` | Smart condense logic |
| `backend/app/services/rag.py` | Pass question_type to retriever |
| `backend/app/routers/chat.py` | Pre-compute search, pass to engine |
| `backend/app/services/cached_embedding.py` | **New** — CachedOpenAIEmbedding wrapper |

## Verification

After each change:
1. Benchmark retrieval time with `python -c` on VPS (like Phase 2)
2. Test on website with real questions
3. Compare response quality with baseline session `2ccd12c5`
4. Ensure follow-up questions still work correctly (especially ambiguous ones)
