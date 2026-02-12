"""
Unit tests for Session Routing Mixin.

Per DOC-SIZE-01-v1: Tests for router/sessions.py module.
Tests: SessionRoutingMixin.route_session, _parse_session_id.
"""

import pytest
from unittest.mock import MagicMock

from governance.router.sessions import SessionRoutingMixin


class _TestSessionRouter(SessionRoutingMixin):
    """Concrete class for testing the session routing mixin."""

    def __init__(self, dry_run=True, embed=False):
        self.dry_run = dry_run
        self.embed = embed
        self.embedding_pipeline = MagicMock() if embed else None
        self.pre_route_hook = None
        self.post_route_hook = None


# ---------------------------------------------------------------------------
# _parse_session_id
# ---------------------------------------------------------------------------
class TestParseSessionId:
    """Tests for _parse_session_id()."""

    def test_full_session_id(self):
        router = _TestSessionRouter()
        meta = router._parse_session_id("SESSION-2024-12-25-PHASE9-FEATURE")
        assert meta["date"] == "2024-12-25"
        assert meta["phase"] == "PHASE9"
        assert meta["topic"] == "FEATURE"

    def test_session_id_no_phase(self):
        router = _TestSessionRouter()
        meta = router._parse_session_id("SESSION-2026-02-11-CHAT-TEST")
        assert meta["date"] == "2026-02-11"

    def test_minimal_session_id(self):
        router = _TestSessionRouter()
        meta = router._parse_session_id("SESSION-2026-01-01")
        assert meta["date"] == "2026-01-01"

    def test_invalid_session_id(self):
        router = _TestSessionRouter()
        meta = router._parse_session_id("INVALID-ID")
        assert meta["date"] == ""
        assert meta["phase"] == ""
        assert meta["topic"] == ""


# ---------------------------------------------------------------------------
# route_session
# ---------------------------------------------------------------------------
class TestRouteSession:
    """Tests for route_session()."""

    def test_empty_session_id_fails(self):
        router = _TestSessionRouter()
        result = router.route_session("")
        assert result["success"] is False
        assert "required" in result["error"]

    def test_none_session_id_fails(self):
        router = _TestSessionRouter()
        result = router.route_session(None)
        assert result["success"] is False

    def test_valid_session_succeeds(self):
        router = _TestSessionRouter()
        result = router.route_session("SESSION-2026-02-11-TEST")
        assert result["success"] is True
        assert result["item_type"] == "session"
        assert result["item_id"] == "SESSION-2026-02-11-TEST"

    def test_dry_run_no_embed(self):
        router = _TestSessionRouter(dry_run=True, embed=False)
        result = router.route_session("SESSION-2026-02-11-TEST")
        assert result["success"] is True
        assert result["embedded"] is False

    def test_embed_enabled(self):
        router = _TestSessionRouter(dry_run=False, embed=True)
        result = router.route_session("SESSION-2026-02-11-TEST", content="test")
        assert result["embedded"] is True
        router.embedding_pipeline.embed_session.assert_called_once()

    def test_dry_run_with_embed_skips_actual_embed(self):
        router = _TestSessionRouter(dry_run=True, embed=True)
        result = router.route_session("SESSION-2026-02-11-TEST")
        router.embedding_pipeline.embed_session.assert_not_called()

    def test_pre_hook_called(self):
        router = _TestSessionRouter()
        hook = MagicMock(side_effect=lambda t, d: d)
        router.pre_route_hook = hook
        router.route_session("SESSION-2026-02-11-TEST")
        hook.assert_called_once()
        assert hook.call_args[0][0] == "session"

    def test_post_hook_called(self):
        router = _TestSessionRouter()
        hook = MagicMock()
        router.post_route_hook = hook
        router.route_session("SESSION-2026-02-11-TEST")
        hook.assert_called_once()
        assert hook.call_args[0][0] == "session"

    def test_metadata_in_result(self):
        router = _TestSessionRouter()
        result = router.route_session("SESSION-2026-02-11-PHASE9-CHAT")
        assert result["metadata"] is not None
        assert result["metadata"]["date"] == "2026-02-11"

    def test_destination_is_typedb(self):
        router = _TestSessionRouter()
        result = router.route_session("SESSION-2026-02-11-TEST")
        assert result["destination"] == "typedb"
