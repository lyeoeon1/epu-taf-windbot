"""Hybrid Search with Reciprocal Rank Fusion (RRF).

Merges results from dense vector search and BM25 keyword search using
Reciprocal Rank Fusion. RRF combines rankings from multiple retrieval
methods without requiring score normalization — each document's final
score is the sum of 1/(k + rank) across all result lists.

Default weights: dense 80% / sparse 20% (following Anthropic's 4:1 ratio).

Reference: Cormack, Clarke & Butt (2009) — "Reciprocal Rank Fusion
outperforms Condorcet and individual Rank Learning Methods"
"""

import logging
from collections import defaultdict

from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)


def _get_node_id(node_ws: NodeWithScore) -> str:
    """Extract a stable ID from a NodeWithScore for deduplication."""
    return node_ws.node.node_id or node_ws.node.id_


def reciprocal_rank_fusion(
    dense_results: list[NodeWithScore],
    sparse_results: list[NodeWithScore],
    k: int = 60,
    dense_weight: float = 0.8,
    sparse_weight: float = 0.2,
    top_n: int = 50,
) -> list[NodeWithScore]:
    """Merge dense and sparse search results using Reciprocal Rank Fusion.

    Args:
        dense_results: Results from vector similarity search (ordered by score).
        sparse_results: Results from BM25 keyword search (ordered by rank).
        k: RRF constant (default 60, standard in literature).
            Higher k reduces the impact of high-ranked documents.
        dense_weight: Weight for dense search results (default 0.8).
        sparse_weight: Weight for sparse search results (default 0.2).
        top_n: Maximum number of results to return.

    Returns:
        List of NodeWithScore sorted by RRF score (descending).
        Each node's score is replaced with its RRF fusion score.
    """
    # Accumulate RRF scores per chunk
    rrf_scores: dict[str, float] = defaultdict(float)
    node_map: dict[str, NodeWithScore] = {}

    # Process dense results
    for rank, node_ws in enumerate(dense_results):
        node_id = _get_node_id(node_ws)
        rrf_scores[node_id] += dense_weight * (1.0 / (k + rank + 1))
        if node_id not in node_map:
            node_map[node_id] = node_ws

    # Process sparse results
    for rank, node_ws in enumerate(sparse_results):
        node_id = _get_node_id(node_ws)
        rrf_scores[node_id] += sparse_weight * (1.0 / (k + rank + 1))
        if node_id not in node_map:
            node_map[node_id] = node_ws

    # Sort by RRF score descending
    sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

    # Build result list with RRF scores
    results = []
    for node_id in sorted_ids[:top_n]:
        node_ws = node_map[node_id]
        # Replace original score with RRF fusion score
        results.append(NodeWithScore(
            node=node_ws.node,
            score=rrf_scores[node_id],
        ))

    logger.debug(
        "RRF fusion: %d dense + %d sparse → %d merged (top score=%.6f)",
        len(dense_results),
        len(sparse_results),
        len(results),
        results[0].score if results else 0,
    )
    return results


def merge_multi_query_results(
    result_lists: list[list[NodeWithScore]],
    top_n: int = 50,
) -> list[NodeWithScore]:
    """Merge results from multiple query variants using RRF.

    Each query variant's result list is treated equally. Documents
    appearing in multiple lists get boosted scores.

    Args:
        result_lists: List of result lists (one per query variant).
        top_n: Maximum number of results to return.

    Returns:
        Deduplicated, RRF-scored results sorted by score descending.
    """
    if not result_lists:
        return []

    if len(result_lists) == 1:
        return result_lists[0][:top_n]

    k = 60
    weight = 1.0 / len(result_lists)  # Equal weight per query

    rrf_scores: dict[str, float] = defaultdict(float)
    node_map: dict[str, NodeWithScore] = {}

    for results in result_lists:
        for rank, node_ws in enumerate(results):
            node_id = _get_node_id(node_ws)
            rrf_scores[node_id] += weight * (1.0 / (k + rank + 1))
            if node_id not in node_map:
                node_map[node_id] = node_ws

    sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

    merged = []
    for node_id in sorted_ids[:top_n]:
        node_ws = node_map[node_id]
        merged.append(NodeWithScore(
            node=node_ws.node,
            score=rrf_scores[node_id],
        ))

    logger.debug(
        "Multi-query merge: %d lists → %d merged results",
        len(result_lists),
        len(merged),
    )
    return merged
