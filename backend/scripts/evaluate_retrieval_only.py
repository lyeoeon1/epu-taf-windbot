"""Evaluate retrieval quality: baseline vs advanced pipeline.

Compares the default dense-only retriever with the new AdvancedRetriever
using the 8 customer error questions from diagnose_retrieval.py.

Metrics measured:
- Recall@K: Whether the correct chunk appears in top K results
- Keyword Hit Rate: Whether expected keywords are found in retrieved chunks
- Mean Reciprocal Rank (MRR): Average position of first relevant result

Usage:
    cd backend
    pip install flashrank  # optional, for reranking
    python scripts/evaluate_retrieval_only.py
    python scripts/evaluate_retrieval_only.py --top-k 10
    python scripts/evaluate_retrieval_only.py --mode baseline   # Only baseline
    python scripts/evaluate_retrieval_only.py --mode advanced   # Only advanced
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llama_index.core.schema import QueryBundle  # noqa: E402
from supabase import create_client  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.query_expansion import GlossaryExpander  # noqa: E402
from app.services.rag import configure_settings, create_index, create_vector_store  # noqa: E402
from app.services.reranker import FlashReranker  # noqa: E402

# Import test questions from diagnose_retrieval (same directory)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "diagnose_retrieval",
    os.path.join(os.path.dirname(__file__), "diagnose_retrieval.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CUSTOMER_ERROR_QUESTIONS = _mod.CUSTOMER_ERROR_QUESTIONS

# Also test with additional retrieval-focused questions
RETRIEVAL_TEST_QUESTIONS = CUSTOMER_ERROR_QUESTIONS + [
    {
        "id": 9,
        "question": "Pitch to feather là gì và hoạt động như thế nào?",
        "error": "N/A - vocabulary mismatch test",
        "correct": "Pitch to feather = phanh khí động học, xoay cánh để giảm lực nâng",
        "keywords": ["pitch to feather", "aerodynamic", "brake", "phanh", "feather"],
    },
    {
        "id": 10,
        "question": "Mối quan hệ giữa momen xoắn và tốc độ quay trong hộp số",
        "error": "N/A - concept gap test",
        "correct": "Tỷ lệ nghịch: P = T × ω, tăng tốc → giảm momen",
        "keywords": ["torque", "speed", "inverse", "momen", "tỷ lệ nghịch", "gearbox"],
    },
]


def evaluate_retriever(retriever, questions, top_k):
    """Run evaluation for a retriever and return metrics."""
    results = []

    for q_info in questions:
        start = time.time()

        try:
            nodes = retriever.retrieve(q_info["question"])
        except Exception as e:
            print(f"  ERROR on Q#{q_info['id']}: {e}")
            results.append({
                "id": q_info["id"],
                "error": str(e),
                "keyword_hit": False,
                "first_hit_rank": None,
                "num_results": 0,
                "latency_ms": 0,
            })
            continue

        elapsed_ms = (time.time() - start) * 1000

        # Check keyword presence in retrieved chunks
        keywords = q_info.get("keywords", [])
        first_hit_rank = None

        for i, node_ws in enumerate(nodes[:top_k]):
            text_lower = node_ws.node.get_content().lower()
            for kw in keywords:
                if kw.lower() in text_lower:
                    if first_hit_rank is None:
                        first_hit_rank = i + 1
                    break

        keyword_hits_in_top5 = 0
        for node_ws in nodes[:5]:
            text_lower = node_ws.node.get_content().lower()
            if any(kw.lower() in text_lower for kw in keywords):
                keyword_hits_in_top5 += 1

        results.append({
            "id": q_info["id"],
            "question": q_info["question"][:60],
            "keyword_hit": first_hit_rank is not None,
            "first_hit_rank": first_hit_rank,
            "keyword_hits_in_top5": keyword_hits_in_top5,
            "num_results": len(nodes),
            "top_score": round(nodes[0].score, 4) if nodes and nodes[0].score else None,
            "latency_ms": round(elapsed_ms),
        })

        status = f"rank #{first_hit_rank}" if first_hit_rank else "MISS"
        print(f"  Q#{q_info['id']}: {status} ({elapsed_ms:.0f}ms, {len(nodes)} results)")

    return results


def compute_metrics(results):
    """Compute aggregate metrics from evaluation results."""
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {}

    hits = sum(1 for r in valid if r["keyword_hit"])
    recall = hits / len(valid)

    # MRR
    mrr_sum = sum(
        1.0 / r["first_hit_rank"]
        for r in valid
        if r["first_hit_rank"] is not None
    )
    mrr = mrr_sum / len(valid)

    # Average hits in top 5
    avg_hits_top5 = sum(r.get("keyword_hits_in_top5", 0) for r in valid) / len(valid)

    # Average latency
    avg_latency = sum(r["latency_ms"] for r in valid) / len(valid)

    return {
        "total_questions": len(valid),
        "recall": round(recall, 3),
        "mrr": round(mrr, 3),
        "avg_keyword_hits_top5": round(avg_hits_top5, 2),
        "avg_latency_ms": round(avg_latency),
        "misses": [r["id"] for r in valid if not r["keyword_hit"]],
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality")
    parser.add_argument("--top-k", type=int, default=10, help="Top K for evaluation")
    parser.add_argument(
        "--mode", choices=["both", "baseline", "advanced"], default="both",
        help="Which retriever(s) to evaluate",
    )
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    args = parser.parse_args()

    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)
    index = create_index(vector_store)

    questions = RETRIEVAL_TEST_QUESTIONS
    all_results = {}

    # ── Baseline: Dense-only retriever ──────────────────────────
    if args.mode in ("both", "baseline"):
        print(f"\n{'='*60}")
        print(f"BASELINE: Dense-only retriever (top_k={args.top_k})")
        print(f"{'='*60}")

        baseline_retriever = index.as_retriever(similarity_top_k=args.top_k)
        baseline_results = evaluate_retriever(baseline_retriever, questions, args.top_k)
        baseline_metrics = compute_metrics(baseline_results)

        print(f"\nBaseline Metrics:")
        print(f"  Recall@{args.top_k}: {baseline_metrics.get('recall', 'N/A')}")
        print(f"  MRR: {baseline_metrics.get('mrr', 'N/A')}")
        print(f"  Avg keyword hits in top 5: {baseline_metrics.get('avg_keyword_hits_top5', 'N/A')}")
        print(f"  Avg latency: {baseline_metrics.get('avg_latency_ms', 'N/A')}ms")
        if baseline_metrics.get("misses"):
            print(f"  Misses: Q#{baseline_metrics['misses']}")

        all_results["baseline"] = {
            "metrics": baseline_metrics,
            "details": baseline_results,
        }

    # ── Advanced: Full pipeline retriever ───────────────────────
    if args.mode in ("both", "advanced"):
        print(f"\n{'='*60}")
        print(f"ADVANCED: Full pipeline retriever")
        print(f"{'='*60}")

        from app.services.advanced_retriever import AdvancedRetriever  # noqa: E402

        supabase_client = create_client(
            settings.supabase_url, settings.supabase_service_key
        )
        glossary = GlossaryExpander()
        reranker = FlashReranker()

        advanced_retriever = AdvancedRetriever(
            index=index,
            supabase_client=supabase_client,
            glossary_expander=glossary,
            reranker=reranker,
            enable_multi_query=settings.enable_multi_query,
            enable_hyde=settings.enable_hyde,
            enable_bm25=settings.enable_bm25,
            enable_reranking=settings.enable_reranking,
            enable_glossary_expansion=settings.enable_glossary_expansion,
            dense_top_k=settings.dense_top_k,
            bm25_top_k=settings.bm25_top_k,
            rerank_top_k=settings.rerank_top_k,
        )

        advanced_results = evaluate_retriever(advanced_retriever, questions, args.top_k)
        advanced_metrics = compute_metrics(advanced_results)

        print(f"\nAdvanced Metrics:")
        print(f"  Recall@{args.top_k}: {advanced_metrics.get('recall', 'N/A')}")
        print(f"  MRR: {advanced_metrics.get('mrr', 'N/A')}")
        print(f"  Avg keyword hits in top 5: {advanced_metrics.get('avg_keyword_hits_top5', 'N/A')}")
        print(f"  Avg latency: {advanced_metrics.get('avg_latency_ms', 'N/A')}ms")
        if advanced_metrics.get("misses"):
            print(f"  Misses: Q#{advanced_metrics['misses']}")

        all_results["advanced"] = {
            "metrics": advanced_metrics,
            "details": advanced_results,
        }

    # ── Comparison ──────────────────────────────────────────────
    if args.mode == "both" and "baseline" in all_results and "advanced" in all_results:
        bm = all_results["baseline"]["metrics"]
        am = all_results["advanced"]["metrics"]

        print(f"\n{'='*60}")
        print(f"COMPARISON")
        print(f"{'='*60}")
        print(f"{'Metric':<30} {'Baseline':>10} {'Advanced':>10} {'Delta':>10}")
        print(f"{'-'*60}")

        for key in ["recall", "mrr", "avg_keyword_hits_top5", "avg_latency_ms"]:
            bv = bm.get(key, 0)
            av = am.get(key, 0)
            delta = av - bv
            sign = "+" if delta > 0 else ""
            print(f"{key:<30} {bv:>10} {av:>10} {sign}{delta:>9}")

    # Save results
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
