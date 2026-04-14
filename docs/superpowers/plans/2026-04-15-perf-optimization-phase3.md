# Performance Optimization Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce TTFT from ~6s (first message) and ~8-10s (follow-up) to <5s for all query types.

**Architecture:** Four layered optimizations: (1) adaptive multi-query per question type eliminates 3-4.5s LLM+search overhead for 60% of queries, (2) smart condense skips the 2s LLM call for standalone follow-ups, (3) pre-compute search overlaps original query retrieval with classification/I/O, (4) embedding cache avoids redundant OpenAI API calls.

**Tech Stack:** Python 3.12, FastAPI, LlamaIndex, OpenAI API, Supabase pgvector, ONNX Runtime

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `backend/app/services/advanced_retriever.py` | Retrieval pipeline with adaptive multi-query + prefetch support | Modify |
| `backend/app/services/windbot_engine.py` | Chat engine with smart condense logic | Modify |
| `backend/app/services/rag.py` | Engine factory — passes question_type to retriever | Modify |
| `backend/app/routers/chat.py` | HTTP handler — pre-compute search in parallel | Modify |
| `backend/app/services/cached_embedding.py` | LRU-cached embedding wrapper | Create |
| `backend/app/services/rag.py` | Use CachedOpenAIEmbedding in Settings | Modify |

---

### Task 1: Adaptive Multi-query per Question Type

**Files:**
- Modify: `backend/app/services/advanced_retriever.py` (lines 44-68, 218-257)
- Modify: `backend/app/services/rag.py` (lines 264-283)

- [ ] **Step 1: Add question_type param to AdvancedRetriever**

In `backend/app/services/advanced_retriever.py`, add `question_type` parameter to `__init__` and use it to override `enable_multi_query` at runtime:

```python
# In __init__, after existing params, add:
        # Question type for adaptive multi-query
        question_type: str = "GENERAL",
```

After `self._multi_query_count = multi_query_count`, add:

```python
        # Adaptive multi-query: disable for simple question types
        self._question_type = question_type
        if question_type in ("STRUCTURE", "GENERAL", "PROCEDURE"):
            self._enable_multi_query = False
            self._enable_hyde = False
        elif question_type == "PRINCIPLE" and len(query) > 40 if hasattr(self, '_initial_query') else True:
            # PRINCIPLE: only use multi-query for short/ambiguous queries
            # This is handled at retrieve time since we don't have the query yet
            pass
```

Wait — the query isn't available at `__init__` time. The PRINCIPLE length check must happen in `_retrieve()`. Simplify `__init__` to:

```python
        # Adaptive multi-query: disable for simple question types
        self._question_type = question_type
        if question_type in ("STRUCTURE", "GENERAL", "PROCEDURE"):
            self._enable_multi_query = False
            self._enable_hyde = False
```

Then in `_retrieve()`, at the top after `query = query_bundle.query_str`, add the PRINCIPLE check:

```python
        # Adaptive multi-query for PRINCIPLE: skip if query is long enough
        if self._question_type == "PRINCIPLE" and len(query) > 40:
            need_multi_query = False
        else:
            need_multi_query = self._enable_multi_query or self._enable_hyde
```

Replace the existing `need_multi_query = self._enable_multi_query or self._enable_hyde` line (currently line 241).

- [ ] **Step 2: Pass question_type from rag.py to AdvancedRetriever**

In `backend/app/services/rag.py`, the `get_chat_engine()` function already receives `question_type` as a parameter (line 199). Add it to the AdvancedRetriever constructor call. After `multi_query_count=app_settings.multi_query_count,` add:

```python
            question_type=question_type,
```

- [ ] **Step 3: Verify syntax**

Run:
```bash
cd /Users/hung/conductor/workspaces/botai/copenhagen-v2/backend
python3 -c "import py_compile; py_compile.compile('app/services/advanced_retriever.py', doraise=True); py_compile.compile('app/services/rag.py', doraise=True); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/advanced_retriever.py backend/app/services/rag.py
git commit -m "perf: adaptive multi-query — skip for STRUCTURE/GENERAL/PROCEDURE types"
```

---

### Task 2: Smart Condense for Follow-ups

**Files:**
- Modify: `backend/app/services/windbot_engine.py` (lines 135-145, 196-220)

- [ ] **Step 1: Add standalone detection function**

In `backend/app/services/windbot_engine.py`, add this function before the `WindBotChatEngine` class:

