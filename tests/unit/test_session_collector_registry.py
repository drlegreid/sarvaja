"""
Unit tests for Session Collector Registry.

Per DOC-SIZE-01-v1: Tests for session_collector/registry.py module.
Tests: _persist_state, get_or_create_session, list_active_sessions, etc.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from governance.session_collector.registry import (
    _active_sessions,
    _persist_state,
    list_active_sessions,
    get_session,
    clear_all_sessions,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure registry is clean before and after each test."""
    _active_sessions.clear()
    yield
    _active_sessions.clear()


class TestPersistState:
    """Tests for _persist_state()."""

    def test_writes_state_file(self, tmp_path):
        state_file = tmp_path / "session_state.json"
        with patch("governance.session_collector.registry.STATE_FILE", state_file):
            _active_sessions["SESSION-TEST"] = MagicMock()
            _persist_state()
        data = json.loads(state_file.read_text())
        assert "SESSION-TEST" in data["active_sessions"]
        assert data["count"] == 1

    def test_empty_state(self, tmp_path):
        state_file = tmp_path / "session_state.json"
        with patch("governance.session_collector.registry.STATE_FILE", state_file):
            _persist_state()
        data = json.loads(state_file.read_text())
        assert data["active_sessions"] == []
        assert data["last_session"] is None
        assert data["count"] == 0

    def test_creates_parent_dirs(self, tmp_path):
        state_file = tmp_path / "deep" / "nested" / "state.json"
        with patch("governance.session_collector.registry.STATE_FILE", state_file):
            _persist_state()
        assert state_file.exists()


class TestListActiveSessions:
    """Tests for list_active_sessions()."""

    def test_empty(self):
        assert list_active_sessions() == []

    def test_with_sessions(self):
        _active_sessions["S-1"] = MagicMock()
        _active_sessions["S-2"] = MagicMock()
        result = list_active_sessions()
        assert len(result) == 2
        assert "S-1" in result
        assert "S-2" in result


class TestGetSession:
    """Tests for get_session()."""

    def test_existing(self):
        mock = MagicMock()
        _active_sessions["S-1"] = mock
        assert get_session("S-1") is mock

    def test_nonexistent(self):
        assert get_session("S-NONEXISTENT") is None


class TestClearAllSessions:
    """Tests for clear_all_sessions()."""

    def test_clears_and_returns_count(self, tmp_path):
        state_file = tmp_path / "state.json"
        with patch("governance.session_collector.registry.STATE_FILE", state_file):
            _active_sessions["S-1"] = MagicMock()
            _active_sessions["S-2"] = MagicMock()
            count = clear_all_sessions()
        assert count == 2
        assert len(_active_sessions) == 0

    def test_empty_returns_zero(self, tmp_path):
        state_file = tmp_path / "state.json"
        with patch("governance.session_collector.registry.STATE_FILE", state_file):
            count = clear_all_sessions()
        assert count == 0
