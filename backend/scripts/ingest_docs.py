"""CLI script to batch-ingest documents into the wind turbine knowledge base.

Usage:
    cd backend
    python scripts/ingest_docs.py --dir ./data --language en --tier agentic
"""

import argparse
import asyncio
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings  # noqa: E402
from app.services.ingestion import ingest_documents  # noqa: E402
from app.services.rag import configure_settings, create_vector_store  # noqa: E402


async def main():
    parser = argparse.ArgumentParser(
        description="Batch-ingest documents into the knowledge base"
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Directory containing documents to ingest",
    )
    parser.add_argument(
        "--language",
        default="en",
        choices=["en", "vi"],
        help="Language of the documents (default: en)",
    )
    parser.add_argument(
        "--tier",
        default="agentic",
        choices=["cost_effective", "agentic", "agentic_plus"],
        help="LlamaParse parsing tier (default: agentic)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"Error: {args.dir} is not a valid directory")
        sys.exit(1)

    # Initialize LlamaIndex settings and vector store
    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)

    # Find all files in directory
    files = [
        os.path.join(args.dir, f)
        for f in os.listdir(args.dir)
        if os.path.isfile(os.path.join(args.dir, f))
        and not f.startswith(".")
    ]

    if not files:
        print(f"No files found in {args.dir}")
        sys.exit(0)

    print(f"Found {len(files)} file(s) to ingest:")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    print()

    total_chunks = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"Ingesting {filename}...", end=" ", flush=True)
        try:
            num_chunks = await ingest_documents(
                file_path, args.language, vector_store, args.tier
            )
            total_chunks += num_chunks
            print(f"OK ({num_chunks} chunks)")
        except Exception as e:
            print(f"FAILED: {e}")

    print(f"\nDone! Total chunks created: {total_chunks}")


if __name__ == "__main__":
    asyncio.run(main())