```python
import re

# Wind turbine technical keywords for standalone detection
_TECHNICAL_KEYWORDS = re.compile(
    r"(tuabin|tua-bin|gió|wind|blade|cánh|gearbox|hộp số|nacelle|rotor|tower|trụ|"
    r"pitch|yaw|generator|máy phát|turbine|điện gió|offshore|onshore|bảo trì|"
    r"maintenance|inspection|kiểm tra|lắp đặt|installation)",
    re.IGNORECASE,
)

_CONTINUATION_PHRASES = re.compile(
    r"(kể thêm|tiếp đi|chi tiết hơn|nói thêm|giải thích thêm|"
    r"tell me more|go on|elaborate|continue|more detail)",
    re.IGNORECASE,
)

_ANAPHORIC_REFS = re.compile(
    r"\b(nó|cái đó|loại này|loại đó|cái này|chúng|thế nào|"
    r"\bit\b|\bthat\b|\bthis one\b|\bthese\b|\bthose\b)",
    re.IGNORECASE,
)


def _is_standalone_question(message: str) -> bool:
    """Check if a follow-up message is already a standalone question.

    Returns True if the message can be used directly for retrieval
    without condensing with chat history.
    """
    msg = message.strip()
    length = len(msg)

    # Short messages are likely continuations
    if length < 20:
        return False

    # Explicit continuation phrases always need condense
    if _CONTINUATION_PHRASES.search(msg):
        return False

    # Anaphoric references need context
    if _ANAPHORIC_REFS.search(msg):
        return False

    # Long messages are usually standalone
    if length > 50:
        return True

    # Medium length + technical keywords = standalone
    if length > 30 and _TECHNICAL_KEYWORDS.search(msg):
        return True

    return False
```

- [ ] **Step 2: Use standalone detection in stream_chat**

In `WindBotChatEngine.stream_chat()`, replace the follow-up condense block. Change:

```python
        else:
            # Follow-up — condense to standalone question
            condensed = self._condense_question(memory_history, message)
            logger.info("Condensed question: %s", condensed[:100])
```

To:

```python
        else:
            # Follow-up — skip condense if message is already standalone
            if _is_standalone_question(message):
                condensed = message
                logger.info("Smart condense: skipped (standalone question)")
            else:
                condensed = self._condense_question(memory_history, message)
                logger.info("Condensed question: %s", condensed[:100])
```

- [ ] **Step 3: Verify syntax**

Run:
```bash
python3 -c "import py_compile; py_compile.compile('app/services/windbot_engine.py', doraise=True); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/windbot_engine.py
git commit -m "perf: smart condense — skip LLM call for standalone follow-up questions"
```

---

### Task 3: Pre-compute Original Query Search

**Files:**
- Modify: `backend/app/routers/chat.py` (lines 199-300)
- Modify: `backend/app/services/advanced_retriever.py` (lines 44-68, 234-265)

- [ ] **Step 1: Add prefetched_results support to AdvancedRetriever**

In `backend/app/services/advanced_retriever.py`, add a method to accept prefetched results and a field to store them:

In `__init__`, after `self._bm25_searcher = ...` line, add:

```python
        # Prefetched results for the original query (set externally)
        self._prefetched_dense = None
        self._prefetched_bm25 = None
```

Add a new method after `_safe_bm25_search`:

```python
    def set_prefetched_results(
        self, dense_results: list[NodeWithScore], bm25_results: list[NodeWithScore]
    ):
        """Set pre-computed search results for the original query."""
        self._prefetched_dense = dense_results
        self._prefetched_bm25 = bm25_results
```

In `_retrieve()`, modify Phase A to use prefetched results when available. Replace the Phase A dense/BM25 futures block:

```python
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            # Submit initial dense + BM25 searches (or use prefetched)
            if self._prefetched_dense is not None and len(initial_queries) >= 1:
                # Use prefetched results for original query
                dense_results_a = [self._prefetched_dense]
                bm25_results_a = [self._prefetched_bm25 or []]
                # If we have an expanded query, search it in parallel
                if len(initial_queries) > 1:
                    expanded_q = initial_queries[1]
                    d_fut = pool.submit(self._safe_dense_search, expanded_q, self._dense_top_k)
                    b_fut = pool.submit(self._safe_bm25_search, expanded_q, self._bm25_top_k)
                    dense_results_a.append(d_fut.result(timeout=15))
                    bm25_results_a.append(b_fut.result(timeout=15))
                # Clear prefetched (one-time use)
                self._prefetched_dense = None
                self._prefetched_bm25 = None
            else:
                dense_futures_a = {
                    q: pool.submit(self._safe_dense_search, q, self._dense_top_k)
                    for q in initial_queries
                }
                bm25_futures_a = {
                    q: pool.submit(self._safe_bm25_search, q, self._bm25_top_k)
                    for q in initial_queries
                }
                dense_results_a = [
                    dense_futures_a[q].result(timeout=15) for q in initial_queries
                ]
                bm25_results_a = [
                    bm25_futures_a[q].result(timeout=15) for q in initial_queries
                ]
```

