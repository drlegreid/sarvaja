"""
Files Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-DATA-003: File content reading.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import os

from governance.models import FileContentResponse

router = APIRouter(tags=["Files"])


# =============================================================================
# FILE CONTENT ENDPOINT
# =============================================================================

@router.get("/files/content", response_model=FileContentResponse)
async def get_file_content(path: str = Query(..., description="File path relative to project root")):
    """
    Read file content by path (GAP-DATA-003).

    Supports evidence files, session logs, and documentation.
    Security: Only allows reading from approved directories.
    """
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")

    # Allowed directories for security
    allowed_prefixes = ["evidence/", "docs/", "results/", "data/"]

    # Normalize path separators
    normalized_path = path.replace("\\", "/")

    # Security check: only allow reading from approved directories
    if not any(normalized_path.startswith(prefix) for prefix in allowed_prefixes):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Only files in {allowed_prefixes} can be read."
        )

    # Build full path
    full_path = os.path.join(project_root, normalized_path)

    # Prevent path traversal
    real_path = os.path.realpath(full_path)
    real_root = os.path.realpath(project_root)
    if not real_path.startswith(real_root):
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
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
