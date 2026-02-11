#!/usr/bin/env python3
"""
Backfill governance sessions from Claude Code .jsonl raw files.

Per DATA-INGEST-01-v1: Uses CCSessionIngestionService for consistent
metadata extraction and TypeDB persistence.

Usage:
  python3 scripts/backfill_claude_sessions.py [--dry-run] [--project PROJ-ID] [--dir PATH]

Options:
  --dry-run         Show what would be ingested without creating sessions
  --project PROJ-ID Associate ingested sessions with a project entity
  --dir PATH        Override CC project directory (default: auto-discover)

Created: 2026-02-11
Updated: 2026-02-11 - Migrated to CCSessionIngestionService (DATA-INGEST-01-v1)
"""

import os
import sys
import logging
from pathlib import Path

# Ensure project root is on path for governance imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill governance sessions from CC .jsonl files"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")
    parser.add_argument("--project", type=str, default=None, help="Project ID to link sessions to")
    parser.add_argument("--dir", type=str, default=None, help="CC project directory override")
    args = parser.parse_args()

    from governance.services.cc_session_ingestion import ingest_all
    from governance.services.cc_session_scanner import DEFAULT_CC_DIR

    directory = Path(args.dir) if args.dir else None

    if directory and not directory.is_dir():
        logger.error("Directory not found: %s", directory)
        sys.exit(1)

    if not directory:
        # Auto-discover sarvaja project dir
        for d in DEFAULT_CC_DIR.iterdir():
            if d.is_dir() and "sarvaja" in d.name.lower():
                directory = d
                break

    if not directory:
        logger.error("CC project directory not found. Use --dir to specify.")
        sys.exit(1)

    logger.info("Scanning: %s", directory)
    logger.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")
    if args.project:
        logger.info("Project: %s", args.project)

    results = ingest_all(
        directory=directory,
        project_id=args.project,
        dry_run=args.dry_run,
    )

    logger.info("\n--- Summary ---")
    logger.info("Ingested: %d sessions", len(results))

    for r in results:
        sid = r.get("session_id", "unknown")
        status = r.get("status", "?")
        tools = r.get("cc_tool_count", 0)
        dry = " (dry-run)" if r.get("dry_run") else ""
        logger.info("  %s [%s] %d tools%s", sid, status, tools, dry)

    if args.dry_run:
        logger.info("\n(Dry run — no changes made)")


if __name__ == "__main__":
    main()
