"""Re-ingest all documents with contextual chunking + FTS table population.

This script performs a complete re-ingestion of the knowledge base:
1. Reads each source document from data/knowledge_base/
2. Chunks using SentenceSplitter (same as original ingestion)
3. Augments each chunk with LLM-generated contextual prefix
4. Embeds the augmented chunks with text-embedding-3-small
5. Upserts into pgvector (vecs.wind_turbine_docs)
6. Inserts into chunk_fts table for BM25 search

Usage:
    cd backend
    python scripts/reindex_with_context.py
    python scripts/reindex_with_context.py --lite          # Use lighter prompt (faster)
    python scripts/reindex_with_context.py --dry-run       # Preview without writing
    python scripts/reindex_with_context.py --skip-context   # Re-ingest without contextual augmentation
"""

import argparse
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from app.config import settings as _settings  # noqa: E402
if _settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = _settings.openai_api_key

from openai import OpenAI  # noqa: E402
from supabase import create_client  # noqa: E402

from llama_index.core.node_parser import SentenceSplitter  # noqa: E402
from llama_index.core.schema import Document, TextNode  # noqa: E402
from llama_index.embeddings.openai import OpenAIEmbedding  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.contextual_chunking import (  # noqa: E402
    contextualize_chunks_batch,
)
from app.services.rag import configure_settings, create_vector_store  # noqa: E402

# Knowledge base directories to process
KB_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base", "technical"),
    os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base", "processes"),
]

# Supported file extensions
SUPPORTED_EXTENSIONS = {".md", ".txt"}


def discover_documents(dirs: list[str]) -> list[str]:
    """Find all supported documents in the knowledge base directories."""
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS and not f.startswith("."):
                files.append(os.path.join(d, f))
    return files


