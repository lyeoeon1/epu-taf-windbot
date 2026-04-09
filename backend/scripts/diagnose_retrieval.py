"""Diagnose retrieval quality for specific questions.

Retrieves top-K chunks from the vector store and displays them
with similarity scores, source file, and content snippets.
Helps identify whether errors come from retrieval, KB content, or LLM.

Usage:
    cd backend
    python scripts/diagnose_retrieval.py --question "Hộp số tăng tốc thì momen xoắn thay đổi thế nào?"
    python scripts/diagnose_retrieval.py --batch   # Run all 8 customer error questions
"""

import argparse
import json
import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings  # noqa: E402
from app.services.rag import configure_settings, create_vector_store, create_index  # noqa: E402

# 8 questions from customer feedback that produced wrong answers
CUSTOMER_ERROR_QUESTIONS = [
    {
        "id": 1,
        "question": "Các bộ phận chính của một tuabin điện gió gồm những gì và chức năng của từng bộ phận?",
        "error": "Drive train chuyển cơ năng thành điện",
        "correct": "Drive train chỉ truyền cơ năng qua hộp số. Máy phát mới chuyển thành điện.",
        "keywords": ["drive train", "hệ thống truyền động", "máy phát", "generator", "mechanical", "electrical"],
    },
    {
        "id": 2,
        "question": "Tại sao cánh quạt tuabin thường có dạng cong và khí động học đặc biệt?",
        "error": "Hình dạng cánh điều chỉnh theo tốc độ gió",
        "correct": "Hình dạng cánh CỐ ĐỊNH. Chỉ góc nghiêng (pitch) thay đổi.",
        "keywords": ["blade shape", "fixed", "pitch", "hình dạng", "cố định", "góc nghiêng"],
    },
    {
        "id": 3,
        "question": "Giới hạn vật lý của việc khai thác năng lượng gió là gì",
        "error": "Nhầm giới hạn kỹ thuật với giới hạn vật lý Betz",
        "correct": "Betz = tối ưu khai thác giữa luồng gió đến/ra (59.3%), KHÔNG phải hiệu suất kỹ thuật.",
        "keywords": ["betz", "59.3", "momentum", "physical limit", "giới hạn vật lý"],
    },
    {
        "id": 4,
        "question": "Hãy giải thích chi tiết về pitch control",
        "error": "Phân loại stall control vào pitch control + dịch sai lực cản",
        "correct": "Stall ≠ Pitch (khác cơ cấu). Stall = mất lực NÂNG, không phải lực cản.",
        "keywords": ["stall", "pitch", "lift", "drag", "lực nâng", "lực cản"],
    },
    {
        "id": 5,
        "question": "Vai trò của hộp số (gearbox) trong tuabin gió là gì",
        "error": "Tăng tốc độ VÀ tăng momen xoắn",
        "correct": "Tốc độ và momen xoắn TỶ LỆ NGHỊCH. Hộp số tăng tốc nhưng GIẢM momen.",
        "keywords": ["torque", "speed", "inverse", "momen xoắn", "tỷ lệ nghịch"],
    },
    {
        "id": 6,
        "question": "Máy phát điện trong tuabin gió thường sử dụng những loại nào (DFIG, synchronous generator) và sự khác biệt giữa chúng là gì?",
        "error": "Stator được kích thích trong máy phát đồng bộ",
        "correct": "ROTOR được cấp từ (permanent magnets hoặc DC windings), không phải stator.",
        "keywords": ["rotor", "stator", "excitation", "permanent magnet", "field", "kích thích", "cấp từ"],
    },
    {
        "id": 7,
        "question": "Máy phát đồng bộ có thể điều chỉnh tốc độ không?",
        "error": "Không thể điều chỉnh tốc độ",
        "correct": "Có converter (full-scale) → hoạt động tốt ở nhiều tốc độ gió.",
        "keywords": ["converter", "variable speed", "full-scale", "tốc độ", "điều chỉnh"],
    },
    {
        "id": 8,
        "question": "Hệ thống phanh (braking system) trong tuabin gió gồm những loại nào",
        "error": "2 hệ thống phanh độc lập",
        "correct": "Phanh cơ khí chỉ hãm SAU KHI phanh khí động đã giảm tốc. KHÔNG độc lập.",
        "keywords": ["aerodynamic", "mechanical", "sequence", "after", "independent", "phanh khí động", "phanh cơ khí"],
    },
]


