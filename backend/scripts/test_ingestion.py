"""Automated verification script for the WINDBOT document ingestion pipeline.

Tests 5 steps end-to-end:
1. Environment & dependencies check
2. Supabase connectivity
3. Test file parsing (markdown — no LlamaCloud API needed)
4. Vector store insert + query roundtrip
5. Cleanup of test data

Usage:
    cd backend
    python scripts/test_ingestion.py                 # Full end-to-end test
    python scripts/test_ingestion.py --dry-run       # Only validate setup, skip ingestion
    python scripts/test_ingestion.py --keep-data     # Skip cleanup (for debugging)

Exit codes:
    0: All checks PASS
    1: One or more checks FAIL
    2: Configuration error (env vars missing)
"""

import argparse
import asyncio
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402


class TestResult:
    """Collects PASS/FAIL results across all checks."""

    def __init__(self):
        self.checks = []

    def add(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        status = "PASS" if passed else "FAIL"
        icon = "✓" if passed else "✗"
        print(f"  {icon} {name}: {status}" + (f" — {detail}" if detail else ""))

    def summary(self) -> tuple[int, int]:
        passed = sum(1 for c in self.checks if c["passed"])
        total = len(self.checks)
        return passed, total

    def all_passed(self) -> bool:
        return all(c["passed"] for c in self.checks)


# ── Test 1: Environment ──────────────────────────────────────────────

def test_environment(result: TestResult) -> bool:
    """Check required env vars and Python dependencies."""
    print("\n[1/5] Environment & dependencies check")

    # Required env vars
    required_vars = {
        "OPENAI_API_KEY": settings.openai_api_key,
        "SUPABASE_URL": settings.supabase_url,
        "SUPABASE_SERVICE_KEY": settings.supabase_service_key,
        "SUPABASE_CONNECTION_STRING": settings.supabase_connection_string,
    }
    all_ok = True
    for name, value in required_vars.items():
        ok = bool(value and len(value) > 10)
        result.add(f"ENV {name}", ok, "set" if ok else "MISSING or too short")
        all_ok &= ok

    # Key Python dependencies
    try:
        import vecs  # noqa
        import supabase  # noqa
        import llama_index.core  # noqa
        import llama_index.vector_stores.supabase  # noqa
        result.add("Dependencies import", True, "vecs, supabase, llama_index OK")
    except ImportError as e:
        result.add("Dependencies import", False, f"missing: {e}")
        all_ok = False

    return all_ok


# ── Test 2: Supabase connectivity ────────────────────────────────────

def test_supabase(result: TestResult) -> bool:
    """Check Supabase client can connect and query tables."""
    print("\n[2/5] Supabase connectivity")

    try:
        from supabase import create_client

        client = create_client(
            settings.supabase_url, settings.supabase_service_key,
        )

        # Probe documents_metadata
        response = client.table("documents_metadata").select("id").limit(1).execute()
        result.add("Query documents_metadata", True, f"{len(response.data)} rows sampled")

        # Probe chunk_fts (needed for BM25)
        response = client.table("chunk_fts").select("chunk_id").limit(1).execute()
        result.add("Query chunk_fts", True, f"{len(response.data)} rows sampled")

        return True
    except Exception as e:
        result.add("Supabase connection", False, str(e)[:120])
        return False


# ── Test 3: Parse simple markdown ────────────────────────────────────

def test_parse(result: TestResult, test_file: Path) -> bool:
    """Test that SimpleDirectoryReader can parse our test file."""
    print("\n[3/5] Document parsing")

    try:
        from app.services.ingestion import parse_with_simple_reader

        docs = parse_with_simple_reader(str(test_file), language="vi")
        ok = len(docs) > 0 and all(d.text.strip() for d in docs)
        result.add(
            "Parse test file",
            ok,
            f"{len(docs)} document(s), {sum(len(d.text) for d in docs)} chars",
        )

        # Verify required metadata
        if docs:
            meta_ok = all(
                d.metadata.get("language") == "vi"
                and d.metadata.get("domain") == "wind_turbine"
                and "filename" in d.metadata
                for d in docs
            )
            result.add("Metadata enriched", meta_ok, "language/domain/filename set")
            return ok and meta_ok
        return ok
    except Exception as e:
        result.add("Parse test file", False, str(e)[:120])
        return False


# ── Test 4: Ingest + query roundtrip ─────────────────────────────────

async def test_ingest_roundtrip(result: TestResult, test_file: Path, test_tag: str) -> list:
    """Test full ingest pipeline and verify chunks are queryable.

    Returns list of chunk IDs created (for cleanup).
    """
    print("\n[4/5] Ingest + query roundtrip")

    chunk_ids = []
    try:
        from app.services.ingestion import ingest_documents
        from app.services.rag import configure_settings, create_vector_store

        configure_settings()
        vector_store = create_vector_store(settings.supabase_connection_string)

        # Ingest (supabase_client=None to skip chunk_fts population —
        # we don't want to pollute FTS with test data)
        start = time.time()
        num_chunks = await ingest_documents(
            str(test_file),
            language="vi",
            vector_store=vector_store,
            tier="cost_effective",
            supabase_client=None,
        )
        elapsed = time.time() - start

        ok = num_chunks > 0
        result.add("Ingest creates chunks", ok, f"{num_chunks} chunks in {elapsed:.1f}s")
        if not ok:
            return chunk_ids

        # Query vector store to verify chunks exist and are retrievable
        import vecs
        vx = vecs.create_client(settings.supabase_connection_string)
        collection = vx.get_or_create_collection(name="wind_turbine_docs", dimension=1536)

        # Search by embedding of the test content (should find our chunks)
        from llama_index.embeddings.openai import OpenAIEmbedding
        embed = OpenAIEmbedding(model="text-embedding-3-small")
        query_vec = embed.get_query_embedding("tua-bin gió test chunk marker")

        hits = collection.query(data=query_vec, limit=10, include_metadata=True)
        # Filter hits by our test_tag in filename
        test_hits = [h for h in hits if test_tag in (h[1].get("filename", "") if len(h) > 1 else "")]

        ok = len(test_hits) > 0
        result.add(
            "Query finds test chunks",
            ok,
            f"{len(test_hits)}/{len(hits)} hits match test tag",
        )
        chunk_ids = [h[0] for h in test_hits]

        return chunk_ids
    except Exception as e:
        result.add("Ingest roundtrip", False, str(e)[:120])
        return chunk_ids


# ── Test 5: Cleanup ──────────────────────────────────────────────────

def test_cleanup(result: TestResult, chunk_ids: list) -> bool:
    """Remove test chunks from vector store."""
    print("\n[5/5] Cleanup")

    if not chunk_ids:
        result.add("Cleanup", True, "nothing to clean up")
        return True

    try:
        import vecs
        vx = vecs.create_client(settings.supabase_connection_string)
        collection = vx.get_or_create_collection(name="wind_turbine_docs", dimension=1536)
        collection.delete(ids=chunk_ids)

        result.add("Remove test chunks", True, f"deleted {len(chunk_ids)} chunks")
        return True
    except Exception as e:
        result.add("Remove test chunks", False, str(e)[:120])
        return False


# ── Main ─────────────────────────────────────────────────────────────

def create_test_fixture(test_tag: str) -> Path:
    """Create a small markdown test fixture (doesn't need LlamaCloud)."""
    content = f"""# Test Ingestion Document — {test_tag}

## Nội dung test

Đây là file test cho script `test_ingestion.py`.
Chứa nội dung về tua-bin gió để test full pipeline ingestion.

## Các thành phần của tua-bin gió

Tua-bin gió (wind turbine) là thiết bị chuyển đổi năng lượng gió thành điện năng.
Các thành phần chính gồm: cánh quạt (blades), vỏ tua-bin (nacelle), tháp (tower),
và máy phát điện (generator).

## Test chunk marker

Đánh dấu đặc biệt để phân biệt chunks test: {test_tag}
Nội dung này sẽ bị xóa sau khi test hoàn thành.
"""

    # Use filename with test_tag for easy identification
    tmp_dir = tempfile.gettempdir()
    test_file = Path(tmp_dir) / f"test_ingestion_{test_tag}.md"
    test_file.write_text(content, encoding="utf-8")
    return test_file


async def main():
    parser = argparse.ArgumentParser(
        description="Verify the WINDBOT document ingestion pipeline",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only validate setup (steps 1-3), skip ingestion + cleanup",
    )
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Skip cleanup (for debugging)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("WINDBOT Ingestion Pipeline Verification")
    print("=" * 70)
    print(f"Mode: {'DRY-RUN (setup only)' if args.dry_run else 'FULL (end-to-end)'}")

    result = TestResult()
    test_tag = f"testrun_{uuid.uuid4().hex[:8]}"
    test_file = create_test_fixture(test_tag)
    print(f"Test fixture: {test_file}")
    print(f"Test tag: {test_tag}")

    try:
        # Step 1
        if not test_environment(result):
            print("\nFAIL: Environment check failed. Fix env vars and retry.")
            return 2

        # Step 2
        if not test_supabase(result):
            print("\nFAIL: Supabase not reachable. Check .env and Supabase dashboard.")
            return 1

        # Step 3
        test_parse(result, test_file)

        if args.dry_run:
            print("\n[DRY-RUN] Skipping ingest roundtrip and cleanup.")
        else:
            # Step 4
            chunk_ids = await test_ingest_roundtrip(result, test_file, test_tag)

            # Step 5
            if args.keep_data:
                print(f"\n[--keep-data] Leaving {len(chunk_ids)} test chunks in DB.")
                print(f"Search tag: {test_tag}")
            else:
                test_cleanup(result, chunk_ids)

    finally:
        # Always remove local test file
        test_file.unlink(missing_ok=True)

    # Summary
    passed, total = result.summary()
    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed}/{total} checks passed")
    print("=" * 70)

    return 0 if result.all_passed() else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
