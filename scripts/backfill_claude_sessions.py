#!/usr/bin/env python3
"""
Backfill governance sessions from Claude Code .jsonl raw files.

Scans Claude Code session logs and creates corresponding governance
sessions in TypeDB via the REST API. Extracts real timestamps, tool
counts, compaction counts, and session slugs.

Usage:
  python3 scripts/backfill_claude_sessions.py [--dry-run]

Created: 2026-02-11
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

API_BASE = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")

# Claude Code session logs directory
CLAUDE_LOGS_DIR = Path(
    os.getenv(
        "CLAUDE_LOGS_DIR",
        os.path.expanduser(
            "~/.claude/projects/-home-oderid-Documents-Vibe-sarvaja-platform"
        ),
    )
)


def _scan_jsonl(filepath: Path) -> dict | None:
    """Extract session metadata from a .jsonl file via streaming parse.

    Returns None if the file has too few entries or no timestamps.
    """
    slug = None
    session_uuid = None
    first_ts = None
    last_ts = None
    entry_count = 0
    user_count = 0
    assistant_count = 0
    tool_uses = 0
    compactions = 0
    models = set()
    first_user_text = None

    with open(filepath) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_count += 1
            ts = obj.get("timestamp")
            etype = obj.get("type", "")

            if ts:
                if first_ts is None or ts < first_ts:
                    first_ts = ts
                if last_ts is None or ts > last_ts:
                    last_ts = ts

            if not slug and etype == "system":
                slug = obj.get("slug")
            if not session_uuid:
                session_uuid = obj.get("sessionId")

            if etype == "user":
                user_count += 1
                if first_user_text is None:
                    msg = obj.get("message", {})
                    c = msg.get("content", "") if isinstance(msg, dict) else ""
                    if isinstance(c, str) and len(c) > 5:
                        first_user_text = c[:120]
                    elif isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type") == "text":
                                first_user_text = b.get("text", "")[:120]
                                break
            elif etype == "assistant":
                assistant_count += 1
                msg = obj.get("message", {})
                if isinstance(msg, dict):
                    m = msg.get("model")
                    if m and m != "<synthetic>":
                        models.add(m)
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for b in content:
                            if isinstance(b, dict) and b.get("type") == "tool_use":
                                tool_uses += 1
            elif etype == "system" and obj.get("compactMetadata"):
                compactions += 1

    if entry_count < 3 or not first_ts:
        return None

    # Determine session name from slug or filename
    name = slug or filepath.stem[:12]

    return {
        "file": filepath.name,
        "slug": slug,
        "session_uuid": session_uuid,
        "name": name,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "entries": entry_count,
        "users": user_count,
        "assistants": assistant_count,
        "tool_uses": tool_uses,
        "compactions": compactions,
        "models": sorted(models),
        "first_user_text": first_user_text,
        "size_mb": round(filepath.stat().st_size / 1024 / 1024, 1),
    }


def _build_session_id(meta: dict) -> str:
    """Build a governance session_id from JSONL metadata."""
    date_str = meta["first_ts"][:10]
    name = meta["name"].upper().replace(" ", "-")
    return f"SESSION-{date_str}-CC-{name}"


def _build_description(meta: dict) -> str:
    """Build a human-readable description from session metadata."""
    parts = [f"Claude Code session: {meta['name']}"]
    parts.append(
        f"{meta['entries']} entries, {meta['tool_uses']} tool calls, "
        f"{meta['compactions']} compactions"
    )
    if meta["models"]:
        parts.append(f"Models: {', '.join(meta['models'])}")
    if meta.get("first_user_text"):
        parts.append(f'First message: "{meta["first_user_text"]}"')
    return " | ".join(parts)


def _is_still_active(meta: dict) -> bool:
    """Check if session might still be active (modified recently)."""
    if not meta.get("last_ts"):
        return False
    try:
        last = datetime.fromisoformat(
            meta["last_ts"].replace("Z", "+00:00")
        )
        now = datetime.now(last.tzinfo)
        # Active if last entry within 2 hours
        return (now - last).total_seconds() < 7200
    except Exception:
        return False


def _format_ts(iso_ts: str) -> str:
    """Convert ISO timestamp to TypeDB-compatible format."""
    return iso_ts[:19].replace("Z", "")


def main():
    dry_run = "--dry-run" in sys.argv

    if not CLAUDE_LOGS_DIR.is_dir():
        logger.error("Claude logs directory not found: %s", CLAUDE_LOGS_DIR)
        sys.exit(1)

    # Discover .jsonl files (top-level only, skip agent- files)
    jsonl_files = sorted(
        (f for f in CLAUDE_LOGS_DIR.glob("*.jsonl") if f.stat().st_size > 100),
        key=lambda f: f.stat().st_mtime,
    )
    logger.info("Found %d non-empty JSONL files in %s", len(jsonl_files), CLAUDE_LOGS_DIR)

    # Fetch existing sessions to avoid duplicates
    existing_ids = set()
    try:
        resp = httpx.get(f"{API_BASE}/api/sessions?limit=200", timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        sessions = data.get("sessions", data.get("items", []))
        existing_ids = {s.get("session_id") for s in sessions}
        logger.info("Existing sessions in TypeDB: %d", len(existing_ids))
    except Exception as e:
        logger.warning("Could not fetch existing sessions: %s", e)

    # Parse and create
    created = 0
    skipped = 0
    failed = 0

    for filepath in jsonl_files:
        logger.info("\nScanning %s ...", filepath.name)
        meta = _scan_jsonl(filepath)
        if meta is None:
            logger.info("  Skipped (too few entries or no timestamps)")
            skipped += 1
            continue

        session_id = _build_session_id(meta)
        if session_id in existing_ids:
            logger.info("  Skipped %s (already exists)", session_id)
            skipped += 1
            continue

        is_active = _is_still_active(meta)
        status = "ACTIVE" if is_active else "COMPLETED"
        description = _build_description(meta)

        logger.info("  %s %s [%s]", "DRY-RUN" if dry_run else "CREATE", session_id, status)
        logger.info("    %s", description[:120])
        logger.info("    Period: %s → %s", meta["first_ts"][:16], meta["last_ts"][:16])

        if dry_run:
            created += 1
            continue

        # Create session via REST API
        try:
            payload = {
                "session_id": session_id,
                "description": description,
                "agent_id": "code-agent",
            }
            r = httpx.post(
                f"{API_BASE}/api/sessions",
                json=payload,
                timeout=10.0,
            )
            if r.status_code not in (200, 201):
                logger.warning("    Create failed: HTTP %d: %s", r.status_code, r.text[:200])
                failed += 1
                continue

            # Update with real timestamps
            update = {
                "start_time": _format_ts(meta["first_ts"]),
                "end_time": _format_ts(meta["last_ts"]),
            }
            if not is_active:
                update["status"] = "COMPLETED"

            r2 = httpx.put(
                f"{API_BASE}/api/sessions/{session_id}",
                json=update,
                timeout=10.0,
            )
            if r2.status_code not in (200, 204):
                logger.warning("    Update failed: HTTP %d", r2.status_code)

            created += 1
            existing_ids.add(session_id)
        except Exception as e:
            logger.warning("    Failed: %s", e)
            failed += 1

    logger.info("\n--- Summary ---")
    logger.info("Created: %d | Skipped: %d | Failed: %d", created, skipped, failed)

    if dry_run:
        logger.info("(Dry run — no changes made)")


if __name__ == "__main__":
    main()
