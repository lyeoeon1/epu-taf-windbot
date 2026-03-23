"""Automated RAG benchmark evaluation using GPT as judge.

Usage:
    cd backend
    python scripts/evaluate_rag.py \
        --input ./data/qa_corpus/benchmark-windbot-v1.json \
        --output ./data/qa_corpus/eval_results.json \
        --sample 10
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.rag import configure_settings, create_index, create_vector_store, get_chat_engine  # noqa: E402

JUDGE_PROMPT = """\
You are an expert evaluator for a wind turbine knowledge chatbot.
Compare the chatbot's actual answer with the expected answer and score on 5 dimensions.

Question: {question}
Expected Answer: {expected_answer}
Actual Answer: {actual_answer}
Scoring Criteria: {scoring_criteria}

Score each dimension from 1 to 5:
- accuracy: How factually correct is the answer compared to expected?
- completeness: Does it cover all key points from expected answer?
- relevance: Does it address the question directly?
- clarity: Is the answer clear and well-structured?
- tone: Is it professional and appropriate for a technical assistant?

Return ONLY a JSON object with these 5 keys and integer values 1-5. Example:
{{"accuracy": 4, "completeness": 3, "relevance": 5, "clarity": 4, "tone": 5}}"""


def judge_answer(client: OpenAI, question: str, expected: str, actual: str, criteria: str) -> dict:
    """Use GPT to judge the chatbot's answer."""
    prompt = JUDGE_PROMPT.format(
        question=question,
        expected_answer=expected,
        actual_answer=actual,
        scoring_criteria=criteria,
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def get_chatbot_answer(index, question: str, language: str = "vi") -> str:
    """Get answer from the RAG chatbot."""
    chat_engine = get_chat_engine(index, language=language, has_history=False)
    response = chat_engine.chat(question)
    return str(response)


async def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG benchmark")
    parser.add_argument("--input", required=True, help="JSON benchmark file")
    parser.add_argument("--output", required=True, help="Output JSON results file")
    parser.add_argument("--sample", type=int, default=0, help="Sample N questions (0=all)")
    parser.add_argument("--language", default="vi", choices=["en", "vi"])
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Collect all Q&A pairs
    all_pairs = []
    for cat in data.get("categories", []):
        for pair in cat.get("pairs", []):
            pair["_category"] = cat["name"]
            all_pairs.append(pair)

    if args.sample > 0 and args.sample < len(all_pairs):
        all_pairs = random.sample(all_pairs, args.sample)

    print(f"Evaluating {len(all_pairs)} questions...")

    # Initialize RAG
    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)
    index = create_index(vector_store)
    client = OpenAI(api_key=settings.openai_api_key)

    results = []
    totals = {"accuracy": 0, "completeness": 0, "relevance": 0, "clarity": 0, "tone": 0}
    category_scores: dict[str, dict] = {}

    for i, pair in enumerate(all_pairs):
        qid = pair["id"]
        question = pair["question"]
        expected = pair["expected_answer"]
        criteria = pair.get("scoring_criteria", "")
        category = pair["_category"]

        print(f"  [{i+1}/{len(all_pairs)}] Q{qid}: {question[:60]}...", end=" ", flush=True)

        try:
            actual = await get_chatbot_answer(index, question, args.language)
            scores = judge_answer(client, question, expected, actual, criteria)

            result = {
                "qa_id": qid,
                "category": category,
                "question": question,
                "expected_answer": expected,
                "actual_answer": actual,
                "difficulty": pair.get("difficulty", ""),
                "scores": scores,
            }
            results.append(result)

            for dim in totals:
                val = scores.get(dim, 0)
                totals[dim] += val

            if category not in category_scores:
                category_scores[category] = {"count": 0, **{d: 0 for d in totals}}
            category_scores[category]["count"] += 1
            for dim in totals:
                category_scores[category][dim] += scores.get(dim, 0)

            avg = sum(scores.values()) / len(scores)
            print(f"avg={avg:.1f}")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "qa_id": qid, "category": category, "question": question,
                "error": str(e),
            })

        time.sleep(0.5)  # Rate limiting

    # Compute summary
    n = len([r for r in results if "scores" in r])
    summary = {}
    if n > 0:
        summary = {
            "total_evaluated": n,
            "overall": {dim: round(totals[dim] / n, 2) for dim in totals},
            "overall_average": round(sum(totals.values()) / (n * len(totals)), 2),
            "by_category": {},
        }
        for cat, scores in category_scores.items():
            c = scores["count"]
            summary["by_category"][cat] = {
                "count": c,
                **{dim: round(scores[dim] / c, 2) for dim in totals},
                "average": round(sum(scores[dim] for dim in totals) / (c * len(totals)), 2),
            }

    output = {
        "source": data.get("source_file", ""),
        "summary": summary,
        "results": results,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    if summary:
        print(f"Total evaluated: {summary['total_evaluated']}")
        print(f"Overall average: {summary['overall_average']}/5")
        print()
        print(f"{'Category':<30} {'Acc':>5} {'Comp':>5} {'Rel':>5} {'Clr':>5} {'Tone':>5} {'Avg':>5}")
        print("-" * 70)
        for cat, s in summary["by_category"].items():
            print(f"{cat:<30} {s['accuracy']:>5.1f} {s['completeness']:>5.1f} "
                  f"{s['relevance']:>5.1f} {s['clarity']:>5.1f} {s['tone']:>5.1f} {s['average']:>5.1f}")
        print("-" * 70)
        o = summary["overall"]
        print(f"{'OVERALL':<30} {o['accuracy']:>5.1f} {o['completeness']:>5.1f} "
              f"{o['relevance']:>5.1f} {o['clarity']:>5.1f} {o['tone']:>5.1f} "
              f"{summary['overall_average']:>5.1f}")

        verdict = "Xuất sắc" if summary["overall_average"] >= 4.5 else \
                  "Tốt" if summary["overall_average"] >= 4.0 else \
                  "Đạt yêu cầu" if summary["overall_average"] >= 3.5 else \
                  "Chưa đạt" if summary["overall_average"] >= 3.0 else "Không đạt"
        print(f"\nVerdict: {verdict} ({summary['overall_average']}/5)")

    print(f"\nResults saved to {args.output}")

    # Generate Markdown report
    md_output = args.output.replace(".json", "_report.md")
    with open(md_output, "w", encoding="utf-8") as f:
        f.write("# WINDBOT RAG Evaluation Report\n\n")
        f.write(f"- Source: {data.get('source_file', '')}\n")
        f.write(f"- Total evaluated: {summary.get('total_evaluated', 0)}\n")
        f.write(f"- Overall average: {summary.get('overall_average', 0)}/5\n\n")
        if summary:
            f.write("| Category | Accuracy | Completeness | Relevance | Clarity | Tone | Average |\n")
            f.write("|----------|----------|-------------|-----------|---------|------|---------|\n")
            for cat, s in summary.get("by_category", {}).items():
                f.write(f"| {cat} | {s['accuracy']:.1f} | {s['completeness']:.1f} | "
                        f"{s['relevance']:.1f} | {s['clarity']:.1f} | {s['tone']:.1f} | {s['average']:.1f} |\n")
            o = summary["overall"]
            f.write(f"| **OVERALL** | **{o['accuracy']:.1f}** | **{o['completeness']:.1f}** | "
                    f"**{o['relevance']:.1f}** | **{o['clarity']:.1f}** | **{o['tone']:.1f}** | "
                    f"**{summary['overall_average']:.1f}** |\n")
    print(f"Markdown report saved to {md_output}")


if __name__ == "__main__":
    asyncio.run(main())
