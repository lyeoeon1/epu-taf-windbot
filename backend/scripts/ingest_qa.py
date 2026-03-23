"""Ingest Q&A corpus JSON into the vector store.

Usage:
    cd backend
    python scripts/ingest_qa.py --input ./data/qa_corpus/benchmark-windbot-v1.json --language vi
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llama_index.core.ingestion import IngestionPipeline  # noqa: E402
from llama_index.core.node_parser import SentenceSplitter  # noqa: E402
from llama_index.core.schema import Document  # noqa: E402
from llama_index.embeddings.openai import OpenAIEmbedding  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.rag import configure_settings, create_vector_store  # noqa: E402


async def main():
    parser = argparse.ArgumentParser(description="Ingest Q&A corpus into vector store")
    parser.add_argument("--input", required=True, help="JSON file with Q&A pairs")
    parser.add_argument("--language", default="vi", choices=["en", "vi"])
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: {args.input} not found")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    configure_settings()
    vector_store = create_vector_store(settings.supabase_connection_string)

    documents = []
    if "categories" in data:
        # Benchmark format: {"categories": [{"name": ..., "pairs": [...]}]}
        for category in data.get("categories", []):
            cat_name = category["name"]
            for pair in category.get("pairs", []):
                text = f"Q: {pair['question']}\nA: {pair['expected_answer']}"
                doc = Document(
                    text=text,
                    metadata={
                        "language": args.language,
                        "domain": "wind_turbine",
                        "source_type": "qa_corpus",
                        "category": cat_name,
                        "qa_id": str(pair["id"]),
                        "difficulty": pair.get("difficulty", ""),
                        "filename": f"qa_corpus/{cat_name}",
                    },
                )
                documents.append(doc)
    elif "pairs" in data:
        # Generated Q&A format: {"category": ..., "pairs": [...]}
        cat_name = data.get("category", "general")
        for pair in data["pairs"]:
            answer = pair.get("expected_answer") or pair.get("answer", "")
            text = f"Q: {pair['question']}\nA: {answer}"
            doc = Document(
                text=text,
                metadata={
                    "language": args.language,
                    "domain": "wind_turbine",
                    "source_type": "qa_corpus",
                    "category": cat_name,
                    "qa_id": str(pair.get("id", "")),
                    "difficulty": pair.get("difficulty", ""),
                    "filename": f"qa_corpus/{cat_name}",
                },
            )
            documents.append(doc)

    print(f"Prepared {len(documents)} Q&A documents for ingestion")

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=1024, chunk_overlap=200),
            OpenAIEmbedding(model="text-embedding-3-small"),
        ],
        vector_store=vector_store,
    )

    nodes = await pipeline.arun(documents=documents)
    print(f"Done! Created {len(nodes)} chunks in vector store")


if __name__ == "__main__":
    asyncio.run(main())
