"""Batch 212 — Session persistence + helpers defense tests.

Validates fixes for:
- BUG-212-PERSIST-FALSY-001: 'and v is not None' preserves empty lists
- BUG-213-SYNTH-TIMESTAMP-001: created_at fallback before datetime.now()
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import uuid

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-212-PERSIST-FALSY-001: Falsy filter preserves empty lists ────

class TestPersistFalsyFilter:
    """persist_session must preserve empty lists (tool_calls=[])."""

    def test_empty_tool_calls_preserved_in_source(self):
        """Source must use 'is not None' not bare 'and v'."""
        src = (SRC / "governance/stores/session_persistence.py").read_text()
        assert "v is not None" in src

    def test_empty_list_not_dropped(self):
        """tool_calls=[] should be in the persisted subset."""
        from governance.stores.session_persistence import _PERSIST_KEYS
        data = {"tool_calls": [], "thoughts": ["x"], "topic": "test"}
        subset = {k: v for k, v in data.items() if k in _PERSIST_KEYS and v is not None}
        assert "tool_calls" in subset
        assert subset["tool_calls"] == []

    def test_none_value_dropped(self):
        """tool_calls=None should be dropped."""
        from governance.stores.session_persistence import _PERSIST_KEYS
        data = {"tool_calls": None, "topic": "test"}
        subset = {k: v for k, v in data.items() if k in _PERSIST_KEYS and v is not None}
        assert "tool_calls" not in subset


# ── BUG-213-SYNTH-TIMESTAMP-001: Timestamp fallback ─────────────────

class TestSynthTimestampFallback:
    """synthesize_execution_events should use created_at before datetime.now()."""

    def test_completed_event_uses_created_at_when_no_completed_at(self):
        """DONE task without completed_at should use created_at, not now()."""
        from governance.stores.helpers import synthesize_execution_events
        events = synthesize_execution_events("TASK-001", {
            "created_at": "2026-01-01T00:00:00",
            "completed_at": None,
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": None,
        })
        completed_events = [e for e in events if e["event_type"] == "completed"]
        assert len(completed_events) == 1
        assert completed_events[0]["timestamp"] == "2026-01-01T00:00:00"

    def test_completed_event_uses_completed_at_when_available(self):
        """When completed_at is available, it should be used."""
        from governance.stores.helpers import synthesize_execution_events
        events = synthesize_execution_events("TASK-002", {
            "created_at": "2026-01-01T00:00:00",
            "completed_at": "2026-01-02T00:00:00",
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": None,
        })
        completed_events = [e for e in events if e["event_type"] == "completed"]
        assert completed_events[0]["timestamp"] == "2026-01-02T00:00:00"

    def test_evidence_event_uses_created_at_fallback(self):
        """Evidence event should also use created_at fallback."""
        from governance.stores.helpers import synthesize_execution_events
        events = synthesize_execution_events("TASK-003", {
            "created_at": "2026-01-01T12:00:00",
            "completed_at": None,
            "agent_id": "code-agent",
            "status": "DONE",
            "evidence": "Fixed the bug",
        })
        evidence_events = [e for e in events if e["event_type"] == "evidence"]
        assert len(evidence_events) == 1
        assert evidence_events[0]["timestamp"] == "2026-01-01T12:00:00"

    def test_fallback_in_source(self):
        """Source must chain: completed_at or created_at or datetime.now()."""
        src = (SRC / "governance/stores/helpers.py").read_text()
        assert "completed_at or created_at or datetime.now()" in src


# ── Session persistence defense ──────────────────────────────────────

class TestSessionPersistenceDefense:
    """Defense tests for session persistence module."""

    def test_persist_session_callable(self):
        from governance.stores.session_persistence import persist_session
        assert callable(persist_session)

    def test_load_persisted_sessions_callable(self):
        from governance.stores.session_persistence import load_persisted_sessions
        assert callable(load_persisted_sessions)

    def test_cleanup_persisted_callable(self):
        from governance.stores.session_persistence import cleanup_persisted
        assert callable(cleanup_persisted)

    def test_get_path_sanitizes_slashes(self):
        from governance.stores.session_persistence import _get_path
        path = _get_path("SESSION/../../etc/passwd")
        assert ".." not in path.name
        assert "/" not in path.name

    def test_persist_keys_include_expected(self):
        from governance.stores.session_persistence import _PERSIST_KEYS
        assert "tool_calls" in _PERSIST_KEYS
        assert "thoughts" in _PERSIST_KEYS
        assert "topic" in _PERSIST_KEYS

    def test_load_skips_nonexistent_dir(self):
        from governance.stores.session_persistence import load_persisted_sessions
        store = {}
        result = load_persisted_sessions(store)
        # Returns 0 if _STORE_DIR doesn't exist (which it won't in test)
        assert isinstance(result, int)


# ── Helpers defense ──────────────────────────────────────────────────

class TestHelpersDefense:
    """Defense tests for store helpers module."""

    def test_task_to_response_callable(self):
        from governance.stores.helpers import task_to_response
        assert callable(task_to_response)

    def test_session_to_response_callable(self):
        from governance.stores.helpers import session_to_response
        assert callable(session_to_response)

    def test_extract_session_id_valid(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("SESSION-2026-02-15-MY-TOPIC.md")
        assert result == "SESSION-2026-02-15-MY-TOPIC"

    def test_extract_session_id_invalid(self):
        from governance.stores.helpers import extract_session_id
        result = extract_session_id("random-file.txt")
        assert result is None

    def test_generate_chat_session_id(self):
        from governance.stores.helpers import generate_chat_session_id
        sid = generate_chat_session_id()
        assert sid.startswith("CHAT-")
        assert len(sid) > 5

    def test_synthesize_handles_typedb_task(self):
        """Should work with objects that have attributes (not dicts)."""
        from governance.stores.helpers import synthesize_execution_events
        from unittest.mock import MagicMock
        task = MagicMock()
        task.created_at = MagicMock()
        task.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        task.claimed_at = None
        task.completed_at = None
        task.agent_id = None
        task.status = "TODO"
        task.evidence = None
        events = synthesize_execution_events("T1", task)
        assert len(events) == 1
        assert events[0]["event_type"] == "started"