def read_document(file_path: str) -> str:
    """Read a document file and return its full text."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_document(text: str, filename: str, language: str = "en") -> list[TextNode]:
    """Split a document into chunks using SentenceSplitter.

    Uses the same parameters as the original ingestion pipeline:
    chunk_size=1024, chunk_overlap=200.
    """
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
    doc = Document(
        text=text,
        metadata={
            "language": language,
            "domain": "wind_turbine",
            "filename": filename,
        },
    )
    nodes = splitter.get_nodes_from_documents([doc])
    return nodes


def populate_chunk_fts(supabase_client, chunk_id: str, content: str, metadata: dict):
    """Insert a chunk into the chunk_fts table for BM25 search."""
    supabase_client.table("chunk_fts").upsert({
        "chunk_id": chunk_id,
        "content": content,
        "filename": metadata.get("filename", ""),
        "page": metadata.get("page"),
        "language": metadata.get("language", "vi"),
    }).execute()


async def reindex_document(
    file_path: str,
    language: str,
    vector_store,
    supabase_client,
    openai_client: OpenAI,
    embed_model: OpenAIEmbedding,
    use_lite: bool = False,
    skip_context: bool = False,
    dry_run: bool = False,
) -> int:
    """Re-ingest a single document with contextual chunking.

    Returns the number of chunks created.
    """
    filename = os.path.basename(file_path)
    full_text = read_document(file_path)

    # Step 1: Chunk the document
    nodes = chunk_document(full_text, filename, language)
    original_texts = [node.get_content() for node in nodes]

    print(f"  Chunked into {len(nodes)} chunks")

    # Step 2: Contextual augmentation
    if skip_context:
        augmented_texts = original_texts
        print("  Skipping contextual augmentation")
    else:
        def progress(current, total):
            print(f"  Contextualizing chunk {current}/{total}...", end="\r")

        augmented_texts = contextualize_chunks_batch(
            client=openai_client,
            whole_document=full_text,
            chunks=original_texts,
            model="gpt-4o-mini",
            use_lite=use_lite,
            progress_callback=progress,
        )
        print(f"  Contextualized {len(augmented_texts)} chunks          ")

    if dry_run:
        # Show a sample augmented chunk
        if augmented_texts:
            print(f"\n  --- Sample augmented chunk (first 500 chars) ---")
            print(f"  {augmented_texts[0][:500]}")
            print(f"  --- End sample ---\n")
        return len(nodes)

    # Step 3: Update node content with augmented text
    for node, aug_text in zip(nodes, augmented_texts):
        node.set_content(aug_text)

    # Step 4: Generate embeddings
    print("  Generating embeddings...", end=" ", flush=True)
    texts_to_embed = [node.get_content() for node in nodes]
    embeddings = await asyncio.to_thread(
        embed_model.get_text_embedding_batch, texts_to_embed
    )
    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding
    print("done")

    # Step 5: Upsert into pgvector via vecs
    print("  Upserting to vector store...", end=" ", flush=True)
    vector_store.add(nodes)
    print("done")

    # Step 6: Populate chunk_fts table for BM25
    # Use ORIGINAL text (not augmented) for BM25 so keyword search matches
    # actual document terms, not LLM-generated context paragraphs.
    # The augmented text is stored in pgvector for dense search.
    print("  Populating FTS table...", end=" ", flush=True)
    for node, orig_text in zip(nodes, original_texts):
        populate_chunk_fts(
            supabase_client,
            chunk_id=node.node_id,
            content=orig_text,
            metadata=node.metadata,
        )
    print("done")

    return len(nodes)


async def main():
    parser = argparse.ArgumentParser(
        description="Re-ingest knowledge base with contextual chunking + FTS"
    )
    parser.add_argument(
        "--language", default="en", choices=["en", "vi"],
        help="Document language (default: en)",
    )
    parser.add_argument(
        "--lite", action="store_true",
        help="Use lighter context prompt (faster, sends only title + headings)",
    )
    parser.add_argument(
        "--skip-context", action="store_true",
        help="Skip contextual augmentation (re-ingest with plain chunks)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview chunking and augmentation without writing to DB",
    )
    parser.add_argument(
        "--clear", action="store_true",
        help="Clear existing data before re-ingesting (WARNING: destructive)",
    )
    args = parser.parse_args()

    # Discover documents
    files = discover_documents(KB_DIRS)
    if not files:
        print("No documents found in knowledge base directories.")
        sys.exit(1)

    print(f"Found {len(files)} document(s):")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    print()

    # Initialize services
    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)
    openai_client = OpenAI()
    embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    supabase_client = create_client(
        settings.supabase_url, settings.supabase_service_key
    )

    # Clear existing data if requested
    if args.clear and not args.dry_run:
        print("Clearing existing data...")
        # Clear FTS table
        supabase_client.table("chunk_fts").delete().neq("chunk_id", "").execute()
        print("  chunk_fts cleared")
        # Note: vecs collection clearing should be done via vecs API
        # or by dropping and recreating the collection
        print("  WARNING: vecs collection not cleared. Use vecs API or SQL to clear manually.")
        print()

    # Process each document
    start_time = time.time()
    total_chunks = 0

    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        try:
            num_chunks = await reindex_document(
                file_path=file_path,
                language=args.language,
                vector_store=vector_store,
                supabase_client=supabase_client,
                openai_client=openai_client,
                embed_model=embed_model,
                use_lite=args.lite,
                skip_context=args.skip_context,
                dry_run=args.dry_run,
            )
            total_chunks += num_chunks
            print(f"  OK ({num_chunks} chunks)\n")
        except Exception as e:
            print(f"  FAILED: {e}\n")

    elapsed = time.time() - start_time
    mode = "dry-run" if args.dry_run else "live"
    context_mode = "lite" if args.lite else ("none" if args.skip_context else "full")

    print(f"{'='*50}")
    print(f"Reindexing complete ({mode})")
    print(f"  Documents:  {len(files)}")
    print(f"  Chunks:     {total_chunks}")
    print(f"  Context:    {context_mode}")
    print(f"  Time:       {elapsed:.1f}s")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
