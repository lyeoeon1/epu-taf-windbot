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
        CachedOpenAIEmbedding._max_size = cache_size

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding with LRU cache."""
        cache = CachedOpenAIEmbedding._cache

        if query in cache:
            cache.move_to_end(query)
            CachedOpenAIEmbedding._hits += 1
            return cache[query]

        CachedOpenAIEmbedding._misses += 1
        embedding = super()._get_query_embedding(query)

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