Keep the rest of `_retrieve()` (mq_future, Phase B, etc.) unchanged.

- [ ] **Step 2: Start prefetch in chat.py**

In `backend/app/routers/chat.py`, add a prefetch function at module level (after the greeting helpers):

```python
from app.services.bm25_search import BM25Searcher


async def _prefetch_search(index, supabase: Client, message: str):
    """Pre-compute dense + BM25 search in parallel with classification."""
    def _do_search():
        retriever = index.as_retriever(similarity_top_k=30)
        dense = retriever.retrieve(message)
        bm25 = BM25Searcher(supabase).search(message, top_k=30)
        return dense, bm25
    return await asyncio.to_thread(_do_search)
```

Then in the `chat()` handler, start the prefetch immediately after classification. Modify the `asyncio.gather` blocks to include prefetch. Replace the two existing gather blocks (lines 228-239) with:

```python
        # Start prefetch search immediately (parallel with save/load/classify)
        prefetch_task = _prefetch_search(index, supabase, request.message)

        if regex_confidence < CONFIDENCE_THRESHOLD:
            async def _classify_llm():
                return await asyncio.to_thread(
                    classifier.classify_llm, get_openai_client(), request.message
                )

            _, history, llm_type, prefetch_results = await asyncio.gather(
                save_message(supabase, session_id, "user", request.message),
                get_session_messages(supabase, session_id),
                _classify_llm(),
                prefetch_task,
            )
            question_type = llm_type
            classification_method = "llm"
        else:
            _, history, prefetch_results = await asyncio.gather(
                save_message(supabase, session_id, "user", request.message),
                get_session_messages(supabase, session_id),
                prefetch_task,
            )
```

Then after `chat_engine = get_chat_engine(...)`, pass the prefetched results to the retriever. Add:

```python
        # Inject prefetched search results into the retriever
        if hasattr(chat_engine, '_retriever') and hasattr(chat_engine._retriever, 'set_prefetched_results'):
            dense, bm25 = prefetch_results
            chat_engine._retriever.set_prefetched_results(dense, bm25)
```

- [ ] **Step 3: Verify syntax**

Run:
```bash
python3 -c "
import py_compile
py_compile.compile('app/routers/chat.py', doraise=True)
py_compile.compile('app/services/advanced_retriever.py', doraise=True)
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/chat.py backend/app/services/advanced_retriever.py
git commit -m "perf: pre-compute original query search in parallel with classification"
```

---

### Task 4: Embedding Cache

**Files:**
- Create: `backend/app/services/cached_embedding.py`
- Modify: `backend/app/services/rag.py` (line 154)

- [ ] **Step 1: Create CachedOpenAIEmbedding**

Create `backend/app/services/cached_embedding.py`:

```python
"""LRU-cached wrapper for OpenAI embeddings.

Avoids redundant API calls for the same query text. Caches
query embeddings only (not document embeddings, which are one-time
at ingest). Cache size 200 entries ≈ 300KB memory.
"""

import logging
from collections import OrderedDict
from typing import List

from llama_index.embeddings.openai import OpenAIEmbedding

logger = logging.getLogger(__name__)


class CachedOpenAIEmbedding(OpenAIEmbedding):
    """OpenAIEmbedding with an in-memory LRU cache for query embeddings."""

    _cache: OrderedDict = OrderedDict()
    _max_size: int = 200
    _hits: int = 0
    _misses: int = 0

    def __init__(self, *args, cache_size: int = 200, **kwargs):
        super().__init__(*args, **kwargs)
        # Use class-level cache shared across instances (singleton pattern)
        CachedOpenAIEmbedding._max_size = cache_size

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding with LRU cache."""
        cache = CachedOpenAIEmbedding._cache

        if query in cache:
            # Move to end (most recently used)
            cache.move_to_end(query)
            CachedOpenAIEmbedding._hits += 1
            return cache[query]

        # Cache miss — call OpenAI API
        CachedOpenAIEmbedding._misses += 1
        embedding = super()._get_query_embedding(query)

        # Store in cache, evict oldest if full
        cache[query] = embedding
        if len(cache) > CachedOpenAIEmbedding._max_size:
            cache.popitem(last=False)

        if (CachedOpenAIEmbedding._hits + CachedOpenAIEmbedding._misses) % 50 == 0:
            total = CachedOpenAIEmbedding._hits + CachedOpenAIEmbedding._misses
            logger.info(
                "Embedding cache: %d hits, %d misses (%.0f%% hit rate)",
                CachedOpenAIEmbedding._hits,
                CachedOpenAIEmbedding._misses,
                100 * CachedOpenAIEmbedding._hits / total if total else 0,
            )

        return embedding
```

