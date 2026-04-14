# Quality Benchmark Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a regression benchmark that scores WindBot responses on 8 quality metrics (5 existing + 3 source faithfulness) and detects quality regressions against a saved baseline.

**Architecture:** Single new script `benchmark_runner.py` that runs the full RAG pipeline per question, collects response + source chunks, scores via GPT judge (8 metrics), compares with baseline snapshot, outputs JSON + Markdown report. Reuses existing infrastructure (evaluate_rag.py patterns, benchmark-windbot-v1.json dataset).

**Tech Stack:** Python 3.12, OpenAI GPT-4o-mini (judge), LlamaIndex, Supabase

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `backend/scripts/benchmark_runner.py` | Main benchmark: run pipeline, judge 8 metrics, compare baseline, report | Create |
| `backend/data/qa_corpus/benchmark-regression-subset.json` | 20-question curated subset for quick regression tests | Create |
| `backend/data/benchmarks/` | Directory for run results and baselines | Create dir |

---

### Task 1: Create Curated Regression Subset

**Files:**
- Create: `backend/data/qa_corpus/benchmark-regression-subset.json`

- [ ] **Step 1: Create the 20-question subset**

Select questions from `benchmark-windbot-v1.json` that cover all types and difficulties. Create `backend/data/qa_corpus/benchmark-regression-subset.json`:

```python
# Script to generate subset — run once:
import json

with open("backend/data/qa_corpus/benchmark-windbot-v1.json") as f:
    data = json.load(f)

# Select 20 representative questions across categories and types
selected_ids = []
all_pairs = []
for cat in data["categories"]:
    pairs = cat["pairs"]
    # Get Hard questions first, then Medium, then Easy
    hard = [p for p in pairs if p.get("difficulty") == "Hard"]
    medium = [p for p in pairs if p.get("difficulty") == "Medium"]
    easy = [p for p in pairs if p.get("difficulty") == "Easy"]

    # Take up to 3 Hard, 2 Medium per category
    take = hard[:3] + medium[:2]
    if len(take) < 5:
        take += easy[:5 - len(take)]

    for p in take:
        p["_category"] = cat["name"]
    all_pairs.extend(take[:10])  # max 10 per category

# Trim to 20
subset = all_pairs[:20]

output = {
    "description": "Curated 20-question subset for quick regression testing (~5-7 min)",
    "source": "benchmark-windbot-v1.json",
    "questions": subset
}

with open("backend/data/qa_corpus/benchmark-regression-subset.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Created subset with {len(subset)} questions")
```

Run this from the project root directory.

- [ ] **Step 2: Verify the file**

```bash
cd backend
python3 -c "
import json
with open('data/qa_corpus/benchmark-regression-subset.json') as f:
    data = json.load(f)
print(f'Questions: {len(data[\"questions\"])}')
for q in data['questions'][:3]:
    print(f'  [{q[\"difficulty\"]}] {q[\"question\"][:60]}')
"
```

Expected: 20 questions, mix of Hard/Medium/Easy.

- [ ] **Step 3: Create benchmarks directory**

```bash
mkdir -p backend/data/benchmarks
```

- [ ] **Step 4: Commit**

```bash
git add backend/data/qa_corpus/benchmark-regression-subset.json backend/data/benchmarks/.gitkeep
git commit -m "data: add 20-question curated regression test subset"
```

---

### Task 2: Create benchmark_runner.py

**Files:**
- Create: `backend/scripts/benchmark_runner.py`

- [ ] **Step 1: Create the benchmark runner script**

Create `backend/scripts/benchmark_runner.py`:

