"""
Session Transcript API Routes.

Per GAP-SESSION-TRANSCRIPT-001: Paginated conversation transcript endpoint
returning the full conversation flow from CC JSONL files.

Created: 2026-02-15
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from governance.services import sessions as session_service
from governance.services.cc_session_scanner import find_jsonl_for_session
from governance.services.cc_transcript import (
    build_synthetic_transcript,
    get_transcript_page,
    stream_transcript,
)
from governance.services.evidence_transcript import (
    find_evidence_file,
    parse_evidence_transcript,
)
from governance.stores import _sessions_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


@router.get("/sessions/{session_id}/transcript")
def session_transcript(
    session_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    include_thinking: bool = Query(default=True),
    include_user: bool = Query(default=True),
    content_limit: int = Query(default=2000, ge=0, le=50000),
):
    """Get paginated conversation transcript for a session.

    Returns the full conversation flow: user prompts, assistant responses,
    tool calls with inputs, tool results with outputs, and thinking blocks.
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    jsonl_path = find_jsonl_for_session(session)
    if jsonl_path:
        result = get_transcript_page(
            filepath=jsonl_path,
            page=page,
            per_page=per_page,
            include_thinking=include_thinking,
            include_user_content=include_user,
            content_limit=content_limit,
        )
        result["session_id"] = session_id
        result["source"] = "jsonl"
        return result

    # Fallback: build synthetic transcript from in-memory session data
    session_data = _sessions_store.get(session_id, {})
    if session_data.get("tool_calls") or session_data.get("thoughts"):
        result = build_synthetic_transcript(
            session_data=session_data,
            page=page,
            per_page=per_page,
            include_thinking=include_thinking,
            content_limit=content_limit,
        )
        result["session_id"] = session_id
        return result

    # Fallback 2: parse evidence file from disk
    evidence_path = find_evidence_file(session_id)
    if evidence_path:
        result = parse_evidence_transcript(
            filepath=evidence_path,
            page=page,
            per_page=per_page,
            include_thinking=include_thinking,
            content_limit=content_limit,
        )
        result["session_id"] = session_id
        return result

    # No data available at all
    return {
        "entries": [],
        "total": 0,
        "page": 1,
        "per_page": per_page,
        "has_more": False,
        "session_id": session_id,
        "source": "none",
    }


@router.get("/sessions/{session_id}/transcript/{entry_index}")
def session_transcript_entry(
    session_id: str,
    entry_index: int,
    content_limit: int = Query(default=50000, ge=0),
):
    """Get a single transcript entry with expanded content.

    Used when user clicks "Show Full Content" on a truncated entry.
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    jsonl_path = find_jsonl_for_session(session)
    if jsonl_path:
        for entry in stream_transcript(
            jsonl_path,
            include_thinking=True,
            include_user_content=True,
            content_limit=content_limit,
            start_index=entry_index,
            max_entries=1,
        ):
            return {"session_id": session_id, "entry": entry.to_dict()}
        raise HTTPException(status_code=404, detail=f"Entry {entry_index} not found")

    # Fallback: rebuild synthetic transcript and find entry by index
    session_data = _sessions_store.get(session_id, {})
    if session_data:
        result = build_synthetic_transcript(
            session_data, page=1, per_page=10000, content_limit=content_limit,
        )
        for e in result["entries"]:
            if e.get("index") == entry_index:
                return {"session_id": session_id, "entry": e}

    # Fallback 2: parse evidence file
    evidence_path = find_evidence_file(session_id)
    if evidence_path:
        result = parse_evidence_transcript(
            filepath=evidence_path, page=1, per_page=10000,
            content_limit=content_limit,
        )
        for e in result["entries"]:
            if e.get("index") == entry_index:
                return {"session_id": session_id, "entry": e}

    raise HTTPException(status_code=404, detail=f"Entry {entry_index} not found")