- [ ] **Step 2: Use CachedOpenAIEmbedding in rag.py settings**

In `backend/app/services/rag.py`, change the import and the `configure_settings()` function. Add import:

```python
from app.services.cached_embedding import CachedOpenAIEmbedding
```

In `configure_settings()`, replace:

```python
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
```

With:

```python
    Settings.embed_model = CachedOpenAIEmbedding(model="text-embedding-3-small", cache_size=200)
```

- [ ] **Step 3: Verify syntax**

Run:
```bash
python3 -c "
import py_compile
py_compile.compile('app/services/cached_embedding.py', doraise=True)
py_compile.compile('app/services/rag.py', doraise=True)
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/cached_embedding.py backend/app/services/rag.py
git commit -m "perf: add LRU embedding cache to avoid redundant OpenAI API calls"
```

---

### Task 5: Final Verification and Push

- [ ] **Step 1: Full syntax check**

```bash
python3 -c "
import py_compile
files = [
    'app/services/advanced_retriever.py',
    'app/services/windbot_engine.py',
    'app/services/rag.py',
    'app/services/cached_embedding.py',
    'app/routers/chat.py',
]
for f in files:
    py_compile.compile(f, doraise=True)
    print(f'OK: {f}')
"
```

- [ ] **Step 2: Push to master**

```bash
git push origin lyeoeon1/add-glossary-search-v3:master
```

- [ ] **Step 3: Deploy and benchmark on VPS**

```bash
# On VPS:
su - botai -c "cd ~/botai/repo && git pull"
sudo systemctl restart botai-backend

# Wait for startup, then benchmark:
su - botai
cd ~/botai/repo/backend && source venv/bin/activate
python -c "
import time, os, logging
logging.basicConfig(level=logging.INFO)
os.environ['OPENAI_API_KEY'] = open('.env').read().split('OPENAI_API_KEY=')[1].split('\n')[0]
from app.services.reranker import create_reranker
from app.services.advanced_retriever import AdvancedRetriever
from app.services.rag import create_vector_store, create_index, configure_settings
from app.services.query_expansion import GlossaryExpander
from app.config import settings
from supabase import create_client
configure_settings()
vs = create_vector_store(settings.supabase_connection_string)
idx = create_index(vs)
sb = create_client(settings.supabase_url, settings.supabase_service_key)
gl = GlossaryExpander()
rr = create_reranker(os.path.join(os.path.dirname(os.path.abspath('app')), 'models/reranker-int8'), 4)

# Test STRUCTURE (should skip multi-query)
ar = AdvancedRetriever(index=idx, supabase_client=sb, glossary_expander=gl, reranker=rr,
    dense_top_k=settings.dense_top_k, bm25_top_k=settings.bm25_top_k,
    rerank_top_k=settings.rerank_top_k, enable_hyde=settings.enable_hyde,
    multi_query_count=settings.multi_query_count, question_type='STRUCTURE')
from llama_index.core.schema import QueryBundle
nodes = ar._retrieve(QueryBundle('Cấu tạo chính của tuabin gió gồm những gì?'))
print(f'STRUCTURE: {len(nodes)} nodes')

# Test COMPARISON (should keep multi-query)
ar2 = AdvancedRetriever(index=idx, supabase_client=sb, glossary_expander=gl, reranker=rr,
    dense_top_k=settings.dense_top_k, bm25_top_k=settings.bm25_top_k,
    rerank_top_k=settings.rerank_top_k, enable_hyde=settings.enable_hyde,
    multi_query_count=settings.multi_query_count, question_type='COMPARISON')
nodes2 = ar2._retrieve(QueryBundle('So sánh tuabin trục ngang và trục đứng'))
print(f'COMPARISON: {len(nodes2)} nodes')
"
```

Expected:
- STRUCTURE: ~2-3s retrieval (no multi-query), 8-13 nodes
- COMPARISON: ~5-6s retrieval (with multi-query), 13 nodes