```python
"""Quality benchmark runner with 8 metrics and regression detection.

Runs the full RAG pipeline for each question, collects response + source
chunks, scores via GPT judge on 8 dimensions, compares with baseline.

Usage:
    cd backend

    # Quick regression test (20 questions, ~5-7 min)
    python scripts/benchmark_runner.py --subset

    # Full benchmark (160 questions, ~30-40 min)
    python scripts/benchmark_runner.py

    # Compare with baseline
    python scripts/benchmark_runner.py --subset --compare data/benchmarks/baseline.json

    # Save as new baseline
    python scripts/benchmark_runner.py --subset --save-baseline

    # Custom threshold
    python scripts/benchmark_runner.py --subset --compare baseline.json --threshold 0.5
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI  # noqa: E402
from supabase import create_client  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.query_expansion import GlossaryExpander  # noqa: E402
from app.services.rag import (  # noqa: E402
    configure_settings, create_index, create_vector_store, get_chat_engine,
)
from app.services.reranker import create_reranker  # noqa: E402

# ── Judge Prompts ─────────────────────────────────────────────────

JUDGE_PROMPT_EXISTING = """\
You are an expert evaluator for a wind turbine knowledge chatbot.
Compare the chatbot's actual answer with the expected answer.

Question: {question}
Expected Answer: {expected_answer}
Actual Answer: {actual_answer}
Scoring Criteria: {scoring_criteria}

Score each dimension from 1 to 5:
- accuracy: Factual correctness compared to expected answer
- completeness: Coverage of key points from expected answer
- relevance: Does it address the question directly?
- clarity: Clear and well-structured?
- tone: Professional and appropriate?

Return ONLY a JSON object. Example:
{{"accuracy": 4, "completeness": 3, "relevance": 5, "clarity": 4, "tone": 5}}"""

JUDGE_PROMPT_FAITHFULNESS = """\
You are evaluating a wind turbine chatbot's response for source faithfulness.

Question: {question}
Response: {response}

SOURCE CHUNKS (retrieved from knowledge base):
{source_chunks}

Score each dimension from 1 to 5 with a brief explanation:

1. factual_grounding: Is every factual claim in the response supported by the source chunks?
   5 = Every claim directly supported by sources
   3 = Most claims supported, 1-2 unsupported but plausible
   1 = Multiple claims have no support in sources

2. citation_accuracy: Do the numbered citations [1], [2] etc. correctly reference the content?
   5 = All citations correctly match their source content
   3 = Some citations decorative or mismatched
   1 = Citations random, no correlation with sources

3. hallucination: Does the response contain fabricated information not in sources?
   5 = No fabricated info, everything traceable to sources or common knowledge
   3 = Some details added beyond sources (could be correct but unverifiable)
   1 = Contains specific numbers/facts/names fabricated as if from documents

Return ONLY a JSON object with scores and explanations. Example:
{{"factual_grounding": {{"score": 4, "explanation": "..."}}, "citation_accuracy": {{"score": 5, "explanation": "..."}}, "hallucination": {{"score": 4, "explanation": "..."}}}}"""

ALL_METRICS = [
    "accuracy", "completeness", "relevance", "clarity", "tone",
    "factual_grounding", "citation_accuracy", "hallucination",
]


# ── Core Functions ────────────────────────────────────────────────

def get_chatbot_response(index, question, supabase_client, glossary, reranker):
    """Run full RAG pipeline and return (response_text, source_chunks)."""
    chat_engine = get_chat_engine(
        index, language="vi", has_history=False,
        supabase_client=supabase_client,
        glossary_expander=glossary,
        reranker=reranker,
    )
    result = chat_engine.chat(question)

    # Extract source chunks from the response
    source_chunks = []
    for node in getattr(result, "source_nodes", []) or []:
        meta = node.node.metadata or {}
        source_chunks.append({
            "id": meta.get("source_number", "?"),
            "filename": meta.get("filename", ""),
            "page": meta.get("page"),
            "text": node.node.get_content()[:500],
            "score": round(node.score, 3) if node.score else None,
        })

    return str(result), source_chunks


def judge_existing_metrics(client, question, expected, actual, criteria):
    """Score accuracy, completeness, relevance, clarity, tone."""
    prompt = JUDGE_PROMPT_EXISTING.format(
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


def judge_faithfulness(client, question, response_text, source_chunks):
    """Score factual_grounding, citation_accuracy, hallucination."""
    chunks_text = "\n\n".join(
        f"[Source {s['id']}] ({s['filename']}, p.{s['page']})\n{s['text']}"
        for s in source_chunks
    )
    if not chunks_text:
        chunks_text = "(No sources retrieved)"

    prompt = JUDGE_PROMPT_FAITHFULNESS.format(
        question=question,
        response=response_text,
        source_chunks=chunks_text,
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)

    # Normalize: extract score from nested dict if needed
    scores = {}
    explanations = {}
    for key in ("factual_grounding", "citation_accuracy", "hallucination"):
        val = raw.get(key, {})
        if isinstance(val, dict):
            scores[key] = val.get("score", 0)
            explanations[key] = val.get("explanation", "")
        else:
            scores[key] = int(val) if val else 0
            explanations[key] = ""

    return scores, explanations


def check_regression(current, baseline, threshold=0.3):
    """Compare current vs baseline scores, return list of regressions."""
    regressions = []
    for metric in ALL_METRICS:
        curr_val = current.get(metric, 0)
        base_val = baseline.get(metric)
        if base_val is None:
            continue  # new metric, no baseline
        delta = curr_val - base_val
        if delta < -threshold:
            regressions.append({
                "metric": metric,
                "baseline": base_val,
                "current": curr_val,
                "delta": round(delta, 2),
            })
    return regressions


def generate_report(summary, baseline_summary=None, threshold=0.3):
    """Generate Markdown report string."""
    lines = [
        f"# Benchmark Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**Total evaluated:** {summary['total_evaluated']}",
        f"**Overall average:** {summary['overall_average']:.2f}/5.0",
    ]

    if baseline_summary:
        base_avg = baseline_summary.get("overall_average", 0)
        delta = summary["overall_average"] - base_avg
        status = "✅ No regression" if delta >= -threshold else "❌ REGRESSION DETECTED"
        lines.append(f"**Baseline:** {base_avg:.2f}/5.0 (Δ {delta:+.2f}) {status}")

    lines += ["", "## Per-Metric Scores", ""]
    header = "| Metric | Current |"
    sep = "|--------|---------|"
    if baseline_summary:
        header += " Baseline | Δ | Status |"
        sep += "----------|---|--------|"
    lines += [header, sep]

    for m in ALL_METRICS:
        curr = summary["overall"].get(m, 0)
        row = f"| {m} | {curr:.2f} |"
        if baseline_summary:
            base = baseline_summary.get("overall", {}).get(m)
            if base is not None:
                delta = curr - base
                flag = "✅" if delta >= -threshold else "❌"
                row += f" {base:.2f} | {delta:+.2f} | {flag} |"
            else:
                row += " — | NEW | 🆕 |"
        lines.append(row)

    # Category breakdown
    lines += ["", "## By Category", ""]
    lines.append("| Category | Avg | Accuracy | Faithfulness | Hallucination |")
    lines.append("|----------|-----|----------|-------------|---------------|")
    for cat, scores in summary.get("by_category", {}).items():
        lines.append(
            f"| {cat} | {scores.get('average', 0):.1f} "
            f"| {scores.get('accuracy', 0):.1f} "
            f"| {scores.get('factual_grounding', 0):.1f} "
            f"| {scores.get('hallucination', 0):.1f} |"
        )

    # Regressions
    if baseline_summary:
        regs = check_regression(summary["overall"], baseline_summary.get("overall", {}), threshold)
        lines += ["", f"## Regressions: {len(regs)}"]
        if regs:
            for r in regs:
                lines.append(f"- **{r['metric']}**: {r['baseline']:.2f} → {r['current']:.2f} ({r['delta']:+.2f})")
        else:
            lines.append("None detected. ✅")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WindBot Quality Benchmark")
    parser.add_argument("--input", default="data/qa_corpus/benchmark-windbot-v1.json",
                        help="Full benchmark JSON")
    parser.add_argument("--subset", action="store_true",
                        help="Use 20-question regression subset")
    parser.add_argument("--output", help="Output JSON (default: auto-timestamped)")
    parser.add_argument("--compare", help="Baseline JSON to compare against")
    parser.add_argument("--save-baseline", action="store_true",
                        help="Save results as the new baseline")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Regression threshold (default: 0.3)")
    parser.add_argument("--sample", type=int, default=0,
                        help="Sample N questions (0=all)")
    args = parser.parse_args()

    # Determine input file
    if args.subset:
        input_file = "data/qa_corpus/benchmark-regression-subset.json"
    else:
        input_file = args.input

    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    # Extract questions
    if "questions" in data:
        # Subset format
        all_pairs = data["questions"]
    else:
        # Full benchmark format
        all_pairs = []
        for cat in data.get("categories", []):
            for pair in cat.get("pairs", []):
                pair["_category"] = cat["name"]
                all_pairs.append(pair)

    if args.sample > 0 and args.sample < len(all_pairs):
        import random
        all_pairs = random.sample(all_pairs, args.sample)

    print(f"🔧 Benchmark: {len(all_pairs)} questions from {input_file}")

    # Initialize RAG pipeline (matches production)
    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)
    index = create_index(vector_store)
    client = OpenAI(api_key=settings.openai_api_key)
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    glossary = GlossaryExpander()
    onnx_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "models", "reranker-int8",
    )
    reranker = create_reranker(onnx_dir, settings.reranker_threads)
    print(f"   Reranker: {type(reranker).__name__}")

    # Run benchmark
    results = []
    totals = {m: 0 for m in ALL_METRICS}
    category_scores = {}

    for i, pair in enumerate(all_pairs):
        qid = pair.get("id", i)
        question = pair["question"]
        expected = pair.get("expected_answer", "")
        criteria = pair.get("scoring_criteria", "")
        category = pair.get("_category", "Unknown")

        print(f"  [{i+1}/{len(all_pairs)}] {question[:60]}...", end=" ", flush=True)

        try:
            t0 = time.perf_counter()
            response_text, source_chunks = get_chatbot_response(
                index, question, supabase, glossary, reranker,
            )
            ttft = time.perf_counter() - t0

            # Judge: existing 5 metrics
            existing_scores = judge_existing_metrics(
                client, question, expected, response_text, criteria,
            )

            # Judge: 3 faithfulness metrics
            faith_scores, faith_explanations = judge_faithfulness(
                client, question, response_text, source_chunks,
            )

            all_scores = {**existing_scores, **faith_scores}

            result = {
                "qa_id": qid,
                "category": category,
                "question": question,
                "difficulty": pair.get("difficulty", ""),
                "response_length": len(response_text),
                "source_count": len(source_chunks),
                "ttft_seconds": round(ttft, 2),
                "scores": all_scores,
                "judge_explanations": faith_explanations,
                "overall": round(sum(all_scores.values()) / len(all_scores), 2),
            }
            results.append(result)

            for m in ALL_METRICS:
                totals[m] += all_scores.get(m, 0)

            if category not in category_scores:
                category_scores[category] = {"count": 0, **{m: 0 for m in ALL_METRICS}}
            category_scores[category]["count"] += 1
            for m in ALL_METRICS:
                category_scores[category][m] += all_scores.get(m, 0)

            print(f"avg={result['overall']:.1f} ({ttft:.1f}s)")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"qa_id": qid, "question": question, "error": str(e)})

        time.sleep(0.3)

    # Compute summary
    n = len([r for r in results if "scores" in r])
    summary = {"total_evaluated": 0, "overall": {}, "overall_average": 0, "by_category": {}}
    if n > 0:
        summary["total_evaluated"] = n
        summary["overall"] = {m: round(totals[m] / n, 2) for m in ALL_METRICS}
        summary["overall_average"] = round(sum(totals.values()) / (n * len(ALL_METRICS)), 2)
        for cat, s in category_scores.items():
            c = s["count"]
            summary["by_category"][cat] = {
                "count": c,
                **{m: round(s[m] / c, 2) for m in ALL_METRICS},
                "average": round(sum(s[m] for m in ALL_METRICS) / (c * len(ALL_METRICS)), 2),
            }

    # Output
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = args.output or f"data/benchmarks/run-{timestamp}.json"
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    output = {
        "timestamp": timestamp,
        "input_file": input_file,
        "question_count": len(all_pairs),
        "summary": summary,
        "results": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Save as baseline if requested
    if args.save_baseline:
        baseline_file = "data/benchmarks/baseline.json"
        with open(baseline_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved as baseline: {baseline_file}")

    # Compare with baseline
    baseline_summary = None
    if args.compare:
        with open(args.compare, encoding="utf-8") as f:
            baseline_data = json.load(f)
        baseline_summary = baseline_data.get("summary", {})

    # Generate report
    report = generate_report(summary, baseline_summary, args.threshold)
    report_file = output_file.replace(".json", "_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    # Print summary
    print("\n" + "=" * 70)
    print(report)
    print("=" * 70)
    print(f"\nResults: {output_file}")
    print(f"Report:  {report_file}")

    # Exit code for CI
    if baseline_summary:
        regs = check_regression(summary["overall"], baseline_summary.get("overall", {}), args.threshold)
        if regs:
            print(f"\n❌ {len(regs)} regressions detected!")
            sys.exit(1)
        else:
            print("\n✅ No regressions. Quality maintained.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
cd backend
python3 -c "import py_compile; py_compile.compile('scripts/benchmark_runner.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/benchmark_runner.py
git commit -m "feat: add quality benchmark runner with 8 metrics + regression detection"
```

