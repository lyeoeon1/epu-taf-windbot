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

# Module-level cache — shared across all instances, survives Pydantic model init.
# Cannot use class-level attributes because OpenAIEmbedding is a Pydantic BaseModel
# and class attributes become ModelPrivateAttr, breaking `in` operator.
_embedding_cache: OrderedDict = OrderedDict()
_cache_max_size: int = 200
_cache_hits: int = 0
_cache_misses: int = 0


class CachedOpenAIEmbedding(OpenAIEmbedding):
    """OpenAIEmbedding with an in-memory LRU cache for query embeddings."""

    def __init__(self, *args, cache_size: int = 200, **kwargs):
        super().__init__(*args, **kwargs)
        global _cache_max_size
        _cache_max_size = cache_size

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding with LRU cache."""
        global _cache_hits, _cache_misses

        if query in _embedding_cache:
            _embedding_cache.move_to_end(query)
            _cache_hits += 1
            return _embedding_cache[query]

        _cache_misses += 1
        embedding = super()._get_query_embedding(query)

        _embedding_cache[query] = embedding
        if len(_embedding_cache) > _cache_max_size:
            _embedding_cache.popitem(last=False)

        if (_cache_hits + _cache_misses) % 50 == 0:
            total = _cache_hits + _cache_misses
            logger.info(
                "Embedding cache: %d hits, %d misses (%.0f%% hit rate)",
                _cache_hits, _cache_misses,
                100 * _cache_hits / total if total else 0,
            )

        return embedding
