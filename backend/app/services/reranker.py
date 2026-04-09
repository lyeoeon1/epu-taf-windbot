"""Cross-encoder reranking using FlashRank.

After retrieval and RRF fusion produce ~30-50 candidate chunks, the
reranker uses a cross-encoder model to score each (query, chunk) pair
with deep semantic understanding. This dramatically improves precision
of the final top-K results.

FlashRank is chosen for CPU efficiency (~50ms per query on CPU).
Model: ms-marco-MiniLM-L-12-v2 (~80MB, good multilingual transfer).

Falls back gracefully if FlashRank is not installed — returns the
input nodes unchanged (sorted by existing scores).
"""

import logging
from typing import Optional

from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)

# Lazy import to allow graceful degradation
_flashrank_available = None


def _check_flashrank():
    global _flashrank_available
    if _flashrank_available is None:
        try:
            import flashrank  # noqa: F401
            _flashrank_available = True
        except ImportError:
            _flashrank_available = False
            logger.warning(
                "flashrank not installed. Reranking disabled. "
                "Install with: pip install flashrank"
            )
    return _flashrank_available


class FlashReranker:
    """Rerank retrieved chunks using FlashRank cross-encoder.

    The model is loaded once at initialization and reused for all queries.
    If FlashRank is not available, the reranker becomes a no-op passthrough.
    """

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        self._ranker = None
        self._model_name = model_name

        if _check_flashrank():
            try:
                from flashrank import Ranker
                self._ranker = Ranker(model_name=model_name)
                logger.info("FlashReranker initialized with model: %s", model_name)
            except Exception as e:
                logger.warning("Failed to initialize FlashReranker: %s", e)

    @property
    def is_available(self) -> bool:
        """Whether the reranker model is loaded and ready."""
        return self._ranker is not None

    def rerank(
        self,
        query: str,
        nodes: list[NodeWithScore],
        top_k: int = 8,
    ) -> list[NodeWithScore]:
        """Rerank nodes using cross-encoder scoring.

        Args:
            query: Original user query (NOT expanded — use the raw query
                   for reranking to get the most accurate relevance scores).
            nodes: Candidate nodes from hybrid search.
            top_k: Number of top results to return after reranking.

        Returns:
            Top-K nodes sorted by reranker score (descending).
            If reranker is unavailable, returns input nodes truncated to top_k.
        """
        if not nodes:
            return []

        if not self.is_available:
            logger.debug("Reranker unavailable, returning top %d by existing score", top_k)
            return sorted(nodes, key=lambda n: n.score or 0, reverse=True)[:top_k]

        try:
            from flashrank import RerankRequest

            # Build rerank request
            passages = []
            for node_ws in nodes:
                passages.append({
                    "id": node_ws.node.node_id or node_ws.node.id_,
                    "text": node_ws.node.get_content(),
                    "meta": node_ws.node.metadata,
                })

            request = RerankRequest(query=query, passages=passages)
            ranked = self._ranker.rerank(request)

            # Map reranked results back to NodeWithScore
            node_by_id = {
                (n.node.node_id or n.node.id_): n
                for n in nodes
            }

            reranked_nodes = []
            for result in ranked[:top_k]:
                node_id = result["id"]
                if node_id in node_by_id:
                    original_node = node_by_id[node_id]
                    reranked_nodes.append(NodeWithScore(
                        node=original_node.node,
                        score=float(result["score"]),
                    ))

            logger.debug(
                "Reranked %d → %d nodes (top score=%.4f)",
                len(nodes),
                len(reranked_nodes),
                reranked_nodes[0].score if reranked_nodes else 0,
            )
            return reranked_nodes

        except Exception as e:
            logger.warning("Reranking failed: %s. Falling back to score-based sort.", e)
            return sorted(nodes, key=lambda n: n.score or 0, reverse=True)[:top_k]
