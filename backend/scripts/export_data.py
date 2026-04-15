"""
Export all Supabase data for backup/handover purposes.

Usage:
    python -m scripts.export_data
    python -m scripts.export_data --output-dir /path/to/backup

Exports all application tables to JSON files inside a timestamped directory.
Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in the .env file.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from supabase import create_client

from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

TABLES = [
    "chat_sessions",
    "chat_messages",
    "documents_metadata",
    "glossary",
    "global_corrections",
    "message_feedback",
]


def export_table(client, table_name: str) -> list[dict]:
    """Fetch all rows from a Supabase table. Returns empty list on failure."""
    try:
        response = client.table(table_name).select("*").execute()
        data = response.data
        logger.info(f"  {table_name}: {len(data)} rows")
        return data
    except Exception as e:
        logger.error(f"  {table_name}: failed to export — {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Export Supabase data for backup")
    parser.add_argument(
        "--output-dir",
        default="./export",
        help="Base output directory (default: ./export)",
    )
    args = parser.parse_args()

    # Validate config
    if not settings.supabase_url or not settings.supabase_service_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)

    # Create timestamped export directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = Path(args.output_dir) / f"export_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting to {export_dir}")

    # Connect to Supabase
    client = create_client(settings.supabase_url, settings.supabase_service_key)

    # Export each table
    summary_lines = []
    total_size = 0

    for table_name in TABLES:
        data = export_table(client, table_name)

        output_file = export_dir / f"{table_name}.json"
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        output_file.write_text(content, encoding="utf-8")

        file_size = output_file.stat().st_size
        total_size += file_size
        summary_lines.append(f"  {table_name}: {len(data)} rows ({file_size:,} bytes)")

    # Write summary report
    summary_path = export_dir / "export_summary.txt"
    summary = (
        f"Supabase Data Export Summary\n"
        f"{'=' * 40}\n"
        f"Export date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Output dir:  {export_dir.resolve()}\n\n"
        f"Tables:\n"
        + "\n".join(summary_lines)
        + f"\n\nTotal data size: {total_size:,} bytes\n"
    )
    summary_path.write_text(summary, encoding="utf-8")

    logger.info(f"Export complete. Summary written to {summary_path}")
    print(f"\n{summary}")


if __name__ == "__main__":
    main()
