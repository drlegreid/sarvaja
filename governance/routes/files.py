"""
Files Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-DATA-003: File content reading.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

from governance.models import FileContentResponse

router = APIRouter(tags=["Files"])


# =============================================================================
# FILE CONTENT ENDPOINT
# =============================================================================

@router.get("/files/content", response_model=FileContentResponse)
async def get_file_content(path: str = Query(..., description="File path relative to project root")):
    """
    Read file content by path (GAP-DATA-003).

    Supports evidence files, screenshots, logs, plans, and documentation.
    Local dev mode: all project-relative and home-claude paths allowed.
    Path traversal prevention remains active.
    """
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")

    # Normalize path separators
    normalized_path = path.replace("\\", "/")

    # Reject obviously dangerous patterns
    if ".." in normalized_path or normalized_path.startswith("/"):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")

    # Resolve path — try multiple roots for portability (host vs container)
    # Container: project at /app, home-claude at /app/home-claude (maps to ~/.claude)
    # Host: project at cwd, home .claude at ~/.claude
    home_claude_dir = os.path.join(project_root, "home-claude")  # Container mount

    # Build search candidates: (root_dir, relative_path) pairs
    search_candidates = [
        (project_root, normalized_path),                           # Project root as-is
        (os.path.expanduser("~"), normalized_path),                # Host home as-is
    ]
    # .claude/ paths also map to home-claude/ mount (strip .claude/ prefix)
    if normalized_path.startswith(".claude/"):
        stripped = normalized_path[len(".claude/"):]  # plans/gleaming-drifting-pearl.md
        search_candidates.insert(1, (home_claude_dir, stripped))   # Container: /app/home-claude/plans/...

    full_path = None
    matched_root = None
    for root, rel_path in search_candidates:
        real_root = os.path.realpath(root)
        candidate = os.path.join(real_root, rel_path)
        real_candidate = os.path.realpath(candidate)
        if real_candidate.startswith(real_root + os.sep) and os.path.exists(real_candidate):
            full_path = candidate
            matched_root = real_root
            break

    if full_path is None:
        # No existing file found — default to project root for the 404
        full_path = os.path.join(project_root, normalized_path)
        matched_root = os.path.realpath(project_root)

    # Final traversal guard
    real_path = os.path.realpath(full_path)
    if not real_path.startswith(matched_root + os.sep) and real_path != matched_root:
        raise HTTPException(status_code=403, detail="Path traversal not allowed")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=400, detail=f"Not a file: {path}")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        stat = os.stat(full_path)
        response = FileContentResponse(
            path=normalized_path,
            content=content,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

        # Render markdown to HTML for .md files
        if normalized_path.endswith(".md"):
            from governance.services.cc_session_ingestion import render_markdown
            response.rendered_html = render_markdown(content)

        return response
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cannot read binary files")
    except Exception as e:
        # BUG-475-FIL-1: Sanitize HTTPException detail — prevent exception detail leakage to API clients
        logger.error(f"Error reading file: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
