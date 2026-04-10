"""Export chunks from database for contextual augmentation.

Reads all non-QA chunks from chunk_fts table, groups by filename,
and exports to local files for Claude Code augmentation.

Usage (run as botai user on VPS):
    cd ~/botai/repo/backend
    ~/botai/repo/backend/venv/bin/python scripts/export_chunks_for_augment.py

Output:
    augment_workspace/input/{safe_name}.context.txt  (all chunks concatenated)
    augment_workspace/input/{safe_name}.chunks.json   (list of {id, text, page})
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
from app.config import settings

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "augment_workspace", "input")


def safe_filename(name: str) -> str:
    """Convert filename to safe filesystem name."""
    name = re.sub(r'[^\w\s\-.]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:80]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sb = create_client(settings.supabase_url, settings.supabase_service_key)

    # Fetch all non-QA chunks from chunk_fts (original text)
    print("Fetching chunks from database...")
    all_chunks = []
    offset = 0
    batch_size = 1000

    while True:
        response = (
            sb.table("chunk_fts")
            .select("chunk_id, content, filename, page, language")
            .filter("filename", "not.like", "QA%")
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        if not response.data:
            break

        all_chunks.extend(response.data)
        offset += batch_size
        print(f"  Fetched {len(all_chunks)} chunks so far...")

        if len(response.data) < batch_size:
            break

    print(f"\nTotal chunks: {len(all_chunks)}")

    # Group by filename
    grouped = {}
    for chunk in all_chunks:
        fname = chunk.get("filename", "unknown")
        if fname not in grouped:
            grouped[fname] = []
        grouped[fname].append(chunk)

    # Sort each group by page
    for fname in grouped:
        grouped[fname].sort(key=lambda c: c.get("page") or 0)

    # Export each group
    print(f"\nExporting {len(grouped)} documents:\n")

    summary = []
    for fname, chunks in sorted(grouped.items(), key=lambda x: -len(x[1])):
        safe_name = safe_filename(fname)

        # Build context (concatenated chunks)
        context_parts = []
        for c in chunks:
            page = c.get("page")
            prefix = f"[Page {page}] " if page else ""
            context_parts.append(f"{prefix}{c['content']}")

        full_context = "\n\n---\n\n".join(context_parts)

        # Truncate if too long (300K chars ~ 75K tokens)
        if len(full_context) > 300_000:
            full_context = full_context[:300_000] + "\n\n[... TRUNCATED ...]"

        # Chunks JSON
        chunks_data = [
            {
                "id": c["chunk_id"],
                "text": c["content"],
                "page": c.get("page"),
            }
            for c in chunks
        ]

        # Write files
        context_path = os.path.join(OUTPUT_DIR, f"{safe_name}.context.txt")
        chunks_path = os.path.join(OUTPUT_DIR, f"{safe_name}.chunks.json")

        with open(context_path, "w", encoding="utf-8") as f:
            f.write(full_context)

        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        context_kb = len(full_context) // 1024
        print(f"  {fname}")
        print(f"    → {len(chunks)} chunks, context {context_kb}KB")
        print(f"    → {safe_name}.context.txt + .chunks.json")

        summary.append({
            "filename": fname,
            "safe_name": safe_name,
            "chunks": len(chunks),
            "context_chars": len(full_context),
        })

    # Write summary
    summary_path = os.path.join(OUTPUT_DIR, "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Files exported to {OUTPUT_DIR}")
    print(f"Summary: {summary_path}")

    # Priority order for augmentation
    print("\n--- PRIORITY ORDER ---")
    priority = sorted(summary, key=lambda x: -x["chunks"])
    for i, s in enumerate(priority, 1):
        print(f"  {i}. {s['filename']} ({s['chunks']} chunks, {s['context_chars']//1024}KB)")


if __name__ == "__main__":
    main()
