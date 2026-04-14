"""Advanced Retriever: orchestrates the full retrieval pipeline.

Implements LlamaIndex's BaseRetriever interface so it plugs directly
into CondensePlusContextChatEngine. The pipeline:

1. Query Expansion (glossary synonyms, <1ms)
2. Multi-Query + HyDE Generation (parallel LLM calls, ~800ms)
3. Dense + BM25 Search (parallel per query variant, ~100ms)
4. RRF Fusion (merge + dedup, <5ms)
5. Cross-encoder Reranking (FlashRank, ~50ms)

Total added latency: ~1-2s (acceptable for chatbot UX).
"""

import asyncio
import logging
from typing import Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from openai import OpenAI
from supabase import Client as SupabaseClient

from app.services.bm25_search import BM25Searcher
from app.services.hybrid_search import merge_multi_query_results, reciprocal_rank_fusion
from app.services.query_expansion import GlossaryExpander
from app.services.query_generation import generate_query_variants
from app.services.reranker import FlashReranker

logger = logging.getLogger(__name__)


class AdvancedRetriever(BaseRetriever):
    """Full pipeline retriever with hybrid search, reranking, and query expansion.

    This retriever replaces the default VectorStoreIndex retriever.
    It implements _retrieve() (sync) which is called by the chat engine.
    """

    def __init__(
        self,
        index: VectorStoreIndex,
        supabase_client: SupabaseClient,
        glossary_expander: Optional[GlossaryExpander] = None,
        reranker: Optional[FlashReranker] = None,
        openai_client: Optional[OpenAI] = None,
        # Feature toggles
        enable_multi_query: bool = True,
        enable_hyde: bool = True,
        enable_bm25: bool = True,
        enable_reranking: bool = True,
        enable_glossary_expansion: bool = True,
        # Tuning parameters
        dense_top_k: int = 20,
        bm25_top_k: int = 20,
        rerank_top_k: int = 8,
        dense_weight: float = 0.8,
        sparse_weight: float = 0.2,
        # Vietnamese document priority
        enable_vi_priority: bool = True,
        vi_priority_threshold: int = 3,
        vi_score_boost: float = 2.0,
        vi_rerank_fallback_score: float = 0.05,
    ):
        super().__init__()
        self._index = index
        self._supabase = supabase_client
        self._glossary = glossary_expander
        self._reranker = reranker
        self._openai = openai_client or OpenAI()

        # Feature toggles
        self._enable_multi_query = enable_multi_query
        self._enable_hyde = enable_hyde
        self._enable_bm25 = enable_bm25
        self._enable_reranking = enable_reranking
        self._enable_glossary = enable_glossary_expansion

        # Parameters
        self._dense_top_k = dense_top_k
        self._bm25_top_k = bm25_top_k
        self._rerank_top_k = rerank_top_k
        self._dense_weight = dense_weight
        self._sparse_weight = sparse_weight

        # Vietnamese priority
        self._enable_vi_priority = enable_vi_priority
        self._vi_threshold = vi_priority_threshold
        self._vi_boost = vi_score_boost
        self._vi_fallback_score = vi_rerank_fallback_score

        # Initialize sub-components
        self._bm25_searcher = BM25Searcher(supabase_client) if enable_bm25 else None

    @staticmethod
    def _apply_vi_priority(
        candidates: list[NodeWithScore],
        vi_threshold: int = 3,
        vi_boost: float = 2.0,
    ) -> tuple[list[NodeWithScore], bool]:
        """Apply Vietnamese document priority.

        If enough VN chunks exist among candidates, drop all EN chunks
        (VN-only mode). Otherwise, boost VN chunk scores so they rank higher.

        Returns:
            (filtered_candidates, vi_only_mode)
        """
        vi_chunks = [n for n in candidates if n.node.metadata.get("language") == "vi"]
        en_chunks = [n for n in candidates if n.node.metadata.get("language") != "vi"]

        if len(vi_chunks) >= vi_threshold:
            logger.info(
                "VI priority: VN-only mode (%d VN chunks, dropped %d EN)",
                len(vi_chunks), len(en_chunks),
            )
            return vi_chunks, True
        elif vi_chunks:
            boosted = [
                NodeWithScore(node=n.node, score=n.score * vi_boost)
                for n in vi_chunks
            ]
            mixed = sorted(boosted + en_chunks, key=lambda n: n.score, reverse=True)
            logger.info(
                "VI priority: mixed mode (%d VN boosted %.1fx, %d EN kept)",
                len(vi_chunks), vi_boost, len(en_chunks),
            )
            return mixed, False
        else:
            logger.info("VI priority: no VN chunks found, using all %d candidates", len(candidates))
            return candidates, False

    @staticmethod
    def _is_qa_chunk(node_ws: NodeWithScore) -> bool:
        """Check if a node is from the AI-generated QA corpus."""
        filename = (node_ws.node.metadata.get("filename") or "").lower()
        if filename.startswith("qa"):
            return True
        content = node_ws.node.get_content()[:50].strip()
        if content.startswith("Q:") or content.startswith("Q :"):
            return True
        return False

    def _dense_search(self, query: str, top_k: int) -> list[NodeWithScore]:
        """Execute dense vector search via the existing VectorStoreIndex."""
        retriever = self._index.as_retriever(similarity_top_k=top_k)
        return retriever.retrieve(query)

    def _dense_search_multiple(
        self, queries: list[str], top_k: int
    ) -> list[list[NodeWithScore]]:
        """Execute dense search for multiple queries."""
        results = []
        for q in queries:
            try:
                results.append(self._dense_search(q, top_k))
            except Exception as e:
                logger.warning("Dense search failed for '%s': %s", q[:50], e)
                results.append([])
        return results

    def _bm25_search_multiple(
        self, queries: list[str], top_k: int
    ) -> list[list[NodeWithScore]]:
        """Execute BM25 search for multiple queries."""
        if not self._bm25_searcher:
            return [[] for _ in queries]
        results = []
        for q in queries:
            try:
                results.append(self._bm25_searcher.search(q, top_k=top_k))
            except Exception as e:
                logger.warning("BM25 search failed for '%s': %s", q[:50], e)
                results.append([])
        return results

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Synchronous retrieval — called by CondensePlusContextChatEngine.

        This is the main entry point. Since the chat engine calls this
        synchronously, we use asyncio.run() for the async pipeline
        (multi-query + HyDE generation).
        """
        query = query_bundle.query_str
        logger.info("AdvancedRetriever: processing '%s'", query[:80])

        # ── Step 1: Query Expansion (sync, <1ms) ──────────────────────
        expanded_query = query
        if self._enable_glossary and self._glossary:
            expanded_query = self._glossary.expand(query)
            if expanded_query != query:
                logger.debug("Glossary expanded: '%s'", expanded_query[:100])

        # ── Step 2: Multi-Query + HyDE (async, ~800ms) ───────────────
        multi_queries = []
        hyde_doc = ""

        if self._enable_multi_query or self._enable_hyde:
            try:
                # Try to use existing event loop, fallback to new one
                try:
                    loop = asyncio.get_running_loop()
                    # We're inside an event loop — use thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            generate_query_variants(
                                self._openai, query,
                                enable_multi_query=self._enable_multi_query,
                                enable_hyde=self._enable_hyde,
                            )
                        )
                        multi_queries, hyde_doc = future.result(timeout=10)
                except RuntimeError:
                    # No event loop running — safe to use asyncio.run()
                    multi_queries, hyde_doc = asyncio.run(
                        generate_query_variants(
                            self._openai, query,
                            enable_multi_query=self._enable_multi_query,
                            enable_hyde=self._enable_hyde,
                        )
                    )
            except Exception as e:
                logger.warning("Query variant generation failed: %s", e)

        # ── Step 3: Collect all query variants ────────────────────────
        all_queries = [query]
        if expanded_query != query:
            all_queries.append(expanded_query)
        all_queries.extend(multi_queries)
        if hyde_doc:
            all_queries.append(hyde_doc)

        logger.debug(
            "Total query variants: %d (original + %d expanded + %d multi + %d hyde)",
            len(all_queries),
            1 if expanded_query != query else 0,
            len(multi_queries),
            1 if hyde_doc else 0,
        )

        # ── Step 4: Dense + BM25 Search (per variant) ────────────────
        dense_per_query = self._dense_search_multiple(all_queries, self._dense_top_k)
        bm25_per_query = self._bm25_search_multiple(all_queries, self._bm25_top_k)

        # ── Step 5: RRF Fusion ────────────────────────────────────────
        # First: merge dense + sparse per query using RRF
        hybrid_per_query = []
        for dense_results, bm25_results in zip(dense_per_query, bm25_per_query):
            if bm25_results:
                merged = reciprocal_rank_fusion(
                    dense_results, bm25_results,
                    dense_weight=self._dense_weight,
                    sparse_weight=self._sparse_weight,
                )
            else:
                merged = dense_results
            hybrid_per_query.append(merged)

        # Then: merge across all query variants
        candidates = merge_multi_query_results(hybrid_per_query, top_n=50)

        logger.debug("Pipeline candidates after RRF: %d", len(candidates))

        # ── Step 5.5: Filter QA corpus BEFORE reranking ──────────────
        # QA chunks (GPT-generated) always outscore original documents
        # in reranking. Filter them here so reranker scores only
        # authoritative source documents.
        pre_filter = len(candidates)
        candidates = [
            n for n in candidates
            if not self._is_qa_chunk(n)
        ]
        if len(candidates) < pre_filter:
            logger.info(
                "Filtered %d QA chunks before reranking, %d remaining",
                pre_filter - len(candidates),
                len(candidates),
            )

        # ── Step 5.6: Vietnamese document priority ──────────────────
        all_candidates_backup = list(candidates)
        vi_only_mode = False
        if self._enable_vi_priority:
            candidates, vi_only_mode = self._apply_vi_priority(
                candidates, self._vi_threshold, self._vi_boost,
            )

        # ── Step 6: Rerank ────────────────────────────────────────────
        if self._enable_reranking and self._reranker:
            # Use the ORIGINAL query for reranking (not expanded)
            final = self._reranker.rerank(query, candidates, top_k=self._rerank_top_k)
        else:
            final = candidates[:self._rerank_top_k]

        # Safety fallback: if VN-only mode produced very low relevance
        if (
            vi_only_mode
            and final
            and final[0].score < self._vi_fallback_score
            and self._enable_reranking
            and self._reranker
        ):
            logger.warning(
                "VI-only top score %.4f < threshold %.4f, falling back to all candidates",
                final[0].score, self._vi_fallback_score,
            )
            final = self._reranker.rerank(
                query, all_candidates_backup, top_k=self._rerank_top_k,
            )

        logger.info(
            "AdvancedRetriever: returned %d nodes (from %d candidates)",
            len(final),
            len(candidates),
        )
        return final
