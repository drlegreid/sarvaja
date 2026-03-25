"""Unit tests for list_all_active_sessions() — FEAT-009.

Tests the 3-source merge: memory + TypeDB + CC JSONL.
"""

import json
import os
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

_MOD = "governance.session_collector.registry"
_STORES = "governance.stores"
_SCANNER = "governance.services.cc_session_scanner"

from governance.session_collector.registry import list_all_active_sessions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_jsonl_dir(tmp_path, files, now=None):
    """Create fake JSONL files with controlled mtimes.

    Args:
        files: list of (name, age_seconds) tuples.
    Returns:
        Path to the fake project dir (parent is the "CC dir").
    """
    project_dir = tmp_path / "-home-user-project"
    project_dir.mkdir(parents=True)
    now = now or time.time()
    for name, age_secs in files:
        f = project_dir / f"{name}.jsonl"
        f.write_text(json.dumps({
            "type": "user",
            "timestamp": "2026-03-24T10:00:00",
            "sessionId": name,
            "gitBranch": "master",
        }) + "\n")
        os.utime(f, (now - age_secs, now - age_secs))
    return project_dir


@pytest.fixture(autouse=True)
def _clean_state(tmp_path):
    """Ensure _active_sessions is empty and CC scan uses empty dir between tests."""
    empty_dir = tmp_path / "empty_cc"
    empty_dir.mkdir()
    with patch(f"{_MOD}._active_sessions", {}), \
         patch(f"{_SCANNER}.DEFAULT_CC_DIR", empty_dir):
        yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestListAllActiveSessions:
    """Tests for list_all_active_sessions()."""

    def test_memory_only(self):
        """Memory sessions returned when TypeDB and CC unavailable."""
        with patch(f"{_MOD}._active_sessions", {"SESSION-MEM": MagicMock()}), \
             patch(f"{_STORES}.get_all_sessions_from_typedb",
                   side_effect=Exception("unavailable")):
            result = list_all_active_sessions()
        mem = [r for r in result if r["source"] == "memory"]
        assert len(mem) == 1
        assert mem[0]["session_id"] == "SESSION-MEM"

    @patch(f"{_STORES}.get_all_sessions_from_typedb")
    def test_typedb_active_sessions(self, mock_typedb):
        """TypeDB ACTIVE sessions are included."""
        mock_typedb.return_value = [
            {"session_id": "SESSION-TDB-1", "status": "ACTIVE"},
            {"session_id": "SESSION-TDB-2", "status": "COMPLETED"},
        ]
        result = list_all_active_sessions()
        sids = [r["session_id"] for r in result]
        assert "SESSION-TDB-1" in sids
        assert "SESSION-TDB-2" not in sids

    @patch(f"{_STORES}.get_all_sessions_from_typedb")
    def test_typedb_completed_excluded(self, mock_typedb):
        """COMPLETED sessions from TypeDB are NOT returned."""
        mock_typedb.return_value = [
            {"session_id": "SESSION-DONE", "status": "COMPLETED"},
        ]
        result = list_all_active_sessions()
        assert len(result) == 0

    @patch(f"{_STORES}.get_all_sessions_from_typedb", return_value=[])
    def test_cc_jsonl_recent_included(self, _mock_tdb, tmp_path):
        """CC JSONL files modified <2h ago are included."""
        project_dir = _fake_jsonl_dir(tmp_path, [("recent-sess", 600)])
        with patch(f"{_SCANNER}.DEFAULT_CC_DIR", project_dir.parent):
            result = list_all_active_sessions()
        cc = [r for r in result if r["source"] == "cc_jsonl"]
        assert len(cc) == 1
        assert "cc_session_uuid" in cc[0]

    @patch(f"{_STORES}.get_all_sessions_from_typedb", return_value=[])
    def test_cc_jsonl_old_excluded(self, _mock_tdb, tmp_path):
        """CC JSONL files modified >2h ago are excluded."""
        project_dir = _fake_jsonl_dir(tmp_path, [("old-sess", 8000)])
        with patch(f"{_SCANNER}.DEFAULT_CC_DIR", project_dir.parent):
            result = list_all_active_sessions()
        cc = [r for r in result if r["source"] == "cc_jsonl"]
        assert len(cc) == 0

    @patch(f"{_STORES}.get_all_sessions_from_typedb")
    def test_dedup_memory_wins(self, mock_typedb):
        """Same session_id in memory and TypeDB → memory source wins."""
        mock_typedb.return_value = [
            {"session_id": "SESSION-DUP", "status": "ACTIVE"},
        ]
        with patch(f"{_MOD}._active_sessions", {"SESSION-DUP": MagicMock()}):
            result = list_all_active_sessions()
        dups = [r for r in result if r["session_id"] == "SESSION-DUP"]
        assert len(dups) == 1
        assert dups[0]["source"] == "memory"

    @patch(f"{_STORES}.get_all_sessions_from_typedb")
    def test_all_three_sources(self, mock_typedb, tmp_path):
        """All 3 sources contribute unique sessions."""
        mock_typedb.return_value = [
            {"session_id": "SESSION-TDB", "status": "ACTIVE"},
        ]
        project_dir = _fake_jsonl_dir(tmp_path, [("cc-new", 300)])
        with patch(f"{_MOD}._active_sessions", {"SESSION-MEM": MagicMock()}), \
             patch(f"{_SCANNER}.DEFAULT_CC_DIR", project_dir.parent):
            result = list_all_active_sessions()
        sources = {r["source"] for r in result}
        assert sources == {"memory", "typedb", "cc_jsonl"}
        assert len(result) == 3

    def test_graceful_on_typedb_error(self):
        """TypeDB runtime error doesn't crash — returns memory only."""
        with patch(f"{_MOD}._active_sessions", {"SESSION-MEM": MagicMock()}), \
             patch(f"{_STORES}.get_all_sessions_from_typedb",
                   side_effect=Exception("conn refused")):
            result = list_all_active_sessions()
        assert len(result) >= 1
        assert result[0]["source"] == "memory"
