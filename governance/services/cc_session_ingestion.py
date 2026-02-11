"""
Claude Code Session Ingestion Service.

Per SESSION-CC-01-v1, DATA-INGEST-01-v1: Ingest CC .jsonl sessions
into governance TypeDB with rich metadata and lazy loading support.
Per DOC-SIZE-01-v1: JSONL scanning in cc_session_scanner.py.

Created: 2026-02-11
"""

import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.session_metrics.parser import (
    discover_log_files,
    parse_log_file,
)
from governance.services import sessions as session_service

# Re-export for backward compatibility
from governance.services.cc_session_scanner import (  # noqa: F401
    DEFAULT_CC_DIR as _DEFAULT_CC_DIR,
    derive_project_slug as _derive_project_slug,
    scan_jsonl_metadata as _scan_jsonl_metadata,
    build_session_id as _build_session_id,
    find_jsonl_for_session as _find_jsonl_for_session,
)

logger = logging.getLogger(__name__)


def ingest_session(
    jsonl_path: Path,
    project_slug: Optional[str] = None,
    project_id: Optional[str] = None,
    dry_run: bool = False,
) -> Optional[Dict[str, Any]]:
    """Ingest a single CC JSONL session into governance.

    Returns session dict on success, None on skip/failure.
    """
    meta = _scan_jsonl_metadata(jsonl_path)
    if not meta:
        return None

    if not project_slug:
        project_slug = _derive_project_slug(jsonl_path.parent)

    session_id = _build_session_id(meta, project_slug)

    # Check if already exists
    existing = session_service.get_session(session_id)
    if existing:
        logger.info(f"Session {session_id} already exists, skipping")
        return None

    # Determine status
    from datetime import datetime, timedelta
    try:
        last_mod = datetime.fromtimestamp(Path(meta["file_path"]).stat().st_mtime)
        is_active = (datetime.now() - last_mod) < timedelta(hours=2)
    except Exception:
        is_active = False

    description = f"CC session: {meta['slug']} ({meta['user_count']} user, {meta['assistant_count']} assistant, {meta['tool_use_count']} tools)"

    if dry_run:
        return {
            "session_id": session_id,
            "description": description,
            "status": "ACTIVE" if is_active else "COMPLETED",
            "cc_session_uuid": meta.get("session_uuid"),
            "cc_tool_count": meta["tool_use_count"],
            "dry_run": True,
        }

    result = session_service.create_session(
        session_id=session_id,
        description=description,
        agent_id="code-agent",
        source="cc-ingestion",
        cc_session_uuid=meta.get("session_uuid"),
        cc_project_slug=project_slug,
        cc_git_branch=meta.get("git_branch"),
        cc_tool_count=meta["tool_use_count"],
        cc_thinking_chars=meta["thinking_chars"],
        cc_compaction_count=meta["compaction_count"],
    )

    # Update timestamps
    if result:
        session_service.update_session(
            session_id=session_id,
            start_time=meta["first_ts"],
            end_time=meta["last_ts"] if not is_active else None,
            status="ACTIVE" if is_active else "COMPLETED",
            source="cc-ingestion",
        )

        # Link to project if provided
        if project_id:
            from governance.services.projects import link_session_to_project
            link_session_to_project(project_id, session_id)

    return result


def ingest_all(
    directory: Optional[Path] = None,
    project_slug: Optional[str] = None,
    project_id: Optional[str] = None,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Batch ingest all JSONL sessions from a CC project directory."""
    if directory is None:
        # Auto-discover: find the sarvaja project directory
        for d in _DEFAULT_CC_DIR.iterdir():
            if d.is_dir() and "sarvaja" in d.name.lower():
                directory = d
                break
    if directory is None or not directory.is_dir():
        logger.warning(f"CC project directory not found: {directory}")
        return []

    if not project_slug:
        project_slug = _derive_project_slug(directory)

    files = discover_log_files(directory, include_agents=False)
    results = []

    for f in files:
        if f.stat().st_size == 0:
            continue
        result = ingest_session(
            f, project_slug=project_slug,
            project_id=project_id, dry_run=dry_run,
        )
        if result:
            results.append(result)

    logger.info(f"Ingested {len(results)} sessions from {directory}")
    return results


def get_session_detail(
    session_id: str, zoom: int = 1,
) -> Optional[Dict[str, Any]]:
    """Lazy-load session detail at zoom level.

    zoom=0: summary (session metadata only)
    zoom=1: + tool breakdown + thinking summary
    zoom=2: + individual tool calls with inputs (paginated)
    zoom=3: + full tool outputs (paginated, from JSONL)
    """
    session = session_service.get_session(session_id)
    if not session:
        return None

    result = {
        "session_id": session_id,
        "zoom": zoom,
        "summary": {
            "status": session.get("status"),
            "description": session.get("description"),
            "start_time": session.get("start_time"),
            "end_time": session.get("end_time"),
            "cc_session_uuid": session.get("cc_session_uuid"),
            "cc_project_slug": session.get("cc_project_slug"),
            "cc_git_branch": session.get("cc_git_branch"),
            "cc_tool_count": session.get("cc_tool_count"),
            "cc_thinking_chars": session.get("cc_thinking_chars"),
            "cc_compaction_count": session.get("cc_compaction_count"),
        },
    }

    if zoom >= 1:
        # Find JSONL file for this session
        jsonl_path = _find_jsonl_for_session(session)
        if jsonl_path:
            tool_breakdown = Counter()
            thinking_total = 0
            for entry in parse_log_file(jsonl_path):
                for tu in entry.tool_uses:
                    tool_breakdown[tu.name] += 1
                thinking_total += entry.thinking_chars
            result["tool_breakdown"] = dict(tool_breakdown.most_common(20))
            result["thinking_summary"] = {
                "total_chars": thinking_total,
                "estimated_tokens": thinking_total // 4,
            }

    return result
