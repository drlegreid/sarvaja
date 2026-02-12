"""
Unit tests for Session Service Layer.

Per DOC-SIZE-01-v1: Tests for governance/services/sessions.py module.
Tests: list_sessions, create_session, get_session, update_session.
"""

from unittest.mock import MagicMock, patch

import pytest

_P = "governance.services.sessions"


@pytest.fixture(autouse=True)
def _patch_deps():
    with patch(f"{_P}.record_audit"), \
         patch(f"{_P}.log_event"), \
         patch(f"{_P}._monitor"):
        yield


@pytest.fixture(autouse=True)
def _patch_sessions_store():
    with patch(f"{_P}._sessions_store", {
        "S-1": {
            "session_id": "S-1", "status": "ACTIVE",
            "start_time": "2026-01-01T10:00:00", "description": "Test",
            "agent_id": "code-agent", "tasks_completed": 0,
        },
        "S-2": {
            "session_id": "S-2", "status": "COMPLETED",
            "start_time": "2026-01-01T09:00:00", "description": "Done",
            "agent_id": "test-agent", "tasks_completed": 3,
        },
    }) as store:
        yield store


# ── list_sessions ────────────────────────────────────────────────


class TestListSessions:
    def test_returns_all(self):
        from governance.services.sessions import list_sessions
        with patch(f"{_P}.get_all_sessions_from_typedb", return_value=[
            {"session_id": "S-1", "status": "ACTIVE", "start_time": "2026-01-01T10:00:00",
             "agent_id": "code-agent"},
            {"session_id": "S-2", "status": "COMPLETED", "start_time": "2026-01-01T09:00:00",
             "agent_id": "test-agent"},
        ]):
            result = list_sessions()
        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_filter_by_status(self):
        from governance.services.sessions import list_sessions
        with patch(f"{_P}.get_all_sessions_from_typedb", return_value=[
            {"session_id": "S-1", "status": "ACTIVE", "start_time": "t1"},
            {"session_id": "S-2", "status": "COMPLETED", "start_time": "t2"},
        ]):
            result = list_sessions(status="ACTIVE")
        assert result["total"] == 1
        assert result["items"][0]["session_id"] == "S-1"

    def test_filter_by_agent(self):
        from governance.services.sessions import list_sessions
        with patch(f"{_P}.get_all_sessions_from_typedb", return_value=[
            {"session_id": "S-1", "status": "ACTIVE", "agent_id": "code-agent"},
            {"session_id": "S-2", "status": "COMPLETED", "agent_id": "test-agent"},
        ]):
            result = list_sessions(agent_id="test-agent")
        assert result["total"] == 1

    def test_pagination(self):
        from governance.services.sessions import list_sessions
        sessions = [{"session_id": f"S-{i}", "status": "ACTIVE", "start_time": f"t{i}"}
                     for i in range(5)]
        with patch(f"{_P}.get_all_sessions_from_typedb", return_value=sessions):
            result = list_sessions(offset=0, limit=2)
        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["has_more"] is True

    def test_sorting_desc(self):
        from governance.services.sessions import list_sessions
        with patch(f"{_P}.get_all_sessions_from_typedb", return_value=[
            {"session_id": "S-1", "start_time": "2026-01-01"},
            {"session_id": "S-2", "start_time": "2026-01-02"},
        ]):
            result = list_sessions(order="desc")
        assert result["items"][0]["start_time"] == "2026-01-02"


# ── create_session ───────────────────────────────────────────────


class TestCreateSession:
    def test_typedb_success(self):
        from governance.services.sessions import create_session
        mock_client = MagicMock()
        created_session = MagicMock()
        mock_client.insert_session.return_value = created_session
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.session_to_response", return_value={"session_id": "S-NEW"}):
            result = create_session(session_id="S-NEW", description="New")
        assert result["session_id"] == "S-NEW"

    def test_fallback_success(self):
        from governance.services.sessions import create_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = create_session(session_id="S-NEW", description="New")
        assert result["session_id"] == "S-NEW"
        assert result["status"] == "ACTIVE"

    def test_fallback_duplicate(self):
        from governance.services.sessions import create_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            with pytest.raises(ValueError, match="already exists"):
                create_session(session_id="S-1")

    def test_auto_generate_id(self):
        from governance.services.sessions import create_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = create_session(description="Auto ID")
        assert result["session_id"].startswith("SESSION-")

    def test_typedb_failure_fallback(self):
        from governance.services.sessions import create_session
        mock_client = MagicMock()
        mock_client.insert_session.side_effect = Exception("DB error")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = create_session(session_id="S-FALLBACK", description="FB")
        assert result["session_id"] == "S-FALLBACK"

    def test_cc_fields_stored(self):
        from governance.services.sessions import create_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = create_session(
                session_id="S-CC", description="CC session",
                cc_session_uuid="uuid-123", cc_project_slug="sarvaja",
                cc_git_branch="master", cc_tool_count=42,
            )
        assert result["cc_session_uuid"] == "uuid-123"
        assert result["cc_project_slug"] == "sarvaja"
        assert result["cc_tool_count"] == 42


# ── get_session ──────────────────────────────────────────────────


class TestGetSession:
    def test_found(self):
        from governance.services.sessions import get_session
        with patch(f"{_P}.get_session_from_typedb", return_value={"session_id": "S-1"}):
            result = get_session("S-1")
        assert result["session_id"] == "S-1"

    def test_not_found(self):
        from governance.services.sessions import get_session
        with patch(f"{_P}.get_session_from_typedb", return_value=None):
            result = get_session("NONEXISTENT")
        assert result is None


# ── update_session ───────────────────────────────────────────────


class TestUpdateSession:
    def test_typedb_success(self):
        from governance.services.sessions import update_session
        mock_client = MagicMock()
        existing = MagicMock()
        existing.status = "ACTIVE"
        mock_client.get_session.return_value = existing
        updated = MagicMock()
        mock_client.update_session.return_value = updated
        with patch(f"{_P}.get_typedb_client", return_value=mock_client), \
             patch(f"{_P}.session_to_response", return_value={"session_id": "S-1", "status": "COMPLETED"}):
            result = update_session("S-1", status="COMPLETED")
        assert result["status"] == "COMPLETED"

    def test_typedb_not_found(self):
        from governance.services.sessions import update_session
        mock_client = MagicMock()
        mock_client.get_session.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = update_session("NONEXISTENT", description="X")
        assert result is None

    def test_fallback_success(self):
        from governance.services.sessions import update_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = update_session("S-1", description="Updated")
        assert result is not None
        assert result["description"] == "Updated"

    def test_fallback_not_found(self):
        from governance.services.sessions import update_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = update_session("NONEXISTENT")
        assert result is None

    def test_fallback_updates_multiple_fields(self):
        from governance.services.sessions import update_session
        with patch(f"{_P}.get_typedb_client", return_value=None):
            result = update_session("S-1", description="New", status="COMPLETED",
                                    tasks_completed=5, agent_id="new-agent")
        assert result["description"] == "New"
        assert result["status"] == "COMPLETED"
        assert result["tasks_completed"] == 5
        assert result["agent_id"] == "new-agent"

    def test_typedb_failure_fallback(self):
        from governance.services.sessions import update_session
        mock_client = MagicMock()
        mock_client.get_session.side_effect = Exception("DB error")
        with patch(f"{_P}.get_typedb_client", return_value=mock_client):
            result = update_session("S-1", description="FB")
        assert result is not None
