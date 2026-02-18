"""
CC Session JSONL Scanner — metadata extraction without full parse.

Per DOC-SIZE-01-v1: Extracted from cc_session_ingestion.py.
Fast JSONL scanning, project slug derivation, and session ID building.

Created: 2026-02-11
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Default CC project directory — check env var first (container use)
_env_cc_dir = os.environ.get("CLAUDE_PROJECT_LOG_DIR")
DEFAULT_CC_DIR = Path(_env_cc_dir) if _env_cc_dir else Path.home() / ".claude" / "projects"


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

        # BUG-209-SCANNER-ENCODING-001: Specify encoding for non-UTF-8 locales
        with open(filepath, "r", encoding="utf-8") as f:
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
        # BUG-415-SCN-001: Add exc_info for stack trace preservation
        logger.warning(f"Failed to scan {filepath.name}: {e}", exc_info=True)
        return None


def build_session_id(meta: Dict[str, Any], project_slug: str) -> str:
    """Build governance session ID from JSONL metadata."""
    # BUG-SCANNER-001: Defensive .get() for external callers
    # BUG-SCANNER-DICT-GET-001: Use `or` to handle both missing AND None
    date_str = (meta.get("first_ts") or "1970-01-01")[:10]
    name = (meta.get("slug") or "unknown").upper().replace(" ", "-")[:30]
    return f"SESSION-{date_str}-CC-{name}"


def discover_cc_projects() -> list[Dict[str, Any]]:
    """Discover projects from CC directory structure.

    Scans ~/.claude/projects/ for subdirectories and derives project metadata.
    Returns list of dicts with project_id, name, path, session_count.
    """
    if not DEFAULT_CC_DIR.is_dir():
        return []

    projects = []
    try:
        entries = list(DEFAULT_CC_DIR.iterdir())
    except OSError as e:
        # BUG-SCANNER-001: Guard against directory vanishing between check and iteration
        # BUG-415-SCN-002: Upgrade debug→warning for operational OSError + exc_info
        logger.warning(f"CC directory iteration failed: {e}", exc_info=True)
        return []
    for d in entries:
        if not d.is_dir() or d.name.startswith("."):
            continue

        slug = derive_project_slug(d)
        # Decode directory name back to filesystem path
        # BUG-334-SCAN-001: Validate decoded path against user home to prevent path traversal
        # BUG-346-SCAN-001: Use is_relative_to() instead of startswith() to prevent
        # prefix-sibling bypass (e.g. /home/user-evil matching /home/user)
        decoded_path = "/" + d.name.lstrip("-").replace("-", "/")
        _home_path = Path.home()
        _decoded = Path(decoded_path)
        if not (_decoded.is_relative_to(_home_path) or _decoded.is_relative_to(Path("/tmp"))):
            decoded_path = str(d)

        # Count JSONL files as proxy for session count
        jsonl_count = len(list(d.glob("*.jsonl")))
        if jsonl_count == 0:
            continue

        # Build a human-readable name from slug
        name_parts = slug.split("-")
        name = " ".join(p.capitalize() for p in name_parts)

        projects.append({
            "project_id": f"PROJ-{slug.upper()}",
            "name": name,
            "path": decoded_path,
            "cc_directory": str(d),
            "session_count": jsonl_count,
        })

    return projects


# Project markers that indicate a directory is a project
_PROJECT_MARKERS = [
    "project.godot",   # Godot engine
    "CLAUDE.md",       # Claude Code project
    "package.json",    # Node.js
    "Cargo.toml",      # Rust
    "go.mod",          # Go
    "pyproject.toml",  # Python (modern)
    "setup.py",        # Python (legacy)
]


def discover_filesystem_projects(
    scan_dirs: list[str] = None,
    existing_paths: set[str] = None,
    existing_ids: set[str] = None,
) -> list[Dict[str, Any]]:
    """Discover projects from filesystem by scanning for project markers.

    Complements discover_cc_projects() by finding projects that don't have
    CC JSONL files (e.g., Godot games created via Claude Code sessions).

    Args:
        scan_dirs: List of parent directory paths to scan for subdirectories.
        existing_paths: Paths to exclude (already-known projects).
        existing_ids: Project IDs to exclude (already-known projects).

    Returns:
        List of dicts with project_id, name, path, project_type.
    """
    from governance.services.workspace_registry import detect_project_type

    if not scan_dirs:
        return []

    existing_paths = existing_paths or set()
    existing_ids = existing_ids or set()
    projects = []

    for scan_dir in scan_dirs:
        parent = Path(scan_dir)
        if not parent.is_dir():
            continue

        try:
            dir_entries = list(parent.iterdir())
        except OSError as e:
            # BUG-SCANNER-002: Guard against directory vanishing during scan
            # BUG-429-SCN-001: Log instead of silently swallowing
            logger.warning(f"Directory scan failed for {scan_dir}: {e}", exc_info=True)
            continue
        for d in dir_entries:
            if not d.is_dir() or d.name.startswith("."):
                continue

            # Check for project markers
            has_marker = any((d / marker).exists() for marker in _PROJECT_MARKERS)
            if not has_marker:
                continue

            path_str = str(d)
            if path_str in existing_paths:
                continue

            # Build project ID from directory name
            slug = d.name.upper().replace(" ", "-")
            project_id = f"PROJ-{slug}"
            if project_id in existing_ids:
                continue

            # Auto-detect project type
            proj_type = detect_project_type(path_str)

            # Build human-readable name
            name = d.name.replace("-", " ").replace("_", " ").title()

            projects.append({
                "project_id": project_id,
                "name": name,
                "path": path_str,
                "project_type": proj_type,
            })

    return projects


def find_jsonl_for_session(session: Union[Dict[str, Any], str]) -> Optional[Path]:
    """Find the JSONL file for a session by matching slug or UUID.

    Args:
        session: Dict with 'session_id' and optionally 'cc_session_uuid',
                 or a bare session_id string (for convenience).
    """
    if isinstance(session, str):
        session = {"session_id": session}
    cc_uuid = session.get("cc_session_uuid")
    session_id = session.get("session_id", "")

    # Extract slug from session_id: SESSION-YYYY-MM-DD-CC-SLUG → SLUG
    parts = session_id.split("-CC-", 1)
    slug = parts[1].lower() if len(parts) == 2 else None

    if not DEFAULT_CC_DIR.is_dir():
        return None

    def _match(f: Path) -> bool:
        return (slug and slug in f.stem.lower()) or (cc_uuid and cc_uuid in f.stem)

    # Check JSONL files directly in DEFAULT_CC_DIR (container flat mount)
    for f in DEFAULT_CC_DIR.glob("*.jsonl"):
        if _match(f):
            return f

    # Check subdirectories (host: ~/.claude/projects/{project-dir}/*.jsonl)
    # BUG-SCANNER-TOCTOU-001: Guard iterdir() like discover_cc_projects() does
    try:
        subdirs = list(DEFAULT_CC_DIR.iterdir())
    except OSError:
        return None
    for d in subdirs:
        if not d.is_dir():
            continue
        for f in d.glob("*.jsonl"):
            if _match(f):
                return f
    return None
