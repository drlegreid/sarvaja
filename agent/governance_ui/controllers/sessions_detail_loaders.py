"""
Session Detail Data Loaders.

Per DOC-SIZE-01-v1: Extracted from sessions.py (>300 lines).
Handles loading tool_calls, thinking_items, evidence, tasks, and timeline
for the session detail view.

Per EPIC-PERF-TELEM-V1 P4: Each loader has a fetch_* (pure HTTP, returns dict)
and a load_* (calls fetch + updates state). select_session uses fetch_* with
ThreadPoolExecutor; other callers use load_* directly.

Created: 2026-02-15
Updated: 2026-03-26 (P4: fetch/load split for parallel loading)
"""

import re

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace
from agent.governance_ui.controllers.traced_http import traced_get

# BUG-305-SDL-001: Validate session IDs before URL path interpolation
_SESSION_ID_RE = re.compile(r'^[A-Za-z0-9_\-\.\(\)]{1,200}$')


def _valid_session_id(session_id: str) -> bool:
    """Check session_id is safe for URL path interpolation."""
    return bool(session_id and isinstance(session_id, str)
                and len(session_id) <= 200 and _SESSION_ID_RE.match(session_id))


def _build_timeline_from_data(tool_calls, thinking_items):
    """Build chronological timeline from raw data (no state access).

    Args:
        tool_calls: list of tool call dicts
        thinking_items: list of thinking item dicts

    Returns:
        Sorted list of timeline entries.
    """
    timeline = []
    for call in (tool_calls or []):
        timeline.append({
            "type": "tool_call",
            "timestamp": call.get("timestamp", ""),
            "icon": "mdi-wrench",
            "title": call.get("tool_name") or call.get("name", "Unknown"),
            "subtitle": call.get("tool_category", ""),
            "detail": call.get("result", "")[:200] if call.get("result") else "",
            "success": call.get("success", True),
            "duration_ms": call.get("duration_ms", 0),
        })
    for thought in (thinking_items or []):
        timeline.append({
            "type": "thought",
            "timestamp": thought.get("timestamp", ""),
            "icon": "mdi-head-lightbulb",
            "title": thought.get("thought_type", "reasoning"),
            "subtitle": f"{thought.get('chars', thought.get('char_count', 0))} chars",
            "detail": thought.get("content", "")[:200] if thought.get("content") else "",
            "confidence": thought.get("confidence"),
        })
    # BUG-UI-TIMELINE-NULL-001: Guard against None timestamps crashing sort
    timeline.sort(key=lambda x: str(x.get("timestamp") or ""))
    return timeline