---

### Task 3: Create Baseline + Test Run

- [ ] **Step 1: Create benchmarks directory and gitkeep**

```bash
mkdir -p backend/data/benchmarks
touch backend/data/benchmarks/.gitkeep
git add backend/data/benchmarks/.gitkeep
```

- [ ] **Step 2: Run quick subset benchmark on VPS to create baseline**

Deploy and run:
```bash
# On VPS:
su - botai
cd ~/botai/repo && git pull
cd backend && source venv/bin/activate

# Quick test with 3 questions first
python scripts/benchmark_runner.py --subset --sample 3

# If works, run full subset and save as baseline
python scripts/benchmark_runner.py --subset --save-baseline
```

Expected output: 20 questions scored, baseline saved to `data/benchmarks/baseline.json`

- [ ] **Step 3: Run regression check against baseline**

```bash
python scripts/benchmark_runner.py --subset --compare data/benchmarks/baseline.json
```

Expected: `✅ No regressions` (since baseline = current)

- [ ] **Step 4: Commit baseline and all files**

```bash
git add backend/data/benchmarks/ backend/data/qa_corpus/benchmark-regression-subset.json
git add docs/superpowers/specs/2026-04-15-quality-benchmark-design.md
git commit -m "feat: complete quality benchmark suite with baseline snapshot"
```

- [ ] **Step 5: Push**

```bash
git push origin lyeoeon1/add-glossary-search-v3:master
```
