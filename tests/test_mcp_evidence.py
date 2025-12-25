"""
MCP Evidence Tools Tests (P9.1)
Created: 2024-12-25

Tests for Task/Session/Evidence MCP tools.
Strategic Goal: View all task/session/evidence artifacts via MCP and UI.
"""
import pytest
import json
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DOCS_DIR = PROJECT_ROOT / "docs"


class TestMCPEvidenceToolsExist:
    """Verify P9.1 evidence MCP tools are defined."""

    @pytest.mark.unit
    def test_mcp_server_exists(self):
        """MCP server module must exist."""
        mcp_file = GOVERNANCE_DIR / "mcp_server.py"
        assert mcp_file.exists(), "governance/mcp_server.py not found"

    @pytest.mark.unit
    def test_evidence_tools_defined(self):
        """Evidence viewing tools must be defined."""
        from governance import mcp_server

        # Check P9.1 tools exist
        assert hasattr(mcp_server, 'governance_list_sessions')
        assert hasattr(mcp_server, 'governance_get_session')
        assert hasattr(mcp_server, 'governance_list_decisions')
        assert hasattr(mcp_server, 'governance_get_decision')
        assert hasattr(mcp_server, 'governance_list_tasks')
        assert hasattr(mcp_server, 'governance_get_task_deps')
        assert hasattr(mcp_server, 'governance_evidence_search')

    @pytest.mark.unit
    def test_tools_are_callable(self):
        """Evidence tools must be callable functions."""
        from governance.mcp_server import (
            governance_list_sessions,
            governance_get_session,
            governance_list_decisions,
            governance_get_decision,
            governance_list_tasks,
            governance_get_task_deps,
            governance_evidence_search
        )

        assert callable(governance_list_sessions)
        assert callable(governance_get_session)
        assert callable(governance_list_decisions)
        assert callable(governance_get_decision)
        assert callable(governance_list_tasks)
        assert callable(governance_get_task_deps)
        assert callable(governance_evidence_search)


class TestSessionListing:
    """Tests for governance_list_sessions tool."""

    @pytest.mark.unit
    def test_list_sessions_returns_json(self):
        """governance_list_sessions should return valid JSON."""
        from governance.mcp_server import governance_list_sessions

        result = governance_list_sessions()
        data = json.loads(result)

        assert "sessions" in data
        assert "count" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.unit
    def test_list_sessions_with_limit(self):
        """governance_list_sessions should respect limit parameter."""
        from governance.mcp_server import governance_list_sessions

        result = governance_list_sessions(limit=5)
        data = json.loads(result)

        assert len(data["sessions"]) <= 5

    @pytest.mark.unit
    def test_session_has_required_fields(self):
        """Each session should have required fields."""
        from governance.mcp_server import governance_list_sessions

        result = governance_list_sessions(limit=1)
        data = json.loads(result)

        if data["sessions"]:
            session = data["sessions"][0]
            assert "session_id" in session
            assert "date" in session or "topic" in session


class TestSessionRetrieval:
    """Tests for governance_get_session tool."""

    @pytest.mark.unit
    def test_get_session_returns_json(self):
        """governance_get_session should return valid JSON."""
        from governance.mcp_server import governance_get_session

        # Try to get a known session
        result = governance_get_session("SESSION-2024-12-25-PHASE8-HEALTHCHECK")
        data = json.loads(result)

        assert isinstance(data, dict)

    @pytest.mark.unit
    def test_get_session_not_found(self):
        """governance_get_session should handle missing sessions."""
        from governance.mcp_server import governance_get_session

        result = governance_get_session("SESSION-NONEXISTENT-999")
        data = json.loads(result)

        assert "error" in data


class TestDecisionListing:
    """Tests for governance_list_decisions tool."""

    @pytest.mark.unit
    def test_list_decisions_returns_json(self):
        """governance_list_decisions should return valid JSON."""
        from governance.mcp_server import governance_list_decisions

        result = governance_list_decisions()
        data = json.loads(result)

        assert "decisions" in data
        assert "count" in data

    @pytest.mark.unit
    def test_decision_has_required_fields(self):
        """Each decision should have required fields."""
        from governance.mcp_server import governance_list_decisions

        result = governance_list_decisions()
        data = json.loads(result)

        if data["decisions"]:
            decision = data["decisions"][0]
            assert "decision_id" in decision
            # Name or title should be present
            assert "name" in decision or "title" in decision


class TestDecisionRetrieval:
    """Tests for governance_get_decision tool."""

    @pytest.mark.unit
    def test_get_decision_returns_json(self):
        """governance_get_decision should return valid JSON."""
        from governance.mcp_server import governance_get_decision

        result = governance_get_decision("DECISION-003")
        data = json.loads(result)

        assert isinstance(data, dict)

    @pytest.mark.unit
    def test_get_decision_not_found(self):
        """governance_get_decision should handle missing decisions."""
        from governance.mcp_server import governance_get_decision

        result = governance_get_decision("DECISION-999")
        data = json.loads(result)

        # Either error or empty result
        assert "error" in data or len(data) == 1


