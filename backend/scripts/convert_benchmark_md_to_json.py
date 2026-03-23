"""Convert benchmark Markdown Q&A file to JSON for evaluation.

Usage:
    cd backend
    python scripts/convert_benchmark_md_to_json.py \
        --input ../benchmark-windbot-v1.md \
        --output ./data/qa_corpus/benchmark-windbot-v1.json
"""

import argparse
import json
import os
import re
import sys


def parse_markdown_tables(md_content: str) -> dict:
    """Parse benchmark Markdown file into structured JSON."""
    result = {
        "version": "1.0",
        "source_file": "",
        "total_pairs": 0,
        "categories": [],
    }

    current_category = None
    current_subsection = None

    lines = md_content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect category headers (## N. Category Name)
        cat_match = re.match(r"^##\s+(\d+)\.\s+(.+)", line)
        if cat_match and not line.startswith("###"):
            current_category = {
                "name": cat_match.group(2).strip(),
                "pairs": [],
            }
            result["categories"].append(current_category)
            i += 1
            continue

        # Detect subsection headers (### N.N. Subsection)
        sub_match = re.match(r"^###\s+\d+\.\d+\.\s+(.+)", line)
        if sub_match:
            current_subsection = sub_match.group(1).strip()
            i += 1
            continue

        # Detect table rows (| # | question | answer | ... |)
        if (
            current_category is not None
            and line.startswith("|")
            and not line.startswith("| #")
            and not line.startswith("|---")
            and not line.startswith("|-")
        ):
            cells = [c.strip() for c in line.split("|")]
            # Remove empty first/last from split
            cells = [c for c in cells if c]

            if len(cells) >= 6:
                try:
                    qa_id = int(cells[0])
                except ValueError:
                    i += 1
                    continue

                pair = {
                    "id": qa_id,
                    "question": cells[1],
                    "expected_answer": cells[2],
                    "difficulty": cells[3],
                    "type": cells[4],
                    "scoring_criteria": cells[5],
                    "subsection": current_subsection or "",
                }
                current_category["pairs"].append(pair)

        i += 1

    result["total_pairs"] = sum(len(c["pairs"]) for c in result["categories"])
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Convert benchmark Markdown Q&A to JSON"
    )
    parser.add_argument("--input", required=True, help="Input Markdown file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: {args.input} not found")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        md_content = f.read()

    result = parse_markdown_tables(md_content)
    result["source_file"] = os.path.basename(args.input)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Converted {result['total_pairs']} Q&A pairs from {result['source_file']}")
    for cat in result["categories"]:
        print(f"  {cat['name']}: {len(cat['pairs'])} pairs")


if __name__ == "__main__":
    main()
