#!/usr/bin/env python3
"""CLI for mega-session ingestion pipeline.

Usage:
    python3 scripts/ingest_mega_session.py SESSION-ID --dry-run
    python3 scripts/ingest_mega_session.py SESSION-ID --file /path/to/mega.jsonl
    python3 scripts/ingest_mega_session.py --estimate /path/to/mega.jsonl
    python3 scripts/ingest_mega_session.py --status SESSION-ID

Per SESSION-METRICS-01-v1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest Claude Code mega-session JSONL into ChromaDB + TypeDB"
    )
    parser.add_argument("session_id", nargs="?", help="Session ID to process")
    parser.add_argument("--file", "-f", help="Path to JSONL file")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Report without writing (default: off)")
    parser.add_argument("--no-resume", action="store_true",
                        help="Start fresh, ignoring existing checkpoint")
    parser.add_argument("--estimate", metavar="FILE",
                        help="Estimate work for a JSONL file")
    parser.add_argument("--status", metavar="SESSION_ID",
                        help="Show ingestion status for a session")
    parser.add_argument("--phases", nargs="+", default=["content", "linking"],
                        choices=["content", "linking"],
                        help="Phases to run (default: both)")
    parser.add_argument("--memory-limit", type=int, default=500,
                        help="Memory limit in MB (default: 500)")

    args = parser.parse_args()

    # --estimate mode
    if args.estimate:
        from governance.services.ingestion_orchestrator import estimate_ingestion
        result = estimate_ingestion(Path(args.estimate))
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "ok" else 1

    # --status mode
    if args.status:
        from governance.services.ingestion_orchestrator import get_ingestion_status
        result = get_ingestion_status(args.status)
        print(json.dumps(result, indent=2))
        return 0

    # Pipeline mode — requires session_id
    if not args.session_id:
        parser.error("session_id is required for ingestion")

    jsonl_path = None
    if args.file:
        jsonl_path = Path(args.file)
        if not jsonl_path.exists():
            print(f"Error: File not found: {jsonl_path}", file=sys.stderr)
            return 1
    else:
        # Auto-discover
        try:
            from governance.services.cc_session_scanner import find_jsonl_for_session
            jsonl_path = find_jsonl_for_session({"session_id": args.session_id})
        except Exception as e:
            print(f"Auto-discovery failed: {e}", file=sys.stderr)

        if jsonl_path is None:
            print(f"Error: No JSONL file found for {args.session_id}", file=sys.stderr)
            print("Use --file to specify the path explicitly", file=sys.stderr)
            return 1

    from governance.services.ingestion_orchestrator import run_ingestion_pipeline

    print(f"Session:  {args.session_id}")
    print(f"File:     {jsonl_path}")
    print(f"Phases:   {', '.join(args.phases)}")
    print(f"Dry-run:  {args.dry_run}")
    print(f"Resume:   {not args.no_resume}")
    print()

    result = run_ingestion_pipeline(
        jsonl_path,
        args.session_id,
        phases=args.phases,
        dry_run=args.dry_run,
        resume=not args.no_resume,
        memory_limit_mb=args.memory_limit,
    )

    print(json.dumps(result, indent=2))

    status = result.get("status", "error")
    if status == "success":
        print("\nIngestion complete.")
        return 0
    elif status == "partial":
        print("\nIngestion completed with errors (see above).")
        return 0
    else:
        print(f"\nIngestion failed: {status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
