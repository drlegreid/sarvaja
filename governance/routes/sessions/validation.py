"""Session Content Validation Route.

Exposes deep JSONL integrity checks for CC sessions via REST API.
Validates tool call/result pairing, MCP metadata, thinking blocks,
and timestamp consistency.

Created: 2026-02-20
"""

import logging

from fastapi import APIRouter, HTTPException

from governance.services.cc_session_scanner import find_jsonl_for_session
from governance.services.session_content_validator import validate_session_content

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


@router.get("/sessions/{session_id}/validate")
def validate_session(session_id: str):
    """Validate CC session JSONL content integrity.

    Returns content validation metrics including:
    - Tool call / result pairing (orphaned calls/results)
    - MCP server metadata coverage
    - Thinking block statistics
    - Timestamp consistency
    """
    jsonl_path = find_jsonl_for_session(session_id)
    if not jsonl_path:
        raise HTTPException(
            status_code=404,
            detail=f"No JSONL file found for session {session_id}",
        )

    try:
        result = validate_session_content(str(jsonl_path))
    except Exception as e:
        logger.error(
            f"Content validation failed for {session_id}: {type(e).__name__}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {type(e).__name__}",
        )

    return result.to_dict()
