# WindBot Quality Benchmark Suite — Design Spec

## Context

After performance optimization (15-20s → 3-10s TTFT), need to ensure content quality doesn't regress. Existing `evaluate_rag.py` has 5 metrics but lacks source faithfulness checking and baseline comparison. This benchmark will run before each deploy to catch quality regressions.

## Design

### New Script: `benchmark_runner.py`

Single script that:
1. Runs full RAG pipeline for each question in the benchmark dataset
2. Collects response + retrieved source chunks
3. GPT judge scores 8 metrics (5 existing + 3 new source faithfulness)
4. Compares with baseline snapshot, flags regressions
5. Outputs JSON results + Markdown report

### 8 Quality Metrics (1-5 scale)

**Existing 5 (from evaluate_rag.py):**
- accuracy: Factual correctness vs expected answer
- completeness: Coverage of key points
- relevance: How well answer addresses the question
- clarity: Structure and readability
- tone: Professional appropriateness

**New 3 (source faithfulness):**
- factual_grounding: Every claim supported by retrieved source chunks
- citation_accuracy: [N] citations correctly reference the cited content
- hallucination: No fabricated info beyond sources/common knowledge

### GPT Judge Prompts for New Metrics

**Factual Grounding:**
```
Given the RESPONSE and the SOURCE CHUNKS retrieved, score 1-5:
5 = Every factual claim directly supported by at least one source
4 = Almost all claims supported, one minor unsupported detail
3 = Most claims supported, 1-2 unsupported but plausible
2 = Several claims lack source support
1 = Multiple specific claims have no basis in sources
```

**Citation Accuracy:**
```
The response contains numbered citations [1], [2], etc. Each maps to a source chunk below.
Score 1-5:
5 = All citations correctly reference the content they claim to cite
4 = Most correct, one minor mismatch
3 = Some citations decorative or mismatched
2 = Many citations don't match actual source content
1 = Citations are random, no correlation with sources
```

**Hallucination Detection:**
```
Compare RESPONSE against ONLY the source chunks. Score 1-5:
5 = No fabricated information, everything traceable to sources or common knowledge
4 = One minor embellishment that's harmless
3 = Some specific details added beyond sources (could be correct but unverifiable)
2 = Notable claims not in sources presented as facts
1 = Contains specific numbers/facts/names fabricated and presented as from documents
```

### Baseline Snapshot + Regression Detection

- First run: save as `data/benchmarks/baseline.json`
- Subsequent runs: compare each metric with baseline
- **Regression threshold:** flag if any metric drops >0.3 points (configurable)
- **Overall pass/fail:** PASS if no metric regressed >0.3

### Curated Regression Subset (20 questions)

Select 2-3 questions per category from the 160 Q&A dataset:
- Prioritize Hard difficulty
- Include questions requiring specific numbers/data (easy to hallucinate)
- Include questions needing multi-source synthesis (tests retrieval quality)

Save as `data/qa_corpus/benchmark-regression-subset.json`

Quick regression test: ~5-7 minutes vs ~30-40 minutes for full 160.

### Output Format

**Per-question JSON:**
```json
{
  "id": "structure-01",
  "question": "...",
  "question_type": "STRUCTURE",
  "difficulty": "Hard",
  "response": "...",
  "response_length": 2321,
  "source_count": 4,
  "sources": [...],
  "scores": {
    "accuracy": 4.5,
    "completeness": 4.0,
    "relevance": 5.0,
    "clarity": 4.5,
    "tone": 5.0,
    "factual_grounding": 4.5,
    "citation_accuracy": 4.0,
    "hallucination": 5.0
  },
  "overall": 4.56,
  "judge_explanations": {
    "factual_grounding": "All claims about gearbox components match Source [1] and [3]...",
    "citation_accuracy": "Citation [2] references blade design but text discusses nacelle...",
    "hallucination": "No fabricated information detected..."
  }
}
```

**Summary Markdown report** with:
- Overall score + comparison with baseline
- Per-metric comparison table with regression flags
- Per-category breakdown
- List of specific regressions (if any)
- Top 5 lowest-scoring questions (attention needed)

### CLI Usage

```bash
# Full benchmark (160 questions)
python scripts/benchmark_runner.py --output data/benchmarks/run-2026-04-15.json

# Quick regression test (20 questions)
python scripts/benchmark_runner.py --subset

# Compare with baseline
python scripts/benchmark_runner.py --subset --compare data/benchmarks/baseline.json

# Save as new baseline
python scripts/benchmark_runner.py --save-baseline

# Custom regression threshold
python scripts/benchmark_runner.py --subset --compare baseline.json --threshold 0.5
```

### Files

| File | Action |
|---|---|
| `backend/scripts/benchmark_runner.py` | Create — main benchmark script |
| `backend/data/benchmarks/` | Create dir — run results |
| `backend/data/qa_corpus/benchmark-regression-subset.json` | Create — 20-question curated subset |
| `backend/scripts/evaluate_rag.py` | Keep unchanged (backward compat) |

### Verification

1. Run `benchmark_runner.py --subset` on VPS, verify all 8 metrics scored
2. Run `--save-baseline` to create first baseline
3. Make a dummy code change, run `--subset --compare baseline.json`, verify no regression
4. Intentionally break something (e.g., disable reranking), verify regression detected