def register_session_detail_loaders(state: Any, api_base_url: str):
    """Register session detail data loaders.

    Returns dict with:
    - fetch_*: Pure HTTP functions returning data dict (thread-safe, no state mutation)
    - load_*: State-mutating wrappers (call fetch + update state)
    - build_timeline_data: Pure function to merge tools+thoughts into timeline
    """

    # ── fetch_* functions (pure HTTP, return dict) ──────────────

    def _fetch_tool_calls(session_id):
        """Fetch tool calls without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/tools",
                    params={"per_page": 100})
                if response.status_code == 200:
                    data = response.json()
                    calls = data.get('tool_calls', [])
                    for call in calls:
                        if 'name' in call and 'tool_name' not in call:
                            call['tool_name'] = call['name']
                    return {"session_tool_calls": calls}
        except Exception as e:
            return {"_error": f"Load tool calls failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/tools"}
        return {}

    def _fetch_thinking_items(session_id):
        """Fetch thinking items without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/thoughts",
                    params={"per_page": 100})
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('thinking_blocks', [])
                    for item in items:
                        if 'chars' in item and 'char_count' not in item:
                            item['char_count'] = item['chars']
                    return {"session_thinking_items": items}
        except Exception as e:
            return {"_error": f"Load thinking items failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/thoughts"}
        return {}

    def _fetch_evidence_rendered(session_id):
        """Fetch rendered HTML evidence without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            with httpx.Client(timeout=15.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/evidence/rendered")
                if response.status_code == 200:
                    data = response.json()
                    return {"session_evidence_html": data.get('html', '')}
        except Exception as e:
            return {"_error": f"Load evidence rendered failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/evidence/rendered"}
        return {}

    def _fetch_evidence(session_id):
        """Fetch evidence files without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/evidence")
                if response.status_code == 200:
                    data = response.json()
                    return {"evidence_files": data.get('evidence_files', [])}
        except Exception as e:
            return {"_error": f"Load evidence files failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/evidence"}
        return {}

    def _fetch_tasks(session_id):
        """Fetch tasks linked to session without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/tasks")
                if response.status_code == 200:
                    data = response.json()
                    return {"session_tasks": data.get('tasks', [])}
        except Exception as e:
            return {"_error": f"Load session tasks failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/tasks"}
        return {}

    def _fetch_transcript(session_id, page=1):
        """Fetch paginated transcript without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            params = {
                "page": page,
                "per_page": 50,
                "include_thinking": state.session_transcript_include_thinking,
                "include_user": state.session_transcript_include_user,
                "content_limit": 2000,
            }
            with httpx.Client(timeout=15.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/transcript",
                    params=params)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "session_transcript": data.get("entries", []),
                        "session_transcript_page": data.get("page", 1),
                        "session_transcript_total": data.get("total", 0),
                        "session_transcript_has_more": data.get("has_more", False),
                    }
                elif response.status_code == 404:
                    return {"session_transcript": [],
                            "session_transcript_total": 0}
        except Exception as e:
            return {"_error": f"Load transcript failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/transcript"}
        return {}

    def _fetch_validation(session_id):
        """Fetch content validation without mutating state. Traced via P5."""
        if not _valid_session_id(session_id):
            return {}
        try:
            with httpx.Client(timeout=15.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/validate")
                if response.status_code == 200:
                    return {"session_validation_data": response.json()}
        except Exception as e:
            return {"_error": f"Load validation failed: {type(e).__name__}",
                    "_endpoint": f"/api/sessions/{session_id}/validate"}
        return {}

    # ── load_* wrappers (state-mutating, for direct callers) ────

    def load_session_tool_calls(session_id):
        """Load tool calls and update state."""
        state.session_tool_calls_loading = True
        try:
            state.session_tool_calls = []
            result = _fetch_tool_calls(session_id)
            state.session_tool_calls = result.get("session_tool_calls", [])
            if "_error" in result:
                add_error_trace(state, result["_error"], result["_endpoint"])
        finally:
            state.session_tool_calls_loading = False

    def load_session_thinking_items(session_id):
        """Load thinking items and update state."""
        state.session_thinking_items_loading = True
        try:
            state.session_thinking_items = []
            result = _fetch_thinking_items(session_id)
            state.session_thinking_items = result.get("session_thinking_items", [])
            if "_error" in result:
                add_error_trace(state, result["_error"], result["_endpoint"])
        finally:
            state.session_thinking_items_loading = False

    def build_session_timeline():
        """Merge tool_calls + thinking_items from state into timeline."""
        state.session_timeline = _build_timeline_from_data(
            state.session_tool_calls, state.session_thinking_items
        )

    def load_session_evidence_rendered(session_id):
        """Load rendered evidence HTML and update state."""
        state.session_evidence_loading = True
        try:
            state.session_evidence_html = ''
            result = _fetch_evidence_rendered(session_id)
            state.session_evidence_html = result.get("session_evidence_html", '')
            if "_error" in result:
                add_error_trace(state, result["_error"], result["_endpoint"])
        finally:
            state.session_evidence_loading = False

    def load_session_evidence(session_id):
        """Load evidence files and merge into selected_session."""
        result = _fetch_evidence(session_id)
        files = result.get("evidence_files", [])
        if state.selected_session and files:
            session = dict(state.selected_session)
            session['evidence_files'] = files
            state.selected_session = session
        if "_error" in result:
            add_error_trace(state, result["_error"], result["_endpoint"])

    def load_session_tasks(session_id):
        """Load tasks and update state."""
        state.session_tasks_loading = True
        try:
            state.session_tasks = []
            result = _fetch_tasks(session_id)
            state.session_tasks = result.get("session_tasks", [])
            if "_error" in result:
                add_error_trace(state, result["_error"], result["_endpoint"])
        finally:
            state.session_tasks_loading = False

    def load_session_transcript(session_id, page=1):
        """Load transcript and update state."""
        state.session_transcript_loading = True
        try:
            state.session_transcript = []
            result = _fetch_transcript(session_id, page=page)
            state.session_transcript = result.get("session_transcript", [])
            state.session_transcript_page = result.get("session_transcript_page", 1)
            state.session_transcript_total = result.get("session_transcript_total", 0)
            state.session_transcript_has_more = result.get(
                "session_transcript_has_more", False
            )
            if "_error" in result:
                add_error_trace(state, result["_error"], result["_endpoint"])
        finally:
            state.session_transcript_loading = False

    def load_transcript_entry_expanded(session_id, entry_index):
        """Load a single transcript entry with full content (expand truncated)."""
        if not _valid_session_id(session_id):
            return
        entry_index = int(entry_index)  # BUG-305-SDL-001: enforce integer
        try:
            with httpx.Client(timeout=10.0) as client:
                response, _ = traced_get(
                    state, client, api_base_url,
                    f"/api/sessions/{session_id}/transcript/{entry_index}",
                    params={"content_limit": 50000})
                if response.status_code == 200:
                    data = response.json()
                    entry = data.get("entry", {})
                    updated = list(state.session_transcript)
                    for i, e in enumerate(updated):
                        if e.get("index") == entry_index:
                            updated[i] = entry
                            break
                    state.session_transcript = updated
                    state.session_transcript_expanded_entry = entry_index
        except Exception:
            pass  # traced_get already called add_error_trace

    def load_session_validation(session_id):
        """Load validation and update state."""
        state.session_validation_loading = True
        state.session_validation_data = None
        result = _fetch_validation(session_id)
        state.session_validation_data = result.get("session_validation_data")
        if "_error" in result:
            add_error_trace(state, result["_error"], result["_endpoint"])
        state.session_validation_loading = False

    return {
        # State-mutating loaders (existing API, backward compat)
        "load_tool_calls": load_session_tool_calls,
        "load_thinking_items": load_session_thinking_items,
        "build_timeline": build_session_timeline,
        "load_evidence_rendered": load_session_evidence_rendered,
        "load_evidence": load_session_evidence,
        "load_tasks": load_session_tasks,
        "load_transcript": load_session_transcript,
        "load_transcript_entry": load_transcript_entry_expanded,
        "load_validation": load_session_validation,
        # Pure fetchers (P4: for ThreadPoolExecutor parallel use)
        "fetch_tool_calls": _fetch_tool_calls,
        "fetch_thinking_items": _fetch_thinking_items,
        "fetch_evidence_rendered": _fetch_evidence_rendered,
        "fetch_evidence": _fetch_evidence,
        "fetch_tasks": _fetch_tasks,
        "fetch_transcript": _fetch_transcript,
        "fetch_validation": _fetch_validation,
        "build_timeline_data": _build_timeline_from_data,
    }
