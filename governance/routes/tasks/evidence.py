"""Tasks Evidence Routes — Rendered evidence preview.

Per SRVJ-FEAT-009: Task detail evidence HTML preview.
Follows session evidence pattern (governance/routes/sessions/detail.py).

Endpoints:
- GET /tasks/{task_id}/evidence/rendered — Get linked evidence as rendered HTML
"""
import html
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from governance.services.cc_session_ingestion import render_markdown

logger = logging.getLogger(__name__)
router = APIRouter()

# Project root for path validation
_PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_EVIDENCE_DIR = os.path.join(_PROJECT_ROOT, "evidence")
_MAX_FILE_SIZE = 512 * 1024  # 512KB cap per file


@router.get("/tasks/{task_id}/evidence/rendered")
async def task_evidence_rendered(task_id: str):
    """Get linked evidence files rendered as HTML.

    Queries TypeDB for evidence-supports relations, reads each evidence file,
    renders markdown→HTML, and returns combined output.

    Returns:
        {task_id, evidence_files: [{source, html}], count}
    """
    from governance.stores import get_typedb_client

    client = get_typedb_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not available")

    # Query linked evidence files
    try:
        tid = task_id.replace('\\', '\\\\').replace('"', '\\"')
        query = f"""
            match
                $t isa task, has task-id "{tid}";
                (supporting-evidence: $e, supported-task: $t) isa evidence-supports;
                $e has evidence-source $src;
            select $src;
        """
        results = client._execute_query(query)
    except Exception as e:
        logger.error(f"Evidence query for {task_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evidence query failed: {type(e).__name__}")

    if not results:
        return {"task_id": task_id, "evidence_files": [], "count": 0}

    evidence_files = []
    for r in results:
        source = r.get("src")
        if not source:
            continue

        # Resolve path — evidence_source may be relative or absolute
        if os.path.isabs(source):
            file_path = source
        else:
            file_path = os.path.join(_PROJECT_ROOT, source)

        real_path = os.path.realpath(file_path)

        # Path traversal guard
        if not real_path.startswith(os.path.realpath(_PROJECT_ROOT) + os.sep):
            logger.warning(f"Path traversal blocked: {source}")
            continue

        p = Path(real_path)
        if not p.exists():
            evidence_files.append({
                "source": source,
                "html": f"<p><em>Evidence file not found: {html.escape(source)}</em></p>",
            })
            continue

        if p.stat().st_size > _MAX_FILE_SIZE:
            evidence_files.append({
                "source": source,
                "html": f"<p><em>File too large to render ({p.stat().st_size} bytes)</em></p>",
            })
            continue

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            evidence_files.append({
                "source": source,
                "html": render_markdown(content),
            })
        except Exception as e:
            evidence_files.append({
                "source": source,
                "html": f"<p><em>Read error: {html.escape(str(type(e).__name__))}</em></p>",
            })

    return {
        "task_id": task_id,
        "evidence_files": evidence_files,
        "count": len(evidence_files),
    }
