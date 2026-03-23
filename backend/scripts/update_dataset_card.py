"""Update dataset_card.md statistics from Supabase and local files.

Usage:
    cd backend
    python scripts/update_dataset_card.py
"""

import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings  # noqa: E402


def get_db_stats() -> dict:
    """Query Supabase for document and glossary statistics."""
    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Documents metadata
    docs = client.table("documents_metadata").select("*").execute()
    total_docs = len(docs.data)
    total_chunks = sum(d.get("num_chunks", 0) for d in docs.data)
    en_docs = sum(1 for d in docs.data if d.get("language") == "en")
    vi_docs = sum(1 for d in docs.data if d.get("language") == "vi")

    # Glossary
    try:
        glossary = client.table("glossary").select("id", count="exact").execute()
        glossary_count = glossary.count if glossary.count is not None else len(glossary.data)
    except Exception:
        glossary_count = 0

    return {
        "total_docs": total_docs,
        "total_chunks": total_chunks,
        "en_docs": en_docs,
        "vi_docs": vi_docs,
        "glossary_count": glossary_count,
    }


def count_qa_pairs() -> int:
    """Count Q&A pairs from JSON files in data/qa_corpus/."""
    qa_dir = os.path.join(os.path.dirname(__file__), "..", "data", "qa_corpus")
    total = 0

    for json_file in glob.glob(os.path.join(qa_dir, "**", "*.json"), recursive=True):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "pairs" in data:
                total += len(data["pairs"])
            elif "categories" in data:
                for cat in data["categories"]:
                    total += len(cat.get("pairs", []))
        except (json.JSONDecodeError, KeyError):
            pass

    return total


def update_card(card_path: str, stats: dict):
    """Update the STATS section in dataset_card.md."""
    with open(card_path, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    new_stats = f"""| Metric / Chỉ số | Value / Giá trị |
|------------------|-----------------|
| Total documents / Tổng tài liệu | {stats['total_docs']} |
| Total chunks / Tổng phân đoạn | {stats['total_chunks']} |
| English documents / Tài liệu tiếng Anh | {stats['en_docs']} |
| Vietnamese documents / Tài liệu tiếng Việt | {stats['vi_docs']} |
| Glossary terms / Thuật ngữ | {stats['glossary_count']} |
| Q&A pairs / Cặp Q&A | {stats['qa_pairs']} |
| Last updated / Cập nhật lần cuối | {now} |"""

    pattern = r"<!-- STATS_START -->.*?<!-- STATS_END -->"
    replacement = f"<!-- STATS_START -->\n{new_stats}\n<!-- STATS_END -->"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(card_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    card_path = os.path.join(os.path.dirname(__file__), "..", "..", "dataset_card.md")
    card_path = os.path.abspath(card_path)

    if not os.path.isfile(card_path):
        print(f"Error: {card_path} not found")
        sys.exit(1)

    print("Gathering statistics...")
    stats = get_db_stats()
    stats["qa_pairs"] = count_qa_pairs()

    print(f"  Documents: {stats['total_docs']} ({stats['en_docs']} EN, {stats['vi_docs']} VI)")
    print(f"  Chunks: {stats['total_chunks']}")
    print(f"  Glossary terms: {stats['glossary_count']}")
    print(f"  Q&A pairs: {stats['qa_pairs']}")

    update_card(card_path, stats)
    print(f"Updated {card_path}")


if __name__ == "__main__":
    main()
