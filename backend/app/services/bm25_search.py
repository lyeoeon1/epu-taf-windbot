"""BM25-style keyword search via Supabase full-text search.

Queries the chunk_fts table using PostgreSQL's tsvector/tsquery for
keyword matching. This catches exact term matches that dense vector
search may miss — especially for technical terms, abbreviations,
model numbers, and cross-lingual vocabulary.

Results are returned as LlamaIndex NodeWithScore objects so they
integrate seamlessly with the existing postprocessor chain.
"""

import logging
from typing import Optional

from llama_index.core.schema import NodeWithScore, TextNode
from supabase import Client

logger = logging.getLogger(__name__)


class BM25Searcher:
    """Perform BM25 keyword search via Supabase RPC.

    Uses the search_chunks_fts() database function which leverages
    PostgreSQL's tsvector with 'simple' configuration for bilingual
    (VN+EN) content.
    """

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    def search(
        self,
        query: str,
        top_k: int = 20,
    ) -> list[NodeWithScore]:
        """Execute BM25 search and return results as NodeWithScore.

        Args:
            query: Search query (natural language, handled by websearch_to_tsquery).
            top_k: Maximum number of results to return.

        Returns:
            List of NodeWithScore objects sorted by BM25 rank (descending).
            Returns empty list if no matches or on error.
        """
        if not query or not query.strip():
            return []

        try:
            response = self._client.rpc(
                "search_chunks_fts",
                {"query_text": query, "match_count": top_k},
            ).execute()

            if not response.data:
                return []

            nodes = []
            for row in response.data:
                node = TextNode(
                    id_=row["chunk_id"],
                    text=row["content"] or "",
                    metadata={
                        "filename": row.get("filename", ""),
                        "page": row.get("page"),
                        "language": row.get("language", "vi"),
                        "domain": "wind_turbine",
                        "search_type": "bm25",
                    },
                )
                # ts_rank returns a float; normalize to 0-1 range approximately
                rank = float(row.get("rank", 0))
                nodes.append(NodeWithScore(node=node, score=rank))

            logger.debug(
                "BM25 search for '%s': %d results (top score=%.4f)",
                query[:50],
                len(nodes),
                nodes[0].score if nodes else 0,
            )
            return nodes

        except Exception as e:
            logger.warning("BM25 search failed for '%s': %s", query[:50], e)
            return []

    def search_multiple(
        self,
        queries: list[str],
        top_k: int = 20,
    ) -> list[NodeWithScore]:
        """Execute BM25 search for multiple queries and merge results.

        Args:
            queries: List of search queries.
            top_k: Maximum results per query.

        Returns:
            Combined list of NodeWithScore (may contain duplicates —
            deduplication is handled by the hybrid search layer).
        """
        all_results = []
        for query in queries:
            results = self.search(query, top_k=top_k)
            all_results.extend(results)
        return all_results
