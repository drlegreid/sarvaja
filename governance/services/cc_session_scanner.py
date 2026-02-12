"""
CC Session JSONL Scanner — metadata extraction without full parse.

Per DOC-SIZE-01-v1: Extracted from cc_session_ingestion.py.
Fast JSONL scanning, project slug derivation, and session ID building.

Created: 2026-02-11
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default CC project directory
DEFAULT_CC_DIR = Path.home() / ".claude" / "projects"


def derive_project_slug(directory: Path) -> str:
    """Derive a project slug from the CC project directory name.

    CC encodes paths like: -home-user-Documents-project
    We extract the last 2 meaningful segments.
    """
    name = directory.name
    parts = [p for p in name.split("-") if p]
    if len(parts) >= 2:
        return "-".join(parts[-2:]).lower()
    return name.lower()


def scan_jsonl_metadata(filepath: Path) -> Optional[Dict[str, Any]]:
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


def build_session_id(meta: Dict[str, Any], project_slug: str) -> str:
    """Build governance session ID from JSONL metadata."""
    date_str = meta["first_ts"][:10]
    name = meta["slug"].upper().replace(" ", "-")[:30]
    return f"SESSION-{date_str}-CC-{name}"


def find_jsonl_for_session(session: Dict[str, Any]) -> Optional[Path]:
    """Find the JSONL file for a session by matching slug or UUID."""
    cc_uuid = session.get("cc_session_uuid")
    session_id = session.get("session_id", "")

    # Extract slug from session_id: SESSION-YYYY-MM-DD-CC-SLUG → SLUG
    parts = session_id.split("-CC-", 1)
    slug = parts[1].lower() if len(parts) == 2 else None

    if not DEFAULT_CC_DIR.is_dir():
        return None

    for d in DEFAULT_CC_DIR.iterdir():
        if not d.is_dir():
            continue
        for f in d.glob("*.jsonl"):
            if slug and slug in f.stem.lower():
                return f
            if cc_uuid and cc_uuid in f.stem:
                return f
    return None