def diagnose_question(index, question: str, top_k: int = 20) -> list[dict]:
    """Retrieve top-K chunks for a question and return structured results."""
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(question)

    results = []
    for i, node_ws in enumerate(nodes):
        content = node_ws.node.get_content()
        metadata = node_ws.node.metadata or {}
        results.append({
            "rank": i + 1,
            "score": round(node_ws.score, 4) if node_ws.score else None,
            "filename": metadata.get("filename", "unknown"),
            "page": metadata.get("page"),
            "language": metadata.get("language", "?"),
            "content_preview": content[:500],
            "content_full": content,
        })
    return results


def check_keywords_in_chunks(chunks: list[dict], keywords: list[str]) -> list[dict]:
    """Check which keywords appear in which chunks."""
    matches = []
    for chunk in chunks:
        text_lower = chunk["content_full"].lower()
        found_keywords = [kw for kw in keywords if kw.lower() in text_lower]
        if found_keywords:
            matches.append({
                "rank": chunk["rank"],
                "score": chunk["score"],
                "filename": chunk["filename"],
                "keywords_found": found_keywords,
            })
    return matches


def print_diagnosis(q_info: dict, chunks: list[dict]):
    """Print formatted diagnosis for one question."""
    print(f"\n{'='*80}")
    print(f"Question #{q_info['id']}: {q_info['question']}")
    print(f"  AI Error: {q_info['error']}")
    print(f"  Correct:  {q_info['correct']}")
    print(f"{'='*80}")

    # Check keywords
    keyword_matches = check_keywords_in_chunks(chunks, q_info["keywords"])
    if keyword_matches:
        print(f"\n  Keyword matches found in {len(keyword_matches)} chunk(s):")
        for m in keyword_matches[:5]:
            print(f"    Rank #{m['rank']} (score={m['score']}) [{m['filename']}] → {m['keywords_found']}")
    else:
        print(f"\n  NO keyword matches found! KB may lack relevant content.")

    # Show top 5 chunks
    print(f"\n  Top 5 retrieved chunks:")
    for chunk in chunks[:5]:
        preview = textwrap.shorten(chunk["content_preview"], width=200, placeholder="...")
        print(f"    #{chunk['rank']} score={chunk['score']} [{chunk['filename']}] p.{chunk['page']}")
        print(f"       {preview}")
        print()

    # Diagnosis suggestion
    if keyword_matches and keyword_matches[0]["rank"] <= 5:
        print(f"  DIAGNOSIS: Type A — Correct content IS retrieved (rank #{keyword_matches[0]['rank']})")
        print(f"             → LLM is IGNORING the context. Fix: Prompt hardening.")
    elif keyword_matches and keyword_matches[0]["rank"] > 5:
        print(f"  DIAGNOSIS: Type B — Correct content exists but ranked LOW (#{keyword_matches[0]['rank']})")
        print(f"             → RETRIEVAL issue. Fix: Tune top_k / similarity_cutoff.")
    elif not keyword_matches:
        print(f"  DIAGNOSIS: Type D — No relevant content found in KB.")
        print(f"             → KB MISSING content. Fix: Add to knowledge base.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Diagnose retrieval quality")
    parser.add_argument("--question", type=str, help="Single question to diagnose")
    parser.add_argument("--batch", action="store_true", help="Run all 8 customer error questions")
    parser.add_argument("--top-k", type=int, default=20, help="Number of chunks to retrieve")
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    args = parser.parse_args()

    if not args.question and not args.batch:
        parser.error("Provide --question or --batch")

    # Initialize
    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)
    index = create_index(vector_store)

    all_results = {}

    if args.batch:
        print(f"Running diagnostic for {len(CUSTOMER_ERROR_QUESTIONS)} customer error questions...")
        print(f"Retrieving top {args.top_k} chunks per question.\n")

        for q_info in CUSTOMER_ERROR_QUESTIONS:
            chunks = diagnose_question(index, q_info["question"], args.top_k)
            print_diagnosis(q_info, chunks)
            all_results[q_info["id"]] = {
                "question": q_info["question"],
                "chunks_count": len(chunks),
                "top_scores": [c["score"] for c in chunks[:5]],
                "keyword_matches": check_keywords_in_chunks(chunks, q_info["keywords"]),
            }
    else:
        chunks = diagnose_question(index, args.question, args.top_k)
        print(f"\nResults for: {args.question}")
        print(f"Retrieved {len(chunks)} chunks:\n")
        for chunk in chunks:
            preview = textwrap.shorten(chunk["content_preview"], width=200, placeholder="...")
            print(f"  #{chunk['rank']} score={chunk['score']} [{chunk['filename']}] p.{chunk['page']} lang={chunk['language']}")
            print(f"     {preview}")
            print()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
