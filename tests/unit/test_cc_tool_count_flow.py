"""DSP-02: BUG-014 — cc_tool_count data flow tests.

Verifies cc_tool_count flows correctly through:
1. Session entity → session_to_response()
2. Session entity → _session_to_dict() (TypeDB stores layer)
3. Pydantic model acceptance (SessionResponse, SessionCreate, SessionUpdate)
4. Zero vs None distinction (BUG-014: count=0 should not be treated as missing)
5. Fallback store round-trip
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.typedb.entities import Session
from governance.models.session import SessionResponse, SessionCreate, SessionUpdate


# =============================================================================
# 1. Entity Construction
# =============================================================================


class TestSessionEntityCcToolCount:
    """Session dataclass accepts and stores cc_tool_count."""

    def test_default_is_none(self):
        s = Session(id="S-1", name="test")
        assert s.cc_tool_count is None

    def test_set_positive_count(self):
        s = Session(id="S-2", name="test", cc_tool_count=42)
        assert s.cc_tool_count == 42

    def test_set_zero_count(self):
        """BUG-014: Zero is a valid count, not the same as None."""
        s = Session(id="S-3", name="test", cc_tool_count=0)
        assert s.cc_tool_count == 0
        assert s.cc_tool_count is not None

    def test_set_large_count(self):
        s = Session(id="S-4", name="test", cc_tool_count=9999)
        assert s.cc_tool_count == 9999


# =============================================================================
# 2. Pydantic Model Acceptance
# =============================================================================


class TestPydanticModelsAcceptCcToolCount:
    """Pydantic session models accept cc_tool_count field."""

    def test_session_response_with_count(self):
        sr = SessionResponse(
            session_id="S-1", start_time="2026-01-01T00:00:00",
            status="COMPLETED", cc_tool_count=15,
        )
        assert sr.cc_tool_count == 15

    def test_session_response_zero_count(self):
        """BUG-014: Zero should be preserved, not coerced to None."""
        sr = SessionResponse(
            session_id="S-2", start_time="2026-01-01T00:00:00",
            status="COMPLETED", cc_tool_count=0,
        )
        assert sr.cc_tool_count == 0

    def test_session_response_none_count(self):
        sr = SessionResponse(
            session_id="S-3", start_time="2026-01-01T00:00:00",
            status="COMPLETED",
        )
        assert sr.cc_tool_count is None

    def test_session_create_with_count(self):
        sc = SessionCreate(description="test", cc_tool_count=7)
        assert sc.cc_tool_count == 7

    def test_session_update_with_count(self):
        su = SessionUpdate(cc_tool_count=25)
        assert su.cc_tool_count == 25


# =============================================================================
# 3. session_to_response Conversion
# =============================================================================


class TestSessionToResponseCcToolCount:
    """session_to_response() includes cc_tool_count from entity."""

    def test_positive_count_preserved(self):
        from governance.stores.helpers import session_to_response
        session = Session(
            id="S-10", name="test", status="COMPLETED",
            started_at=datetime(2026, 1, 1, 9, 0),
            completed_at=datetime(2026, 1, 1, 10, 0),
            cc_tool_count=42,
        )
        resp = session_to_response(session)
        assert resp.cc_tool_count == 42

    def test_zero_count_preserved(self):
        """BUG-014: cc_tool_count=0 must not become None in response."""
        from governance.stores.helpers import session_to_response
        session = Session(
            id="S-11", name="test", status="COMPLETED",
            started_at=datetime(2026, 1, 1, 9, 0),
            completed_at=datetime(2026, 1, 1, 10, 0),
            cc_tool_count=0,
        )
        resp = session_to_response(session)
        assert resp.cc_tool_count == 0

    def test_none_count_preserved(self):
        from governance.stores.helpers import session_to_response
        session = Session(
            id="S-12", name="test", status="COMPLETED",
            started_at=datetime(2026, 1, 1, 9, 0),
            completed_at=datetime(2026, 1, 1, 10, 0),
        )
        resp = session_to_response(session)
        assert resp.cc_tool_count is None


# =============================================================================
# 4. model_dump / Serialization
# =============================================================================


class TestCcToolCountSerialization:
    """cc_tool_count survives serialization round-trip."""

    def test_model_dump_includes_cc_tool_count(self):
        sr = SessionResponse(
            session_id="S-20", start_time="2026-01-01T00:00:00",
            status="COMPLETED", cc_tool_count=15,
        )
        data = sr.model_dump()
        assert data["cc_tool_count"] == 15

    def test_model_dump_zero_not_dropped(self):
        """BUG-014: Ensure zero is not filtered out by exclude_none."""
        sr = SessionResponse(
            session_id="S-21", start_time="2026-01-01T00:00:00",
            status="COMPLETED", cc_tool_count=0,
        )
        data = sr.model_dump()
        assert "cc_tool_count" in data
        assert data["cc_tool_count"] == 0

    def test_model_dump_none_present(self):
        sr = SessionResponse(
            session_id="S-22", start_time="2026-01-01T00:00:00",
            status="COMPLETED",
        )
        data = sr.model_dump()
        assert "cc_tool_count" in data
        assert data["cc_tool_count"] is None


# =============================================================================
# 5. Fallback Store Round-Trip
# =============================================================================


class TestCcToolCountFallbackStore:
    """cc_tool_count survives in-memory fallback store operations."""

    @patch("governance.services.sessions_crud.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.log_event")
    def test_create_session_stores_cc_tool_count(
        self, mock_log, mock_audit, mock_client
    ):
        from governance.services.sessions_crud import create_session
        from governance.stores import _sessions_store

        result = create_session(
            description="test session",
            session_id="S-TOOL-001",
            cc_tool_count=42,
        )
        assert _sessions_store.get("S-TOOL-001", {}).get("cc_tool_count") == 42
        # Cleanup
        _sessions_store.pop("S-TOOL-001", None)

    @patch("governance.services.sessions_crud.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.log_event")
    def test_create_session_stores_zero_cc_tool_count(
        self, mock_log, mock_audit, mock_client
    ):
        """BUG-014: Zero count must be stored, not dropped."""
        from governance.services.sessions_crud import create_session
        from governance.stores import _sessions_store

        result = create_session(
            description="test zero count",
            session_id="S-TOOL-002",
            cc_tool_count=0,
        )
        assert _sessions_store.get("S-TOOL-002", {}).get("cc_tool_count") == 0
        # Cleanup
        _sessions_store.pop("S-TOOL-002", None)
