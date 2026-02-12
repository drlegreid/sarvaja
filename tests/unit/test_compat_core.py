"""
Unit tests for Compat - Core Query Functions.

Per DOC-SIZE-01-v1: Tests for compat/core.py module.
Tests: governance_list_sessions, governance_get_session,
       governance_get_task_deps, governance_evidence_search.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestGovernanceListSessions:
    """Tests for governance_list_sessions()."""

    def test_returns_sessions(self, tmp_path):
        # Create session files
        (tmp_path / "SESSION-2026-02-11-TEST.md").write_text("# Session")
        (tmp_path / "SESSION-2026-02-10-OTHER.md").write_text("# Other")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_list_sessions
            result = json.loads(governance_list_sessions(limit=20))
            assert result["count"] == 2

    def test_limit(self, tmp_path):
        for i in range(5):
            (tmp_path / f"SESSION-2026-02-0{i+1}-TEST.md").write_text(f"S{i}")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_list_sessions
            result = json.loads(governance_list_sessions(limit=3))
            assert result["count"] == 3

    def test_session_type_filter(self, tmp_path):
        (tmp_path / "SESSION-2026-02-11-CHAT-TEST.md").write_text("C")
        (tmp_path / "SESSION-2026-02-11-DSM-AUDIT.md").write_text("D")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_list_sessions
            result = json.loads(governance_list_sessions(session_type="CHAT"))
            assert result["count"] == 1
            assert "CHAT" in result["sessions"][0]["topic"]

    def test_empty_dir(self, tmp_path):
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_list_sessions
            result = json.loads(governance_list_sessions())
            assert result["count"] == 0

    def test_parses_date(self, tmp_path):
        (tmp_path / "SESSION-2026-02-11-TEST.md").write_text("# S")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_list_sessions
            result = json.loads(governance_list_sessions())
            assert result["sessions"][0]["date"] == "2026-02-11"


class TestGovernanceGetSession:
    """Tests for governance_get_session()."""

    def test_found(self, tmp_path):
        (tmp_path / "SESSION-2026-02-11-TEST.md").write_text("# Test Session\nContent here")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_get_session
            result = json.loads(governance_get_session("SESSION-2026-02-11-TEST"))
            assert "Content here" in result["content"]

    def test_not_found(self, tmp_path):
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_get_session
            result = json.loads(governance_get_session("NONEXISTENT"))
            assert "error" in result

    def test_appends_md_extension(self, tmp_path):
        (tmp_path / "SESSION-2026-02-11-TEST.md").write_text("ok")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_get_session
            result = json.loads(governance_get_session("SESSION-2026-02-11-TEST"))
            assert result["session_id"] == "SESSION-2026-02-11-TEST"


class TestGovernanceGetTaskDeps:
    """Tests for governance_get_task_deps()."""

    def test_phase_dependencies(self):
        from governance.compat.core import governance_get_task_deps
        result = json.loads(governance_get_task_deps("P5.1"))
        assert "P4" in result["blocked_by"]
        assert "P6" in result["blocks"]

    def test_phase_1_no_blockers(self):
        from governance.compat.core import governance_get_task_deps
        result = json.loads(governance_get_task_deps("P1.1"))
        assert result["blocked_by"] == []
        assert "P2" in result["blocks"]

    def test_non_phase_task(self):
        from governance.compat.core import governance_get_task_deps
        result = json.loads(governance_get_task_deps("RD-001"))
        assert result["blocked_by"] == []
        assert result["blocks"] == []


class TestGovernanceEvidenceSearch:
    """Tests for governance_evidence_search()."""

    def test_finds_match(self, tmp_path):
        (tmp_path / "SESSION-2026-02-11-TEST.md").write_text("TypeDB migration complete")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_evidence_search
            result = json.loads(governance_evidence_search("TypeDB"))
            assert result["count"] >= 1
            assert result["results"][0]["source_type"] == "session"

    def test_no_match(self, tmp_path):
        (tmp_path / "SESSION-2026-02-11-TEST.md").write_text("Nothing here")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_evidence_search
            result = json.loads(governance_evidence_search("nonexistent_query_xyz"))
            assert result["count"] == 0

    def test_top_k_limit(self, tmp_path):
        for i in range(10):
            (tmp_path / f"SESSION-2026-02-{i:02d}-TEST.md").write_text(f"keyword match {i}")
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_evidence_search
            result = json.loads(governance_evidence_search("keyword", top_k=3))
            assert result["count"] <= 3

    def test_search_method(self, tmp_path):
        with patch("governance.compat.core.EVIDENCE_DIR", tmp_path):
            from governance.compat.core import governance_evidence_search
            result = json.loads(governance_evidence_search("test"))
            assert result["search_method"] == "keyword_match"
