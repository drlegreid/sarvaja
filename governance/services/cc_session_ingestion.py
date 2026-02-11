"""
Claude Code Session Ingestion Service.

Per SESSION-CC-01-v1, DATA-INGEST-01-v1: Ingest CC .jsonl sessions
into governance TypeDB with rich metadata and lazy loading support.

Created: 2026-02-11
"""

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.session_metrics.parser import (
    discover_log_files,
    parse_log_file,
    parse_log_file_extended,
)
from governance.services import sessions as session_service

logger = logging.getLogger(__name__)

# Default CC project directory
_DEFAULT_CC_DIR = Path.home() / ".claude" / "projects"


def _derive_project_slug(directory: Path) -> str:
    """Derive a project slug from the CC project directory name.

    CC encodes paths like: -home-user-Documents-project
    We extract the last 2 meaningful segments.
    """
    name = directory.name
    parts = [p for p in name.split("-") if p]
    if len(parts) >= 2:
        return "-".join(parts[-2:]).lower()
    return name.lower()


def _scan_jsonl_metadata(filepath: Path) -> Optional[Dict[str, Any]]:
    """Quick-scan a JSONL file for session metadata without full parse.

    Reads first/last lines + counts for summary. Much faster than full parse.
    """
    try:
        slug = filepath.stem
        file_size = filepath.stat().st_size
        if file_size == 0:
            return None

        first_ts = None
        last_ts = None
        session_uuid = None
        git_branch = None
        user_count = 0
        assistant_count = 0
        tool_use_count = 0
        thinking_chars = 0
        compaction_count = 0
        models_seen = set()

        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = obj.get("timestamp")
                if ts:
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts

                if not session_uuid:
                    session_uuid = obj.get("sessionId")
                if not git_branch:
                    git_branch = obj.get("gitBranch")

                entry_type = obj.get("type", "")
                if entry_type == "user":
                    user_count += 1
                elif entry_type == "assistant":
                    assistant_count += 1
                    msg = obj.get("message", {})
                    content = msg.get("content", []) if isinstance(msg, dict) else []
                    model = msg.get("model") if isinstance(msg, dict) else None
                    if model:
                        models_seen.add(model)
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "tool_use":
                                    tool_use_count += 1
                                elif block.get("type") == "thinking":
                                    thinking_chars += len(block.get("thinking", ""))
                elif entry_type == "system" and obj.get("compactMetadata"):
                    compaction_count += 1

        if not first_ts:
            return None

        return {
            "slug": slug,
            "session_uuid": session_uuid,
            "git_branch": git_branch,
            "first_ts": first_ts,
            "last_ts": last_ts,
            "user_count": user_count,
            "assistant_count": assistant_count,
            "tool_use_count": tool_use_count,
            "thinking_chars": thinking_chars,
            "compaction_count": compaction_count,
            "models": sorted(models_seen),
            "file_path": str(filepath),
            "file_size": file_size,
        }
    except Exception as e:
        logger.warning(f"Failed to scan {filepath.name}: {e}")
        return None


def _build_session_id(meta: Dict[str, Any], project_slug: str) -> str:
    """Build governance session ID from JSONL metadata."""
    date_str = meta["first_ts"][:10]
    name = meta["slug"].upper().replace(" ", "-")[:30]
    return f"SESSION-{date_str}-CC-{name}"


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


def _find_jsonl_for_session(session: Dict[str, Any]) -> Optional[Path]:
    """Find the JSONL file for a session by matching slug or UUID."""
    cc_uuid = session.get("cc_session_uuid")
    session_id = session.get("session_id", "")

    # Extract slug from session_id: SESSION-YYYY-MM-DD-CC-SLUG → SLUG
    parts = session_id.split("-CC-", 1)
    slug = parts[1].lower() if len(parts) == 2 else None

    for d in _DEFAULT_CC_DIR.iterdir():
        if not d.is_dir():
            continue
        for f in d.glob("*.jsonl"):
            if slug and slug in f.stem.lower():
                return f
            if cc_uuid and cc_uuid in f.stem:
                return f
    return None
