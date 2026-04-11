"""Auto-augment all exported chunks using gpt-4o-mini.

Reads chunks from augment_workspace/input/, augments with contextual
information, and writes results to augment_workspace/output/.

Resume-safe: skips successfully augmented chunks.

Usage:
    cd backend
    python scripts/augment_all_chunks.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from app.services.contextual_chunking import (
    CONTEXT_PROMPT_LITE,
    extract_document_title,
    extract_headings,
)

INPUT_DIR = os.path.join("augment_workspace", "input")
OUTPUT_DIR = os.path.join("augment_workspace", "output")


def get_document_pairs():
    pairs = []
    for fname in sorted(os.listdir(INPUT_DIR)):
        if fname.endswith(".chunks.json"):
            base = fname.replace(".chunks.json", "")
            context_file = os.path.join(INPUT_DIR, f"{base}.context.txt")
            chunks_file = os.path.join(INPUT_DIR, fname)
            output_file = os.path.join(OUTPUT_DIR, f"{base}.augmented.json")
            if os.path.exists(context_file):
                pairs.append({
                    "base": base,
                    "context_file": context_file,
                    "chunks_file": chunks_file,
                    "output_file": output_file,
                })
    return pairs


def augment_one_chunk(client, title, headings, chunk_text, max_retries=5):
    """Augment a single chunk with retry + exponential backoff."""
    prompt = CONTEXT_PROMPT_LITE.format(
        document_title=title,
        document_headings=headings,
        chunk_text=chunk_text[:2000],  # Truncate very long chunks
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            context = response.choices[0].message.content.strip()
            return f"[Ngữ cảnh: {context}]\n{chunk_text}"
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                wait = min(30, 5 * (2 ** attempt))  # 5, 10, 20, 30, 30
                print(f"      Rate limit, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                print(f"      Error: {error_str[:100]}")
                time.sleep(2)

    print(f"      FAILED after {max_retries} retries")
    return chunk_text  # Return original without augmentation


def augment_document(client, pair):
    with open(pair["context_file"], "r", encoding="utf-8") as f:
        whole_document = f.read()

    with open(pair["chunks_file"], "r", encoding="utf-8") as f:
        chunks = json.load(f)

    title = extract_document_title(whole_document)
    headings = extract_headings(whole_document, max_headings=30)

    print(f"\n  {pair['base']}")
    print(f"    {len(chunks)} chunks, title: {title[:60]}")

    # Load existing successful results
    existing_results = []
    done_ids = set()
    if os.path.exists(pair["output_file"]):
        try:
            with open(pair["output_file"], "r", encoding="utf-8") as f:
                all_existing = json.load(f)
            existing_results = [
                r for r in all_existing
                if r.get("augmented", "").startswith("[Ngữ cảnh:")
            ]
            done_ids = {r["id"] for r in existing_results}
            failed = len(all_existing) - len(existing_results)
            if failed:
                print(f"    Discarding {failed} failed entries")
        except (json.JSONDecodeError, KeyError):
            pass

    if len(done_ids) >= len(chunks):
        print(f"    Complete ({len(chunks)} chunks), skipping.")
        return len(chunks), 0

    if done_ids:
        print(f"    Resuming: {len(done_ids)}/{len(chunks)} done")

    remaining = [c for c in chunks if c["id"] not in done_ids]
    all_results = list(existing_results)
    start_time = time.time()

    for i, chunk in enumerate(remaining):
        augmented_text = augment_one_chunk(client, title, headings, chunk["text"])

        all_results.append({
            "id": chunk["id"],
            "original": chunk["text"],
            "augmented": augmented_text,
        })

        # Save every 20 chunks
        if (i + 1) % 20 == 0 or (i + 1) == len(remaining):
            with open(pair["output_file"], "w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)

            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(remaining) - (i + 1)) / rate if rate > 0 else 0
            print(f"    {len(all_results)}/{len(chunks)} ({rate:.1f}/s, ETA {eta:.0f}s)")

        # Small delay to stay within rate limits (~1K tokens per request)
        # 200K TPM / 1K per req = 200 req/min = 3.3 req/s
        time.sleep(0.5)

    elapsed = time.time() - start_time
    print(f"    Done in {elapsed:.1f}s")
    return len(chunks), len(remaining)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    client = OpenAI()
    pairs = get_document_pairs()

    print(f"Found {len(pairs)} documents")
    print(f"Using LITE mode (title+headings only) for all documents")
    print(f"Output: {OUTPUT_DIR}\n")

    total_chunks = 0
    total_new = 0
    start = time.time()

    # Smallest first
    pairs.sort(key=lambda p: os.path.getsize(p["chunks_file"]))

    for pair in pairs:
        c, n = augment_document(client, pair)
        total_chunks += c
        total_new += n

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"Done! {total_chunks} chunks, {total_new} newly augmented")
    print(f"Time: {elapsed:.0f}s ({elapsed/60:.1f}m)")


if __name__ == "__main__":
    main()