class TestTaskListing:
    """Tests for governance_list_tasks tool."""

    @pytest.mark.unit
    def test_list_tasks_returns_json(self):
        """governance_list_tasks should return valid JSON."""
        from governance.mcp_server import governance_list_tasks

        result = governance_list_tasks()
        data = json.loads(result)

        assert "tasks" in data
        assert "count" in data

    @pytest.mark.unit
    def test_list_tasks_filter_by_phase(self):
        """governance_list_tasks should filter by phase."""
        from governance.mcp_server import governance_list_tasks

        result = governance_list_tasks(phase="P7")
        data = json.loads(result)

        for task in data["tasks"]:
            assert task["phase"] == "P7"

    @pytest.mark.unit
    def test_list_tasks_filter_by_status(self):
        """governance_list_tasks should filter by status."""
        from governance.mcp_server import governance_list_tasks

        result = governance_list_tasks(status="DONE")
        data = json.loads(result)

        for task in data["tasks"]:
            assert task["status"] == "DONE"

    @pytest.mark.unit
    def test_task_has_required_fields(self):
        """Each task should have required fields."""
        from governance.mcp_server import governance_list_tasks

        result = governance_list_tasks()
        data = json.loads(result)

        if data["tasks"]:
            task = data["tasks"][0]
            assert "task_id" in task
            assert "status" in task
            assert "phase" in task


class TestTaskDependencies:
    """Tests for governance_get_task_deps tool."""

    @pytest.mark.unit
    def test_get_task_deps_returns_json(self):
        """governance_get_task_deps should return valid JSON."""
        from governance.mcp_server import governance_get_task_deps

        result = governance_get_task_deps("P9.1")
        data = json.loads(result)

        assert "task_id" in data
        assert "blocked_by" in data
        assert "blocks" in data

    @pytest.mark.unit
    def test_task_deps_infers_phase_order(self):
        """Task deps should infer phase ordering dependencies."""
        from governance.mcp_server import governance_get_task_deps

        result = governance_get_task_deps("P9.1")
        data = json.loads(result)

        # P9 tasks should be blocked by earlier phases
        assert len(data["blocked_by"]) > 0


class TestEvidenceSearch:
    """Tests for governance_evidence_search tool."""

    @pytest.mark.unit
    def test_evidence_search_returns_json(self):
        """governance_evidence_search should return valid JSON."""
        from governance.mcp_server import governance_evidence_search

        result = governance_evidence_search("governance")
        data = json.loads(result)

        assert "query" in data
        assert "results" in data
        assert "search_method" in data

    @pytest.mark.unit
    def test_evidence_search_respects_top_k(self):
        """governance_evidence_search should respect top_k parameter."""
        from governance.mcp_server import governance_evidence_search

        result = governance_evidence_search("governance", top_k=3)
        data = json.loads(result)

        assert len(data["results"]) <= 3

    @pytest.mark.unit
    def test_evidence_search_result_has_fields(self):
        """Each search result should have required fields."""
        from governance.mcp_server import governance_evidence_search

        result = governance_evidence_search("RULE", top_k=1)
        data = json.loads(result)

        if data["results"]:
            res = data["results"][0]
            assert "source" in res
            assert "score" in res


class TestEvidenceDirectoryStructure:
    """Tests for evidence directory structure."""

    @pytest.mark.unit
    def test_evidence_dir_exists(self):
        """Evidence directory must exist."""
        assert EVIDENCE_DIR.exists(), "evidence/ directory not found"

    @pytest.mark.unit
    def test_has_session_files(self):
        """Should have session evidence files."""
        import glob
        sessions = glob.glob(str(EVIDENCE_DIR / "SESSION-*.md"))
        assert len(sessions) > 0, "No SESSION-*.md files found"

    @pytest.mark.unit
    def test_backlog_file_exists(self):
        """R&D backlog file must exist."""
        backlog = DOCS_DIR / "backlog" / "R&D-BACKLOG.md"
        assert backlog.exists(), "R&D-BACKLOG.md not found"


class TestMCPToolIntegration:
    """Integration tests for MCP tools working together."""

    @pytest.mark.unit
    def test_list_then_get_session(self):
        """Should be able to list sessions then get one."""
        from governance.mcp_server import governance_list_sessions, governance_get_session

        # List sessions
        list_result = governance_list_sessions(limit=1)
        list_data = json.loads(list_result)

        if list_data["sessions"]:
            session_id = list_data["sessions"][0]["session_id"]

            # Get that session
            get_result = governance_get_session(session_id)
            get_data = json.loads(get_result)

            # Should not be an error
            assert "error" not in get_data or get_data.get("content")

    @pytest.mark.unit
    def test_list_then_get_decision(self):
        """Should be able to list decisions then get one."""
        from governance.mcp_server import governance_list_decisions, governance_get_decision

        # List decisions
        list_result = governance_list_decisions()
        list_data = json.loads(list_result)

        if list_data["decisions"]:
            decision_id = list_data["decisions"][0]["decision_id"]

            # Get that decision
            get_result = governance_get_decision(decision_id)
            get_data = json.loads(get_result)

            # Should have decision_id at minimum
            assert "decision_id" in get_data

    @pytest.mark.unit
    def test_task_list_filter_combinations(self):
        """Should be able to combine phase and status filters."""
        from governance.mcp_server import governance_list_tasks

        # Get all P7 TODO tasks
        result = governance_list_tasks(phase="P7", status="TODO")
        data = json.loads(result)

        for task in data["tasks"]:
            assert task["phase"] == "P7"
            assert task["status"] == "TODO"
