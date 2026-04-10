"""Re-embed augmented chunks and update pgvector database.

Reads augmented JSON files from augment_workspace/output/,
generates new embeddings with text-embedding-3-small, and
upserts to pgvector. Does NOT modify chunk_fts (BM25 keeps original text).

Usage (run as botai user on VPS):
    cd ~/botai/repo/backend
    ~/botai/repo/backend/venv/bin/python scripts/reembed_augmented.py
    ~/botai/repo/backend/venv/bin/python scripts/reembed_augmented.py --file AWEA
    ~/botai/repo/backend/venv/bin/python scripts/reembed_augmented.py --dry-run
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.config import settings
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

import vecs
from openai import OpenAI

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "augment_workspace", "output")
EMBED_BATCH_SIZE = 100  # OpenAI embedding batch limit


def main():
    parser = argparse.ArgumentParser(description="Re-embed augmented chunks")
    parser.add_argument("--file", type=str, help="Only process files matching this pattern")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()

    if not os.path.isdir(OUTPUT_DIR):
        print(f"Output directory not found: {OUTPUT_DIR}")
        sys.exit(1)

    # Find augmented JSON files
    augmented_files = sorted([
        f for f in os.listdir(OUTPUT_DIR)
        if f.endswith(".augmented.json")
    ])

    if args.file:
        augmented_files = [f for f in augmented_files if args.file.lower() in f.lower()]

    if not augmented_files:
        print("No augmented files found.")
        sys.exit(0)

    print(f"Found {len(augmented_files)} augmented file(s):")
    for f in augmented_files:
        print(f"  - {f}")
    print()

    # Initialize clients
    openai_client = OpenAI()

    if not args.dry_run:
        vx = vecs.create_client(settings.supabase_connection_string)
        collection = vx.get_or_create_collection("wind_turbine_docs", dimension=1536)

    total_updated = 0
    start_time = time.time()

    for filename in augmented_files:
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            items = json.load(f)

        print(f"Processing {filename}: {len(items)} chunks")

        if args.dry_run:
            # Show first augmented chunk as sample
            if items:
                sample = items[0]
                print(f"  Sample augmented text (first 300 chars):")
                print(f"  {sample['augmented'][:300]}")
            print(f"  [DRY RUN] Would update {len(items)} chunks\n")
            continue

        # Process in batches
        for i in range(0, len(items), EMBED_BATCH_SIZE):
            batch = items[i:i + EMBED_BATCH_SIZE]

            # Generate embeddings for augmented text
            texts = [item["augmented"] for item in batch]
            try:
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts,
                )
            except Exception as e:
                print(f"  ERROR embedding batch {i}-{i+len(batch)}: {e}")
                continue

            # Build upsert records: (id, vector, metadata)
            records = []
            for item, embed_obj in zip(batch, response.data):
                # Fetch existing metadata to preserve filename, page, etc.
                try:
                    existing = collection.fetch([item["id"]])
                    if existing and existing[0]:
                        old_meta = existing[0][2] if len(existing[0]) > 2 else {}
                    else:
                        old_meta = {}
                except Exception:
                    old_meta = {}

                # Update metadata with augmented text
                new_meta = {**old_meta}
                # The _node_content field contains serialized TextNode JSON
                # We need to update the text inside it
                if "_node_content" in new_meta:
                    try:
                        node_content = json.loads(new_meta["_node_content"])
                        node_content["text"] = item["augmented"]
                        new_meta["_node_content"] = json.dumps(node_content, ensure_ascii=False)
                    except (json.JSONDecodeError, KeyError):
                        pass

                records.append((
                    item["id"],
                    embed_obj.embedding,
                    new_meta,
                ))

            # Upsert to pgvector
            try:
                collection.upsert(records)
                total_updated += len(records)
                print(f"  Updated {i + len(batch)}/{len(items)} chunks")
            except Exception as e:
                print(f"  ERROR upserting batch {i}-{i+len(batch)}: {e}")

        print(f"  Done: {len(items)} chunks updated\n")

    elapsed = time.time() - start_time
    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"{'='*50}")
    print(f"Re-embedding complete ({mode})")
    print(f"  Files processed: {len(augmented_files)}")
    print(f"  Chunks updated:  {total_updated}")
    print(f"  Time:            {elapsed:.1f}s")
    print(f"  chunk_fts:       UNCHANGED (BM25 uses original text)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
