"""
Session Detail Data Loaders.

Per DOC-SIZE-01-v1: Extracted from sessions.py (>300 lines).
Handles loading tool_calls, thinking_items, evidence, tasks, and timeline
for the session detail view.

Created: 2026-02-15
"""

import re

import httpx
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_error_trace

# BUG-305-SDL-001: Validate session IDs before URL path interpolation
_SESSION_ID_RE = re.compile(r'^[A-Za-z0-9_\-]+$')


def _valid_session_id(session_id: str) -> bool:
    """Check session_id is safe for URL path interpolation."""
    return bool(session_id and isinstance(session_id, str)
                and len(session_id) <= 200 and _SESSION_ID_RE.match(session_id))


def register_session_detail_loaders(state: Any, api_base_url: str):
    """Register session detail data loaders. Returns dict of loader functions."""

    def load_session_tool_calls(session_id):
        """Load tool calls via detail.py zoom endpoint (JSONL-backed)."""
        if not _valid_session_id(session_id):
            return
        state.session_tool_calls_loading = True
        try:
            state.session_tool_calls = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions/{session_id}/tools",
                    params={"per_page": 100},
                )
                if response.status_code == 200:
                    data = response.json()
                    calls = data.get('tool_calls', [])
                    for call in calls:
                        if 'name' in call and 'tool_name' not in call:
                            call['tool_name'] = call['name']
                    state.session_tool_calls = calls
        except Exception as e:
            # BUG-449-SDL-001: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load tool calls failed: {type(e).__name__}", f"/api/sessions/{session_id}/tools")
            state.session_tool_calls = []
        finally:
            state.session_tool_calls_loading = False

    def load_session_thinking_items(session_id):
        """Load thinking items via detail.py zoom endpoint (JSONL-backed)."""
        if not _valid_session_id(session_id):
            return
        state.session_thinking_items_loading = True
        try:
            state.session_thinking_items = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions/{session_id}/thoughts",
                    params={"per_page": 100},
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('thinking_blocks', [])
                    for item in items:
                        if 'chars' in item and 'char_count' not in item:
                            item['char_count'] = item['chars']
                    state.session_thinking_items = items
        except Exception as e:
            # BUG-449-SDL-002: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load thinking items failed: {type(e).__name__}", f"/api/sessions/{session_id}/thoughts")
            state.session_thinking_items = []
        finally:
            state.session_thinking_items_loading = False

    def build_session_timeline():
        """Merge tool_calls + thinking_items into chronological timeline."""
        timeline = []
        for call in (state.session_tool_calls or []):
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
        for thought in (state.session_thinking_items or []):
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
        state.session_timeline = timeline

    def load_session_evidence_rendered(session_id):
        """Load rendered HTML evidence for inline preview."""
        if not _valid_session_id(session_id):
            return
        state.session_evidence_loading = True
        try:
            state.session_evidence_html = ''
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions/{session_id}/evidence/rendered"
                )
                if response.status_code == 200:
                    data = response.json()
                    state.session_evidence_html = data.get('html', '')
        except Exception as e:
            # BUG-449-SDL-003: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load evidence rendered failed: {type(e).__name__}", f"/api/sessions/{session_id}/evidence/rendered")
            state.session_evidence_html = ''
        finally:
            state.session_evidence_loading = False

    def load_session_evidence(session_id):
        """Load evidence files for a session and merge into selected_session."""
        if not _valid_session_id(session_id):
            return
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions/{session_id}/evidence")
                if response.status_code == 200:
                    data = response.json()
                    files = data.get('evidence_files', [])
                    if state.selected_session and files:
                        session = dict(state.selected_session)
                        session['evidence_files'] = files
                        state.selected_session = session
        except Exception as e:
            # BUG-449-SDL-004: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load evidence files failed: {type(e).__name__}", f"/api/sessions/{session_id}/evidence")

    def load_session_tasks(session_id):
        """Load tasks linked to a session."""
        if not _valid_session_id(session_id):
            return
        state.session_tasks_loading = True
        try:
            state.session_tasks = []
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/sessions/{session_id}/tasks")
                if response.status_code == 200:
                    data = response.json()
                    state.session_tasks = data.get('tasks', [])
                else:
                    state.session_tasks = []
        except Exception as e:
            # BUG-449-SDL-005: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load session tasks failed: {type(e).__name__}", f"/api/sessions/{session_id}/tasks")
            state.session_tasks = []
        finally:
            state.session_tasks_loading = False

    def load_session_transcript(session_id, page=1):
        """Load paginated conversation transcript (GAP-SESSION-TRANSCRIPT-001)."""
        if not _valid_session_id(session_id):
            return
        state.session_transcript_loading = True
        try:
            state.session_transcript = []
            params = {
                "page": page,
                "per_page": 50,
                "include_thinking": state.session_transcript_include_thinking,
                "include_user": state.session_transcript_include_user,
                "content_limit": 2000,
            }
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions/{session_id}/transcript",
                    params=params,
                )
                if response.status_code == 200:
                    data = response.json()
                    state.session_transcript = data.get("entries", [])
                    state.session_transcript_page = data.get("page", 1)
                    state.session_transcript_total = data.get("total", 0)
                    state.session_transcript_has_more = data.get("has_more", False)
                elif response.status_code == 404:
                    state.session_transcript = []
                    state.session_transcript_total = 0
        except Exception as e:
            # BUG-449-SDL-006: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load transcript failed: {type(e).__name__}", f"/api/sessions/{session_id}/transcript")
            state.session_transcript = []
        finally:
            state.session_transcript_loading = False

    def load_transcript_entry_expanded(session_id, entry_index):
        """Load a single transcript entry with full content (expand truncated)."""
        if not _valid_session_id(session_id):
            return
        entry_index = int(entry_index)  # BUG-305-SDL-001: enforce integer
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{api_base_url}/api/sessions/{session_id}/transcript/{entry_index}",
                    params={"content_limit": 50000},
                )
                if response.status_code == 200:
                    data = response.json()
                    entry = data.get("entry", {})
                    # Replace entry in current transcript list
                    updated = list(state.session_transcript)
                    for i, e in enumerate(updated):
                        if e.get("index") == entry_index:
                            updated[i] = entry
                            break
                    state.session_transcript = updated
                    state.session_transcript_expanded_entry = entry_index
        except Exception as e:
            # BUG-449-SDL-007: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Expand transcript entry failed: {type(e).__name__}", f"/api/sessions/{session_id}/transcript/{entry_index}")

    return {
        "load_tool_calls": load_session_tool_calls,
        "load_thinking_items": load_session_thinking_items,
        "build_timeline": build_session_timeline,
        "load_evidence_rendered": load_session_evidence_rendered,
        "load_evidence": load_session_evidence,
        "load_tasks": load_session_tasks,
        "load_transcript": load_session_transcript,
        "load_transcript_entry": load_transcript_entry_expanded,
    }
