# Bilingual Retrieval Redesign — Design Spec

## Problem

1. System prompt says "IGNORE English sources on same topic" → 86% of KB (EN content) is effectively unused when VN sources exist
2. Hỏi VN retrieves mostly VN chunks; hỏi EN retrieves mostly EN chunks → same question in different languages produces different answers
3. EN sources have valuable deep technical details that VN sources don't cover, but they're being ignored

## Principles

- Same question = same content, regardless of query language
- Vietnamese terminology and structure as foundation
- English sources supplement with deeper details VN doesn't cover
- When VN and EN conflict → VN wins
- vi_reserved_slots=8 stays (retriever still prioritizes VN chunks)

## Changes (ordered by risk: lowest first)

### 1. Consistency Instruction (zero risk)

Add to system prompt (EN + VI):
```
CONSISTENCY: Your answer content must be the SAME regardless of whether 
the user asks in Vietnamese or English. Only the response language changes. 
Use ALL relevant sources (both Vietnamese and English) to build the most 
complete answer possible.
```

### 2. Revise Source Priority Prompt (medium risk)

Replace "IGNORE English" with "SUPPLEMENT from English":

**EN prompt — replace SOURCE DOCUMENT PRIORITY section:**
```
SOURCE DOCUMENT PRIORITY: Vietnamese-language sources (EPU textbook 
"Dien_Gio_Sach_chuyen_nganh.pdf", "Wind-Tecnology_1.docx") provide the 
FOUNDATION — use their terminology, structure, and descriptions as the 
primary framework for your answer. English-language sources SUPPLEMENT 
the answer: include specific technical details, numbers, standards, 
formulas, or deeper analysis from English sources that Vietnamese sources 
do not cover. When Vietnamese and English sources CONFLICT on facts, 
specifications, or descriptions, use the Vietnamese source EXCLUSIVELY.
When English sources add NEW information not found in Vietnamese sources, 
INCLUDE it with proper citation.
```

**VI prompt — equivalent update.**

### 3. Verify Glossary Coverage (zero risk)

Check if key technical terms are in the 90-entry glossary. Run queries through GlossaryExpander and check if cross-language expansion works. If gaps found, add entries.

### 4. Cross-language Multi-query for COMPARISON/TROUBLESHOOT (low risk)

Only if glossary expansion is insufficient after step 3.

Modify `generate_query_variants` prompt to include instruction:
"Generate 1 variant in the OPPOSITE language of the original query 
(if query is Vietnamese, generate 1 English variant; if English, 
generate 1 Vietnamese variant)."

Only applies when multi-query is ON (COMPARISON, TROUBLESHOOT types).

## Files to Modify

| File | Change |
|---|---|
| `backend/app/prompts/system.py` | Steps 1+2: consistency + revised source priority (EN+VI) |
| `backend/data/knowledge_base/glossary_seed.json` | Step 3: add missing entries if found |
| `backend/app/services/query_generation.py` | Step 4: cross-lang variant instruction |

## Verification

After each step:
1. Run benchmark: `python scripts/benchmark_runner.py --input data/qa_corpus/benchmark-recent-10.json`
2. Test same question in VN and EN on website, compare responses
3. Check source citations: should include both VN and EN sources
4. Verify no quality regression vs baseline (4.51 overall)

## Edge Cases to Test

- "Hộp số hoạt động như thế nào?" vs "How does a gearbox work?" → same content
- "So sánh HAWT và VAWT" → should cite both VN (EPU) and EN (Wind Energy Handbook)
- Topic only in EN (e.g., FOWT foundations) → should use EN sources freely
- Topic only in VN (e.g., EPU-specific terminology) → should use VN exclusively
