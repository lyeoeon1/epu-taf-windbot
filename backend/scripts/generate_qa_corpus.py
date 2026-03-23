"""Generate Q&A corpus using GPT from general knowledge or documents.

Usage:
    cd backend
    python scripts/generate_qa_corpus.py --category structure --language vi --count 50
    python scripts/generate_qa_corpus.py --category maintenance --language vi --count 30 --from-doc ./data/manual.pdf
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI  # noqa: E402

from app.config import settings  # noqa: E402

CATEGORIES = ["structure", "components", "operations", "maintenance", "safety", "troubleshooting"]

GENERATE_PROMPT = """\
Generate exactly {count} question-answer pairs about wind turbine {category}.
Language: {language_name}
Difficulty distribution: 40% Easy, 40% Medium, 20% Hard

Each pair must be technically accurate and suitable for training an AI chatbot
specialized in wind turbine technology.

Return a JSON array where each element has:
- "id": "{category}_{lang}_{start_num}" (incrementing)
- "question": the question
- "answer": detailed, accurate answer (2-5 sentences)
- "difficulty": "Easy", "Medium", or "Hard"
- "tags": list of relevant keywords
- "source": "general_knowledge"

Return ONLY the JSON array, no other text."""

GENERATE_FROM_DOC_PROMPT = """\
Based on the following document content, generate exactly {count} question-answer pairs
about wind turbine {category}.
Language: {language_name}

Document content:
---
{doc_content}
---

Each pair must be based on information from the document.

Return a JSON array where each element has:
- "id": "{category}_{lang}_{start_num}" (incrementing)
- "question": the question
- "answer": detailed answer based on the document (2-5 sentences)
- "difficulty": "Easy", "Medium", or "Hard"
- "tags": list of relevant keywords
- "source": "document"

Return ONLY the JSON array, no other text."""


async def main():
    parser = argparse.ArgumentParser(description="Generate Q&A corpus using GPT")
    parser.add_argument("--category", required=True, choices=CATEGORIES)
    parser.add_argument("--language", default="vi", choices=["en", "vi"])
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--from-doc", help="Generate from a document file")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "qa_corpus"),
    )
    args = parser.parse_args()

    client = OpenAI(api_key=settings.openai_api_key)
    lang_name = "Vietnamese" if args.language == "vi" else "English"

    # Check existing pairs for start numbering
    output_dir = os.path.join(args.output_dir, args.category)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"qa_{args.category}_{args.language}.json")

    existing_pairs = []
    if os.path.isfile(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing_pairs = data.get("pairs", [])

    start_num = len(existing_pairs) + 1

    if args.from_doc:
        # Read document content
        with open(args.from_doc, "r", encoding="utf-8") as f:
            doc_content = f.read()[:8000]  # Limit to 8K chars

        prompt = GENERATE_FROM_DOC_PROMPT.format(
            count=args.count,
            category=args.category,
            language_name=lang_name,
            doc_content=doc_content,
            lang=args.language,
            start_num=f"{start_num:03d}",
        )
    else:
        prompt = GENERATE_PROMPT.format(
            count=args.count,
            category=args.category,
            language_name=lang_name,
            lang=args.language,
            start_num=f"{start_num:03d}",
        )

    print(f"Generating {args.count} Q&A pairs for {args.category} ({lang_name})...")

    # Generate in batches of 25 to avoid token limits
    all_new_pairs = []
    remaining = args.count
    batch_num = start_num

    while remaining > 0:
        batch_size = min(remaining, 25)
        batch_prompt = prompt.replace(f"exactly {args.count}", f"exactly {batch_size}")
        batch_prompt = batch_prompt.replace(f"_{start_num:03d}", f"_{batch_num:03d}")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": batch_prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        try:
            parsed = json.loads(content)
            # Handle both array and object with "pairs" key
            pairs = parsed if isinstance(parsed, list) else parsed.get("pairs", parsed.get("questions", []))
            all_new_pairs.extend(pairs)
            print(f"  Batch: generated {len(pairs)} pairs")
        except json.JSONDecodeError as e:
            print(f"  Batch failed to parse: {e}")

        remaining -= batch_size
        batch_num += batch_size

    # Merge with existing
    all_pairs = existing_pairs + all_new_pairs

    corpus = {
        "category": args.category,
        "language": args.language,
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pairs": all_pairs,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_pairs)} total pairs to {output_file}")
    print(f"  ({len(existing_pairs)} existing + {len(all_new_pairs)} new)")


if __name__ == "__main__":
    asyncio.run(main())
