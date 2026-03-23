"""Seed glossary data into Supabase DB and/or generate Markdown files.

Usage:
    cd backend
    python scripts/seed_glossary.py --seed ./data/knowledge_base/glossary_seed.json --write-db --write-md
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings  # noqa: E402


def load_seed_data(seed_path: str) -> list[dict]:
    with open(seed_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_to_db(entries: list[dict]):
    """Upsert glossary entries into Supabase."""
    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_key)

    for entry in entries:
        row = {
            "term_en": entry["term_en"],
            "term_vi": entry["term_vi"],
            "definition_en": entry["definition_en"],
            "definition_vi": entry["definition_vi"],
            "category": entry["category"],
            "abbreviation": entry.get("abbreviation"),
            "related_terms": entry.get("related_terms", []),
        }
        client.table("glossary").upsert(row, on_conflict="term_en").execute()

    print(f"  [DB] Upserted {len(entries)} glossary entries")


def write_to_markdown(entries: list[dict], output_dir: str):
    """Generate Markdown files grouped by category."""
    os.makedirs(output_dir, exist_ok=True)

    by_category: dict[str, list[dict]] = {}
    for entry in entries:
        cat = entry["category"]
        by_category.setdefault(cat, []).append(entry)

    for category, items in sorted(by_category.items()):
        filename = f"glossary_{category}.md"
        filepath = os.path.join(output_dir, filename)

        lines = [
            f"# Wind Turbine Glossary: {category.title()}",
            f"# Từ điển thuật ngữ tua-bin gió: {category.title()}",
            "",
        ]

        for item in sorted(items, key=lambda x: x["term_en"]):
            abbr = f" ({item['abbreviation']})" if item.get("abbreviation") else ""
            lines.append(f"## {item['term_en']}{abbr} / {item['term_vi']}")
            lines.append("")
            lines.append(f"**English**: {item['definition_en']}")
            lines.append("")
            lines.append(f"**Tiếng Việt**: {item['definition_vi']}")
            lines.append("")
            lines.append(f"- **Category**: {category}")
            if item.get("related_terms"):
                lines.append(f"- **Related**: {', '.join(item['related_terms'])}")
            lines.append("")
            lines.append("---")
            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"  [MD] {filename} — {len(items)} terms")


def main():
    parser = argparse.ArgumentParser(description="Seed glossary data")
    parser.add_argument("--seed", required=True, help="Path to glossary_seed.json")
    parser.add_argument("--write-db", action="store_true", help="Write to Supabase DB")
    parser.add_argument("--write-md", action="store_true", help="Generate Markdown files")
    parser.add_argument(
        "--md-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base", "glossary"),
        help="Output directory for Markdown files",
    )
    args = parser.parse_args()

    if not args.write_db and not args.write_md:
        print("Error: specify at least one of --write-db or --write-md")
        sys.exit(1)

    entries = load_seed_data(args.seed)
    print(f"Loaded {len(entries)} glossary entries from {args.seed}")

    if args.write_db:
        write_to_db(entries)

    if args.write_md:
        write_to_markdown(entries, args.md_dir)

    print("Done!")


if __name__ == "__main__":
    main()
