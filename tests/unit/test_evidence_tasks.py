"""
Unit tests for evidence/tasks.py MCP tools.

Tests governance_list_tasks and governance_get_task_deps.
Covers TypeDB path, markdown fallback, filters, and edge cases.
"""

import json
import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

import pytest


_MOD = "governance.mcp_tools.evidence.tasks"


@pytest.fixture(autouse=True)
def force_json_output():
    """Force JSON output format for predictable test results."""
    old = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old


def _register_tools():
    """Register and return tools by name."""
    from governance.mcp_tools.evidence.tasks import register_task_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_task_tools(MockMCP())
    return tools


@dataclass
class FakeTask:
    id: str = "T-1"
    name: str = "Test Task"
    body: str = "Description"
    status: str = "OPEN"
    phase: str = "P10"
    agent_id: str = "code-agent"
    gap_id: str = ""


# ── governance_list_tasks ─────────────────────────────────


class TestGovernanceListTasks:

    def test_registration(self):
        tools = _register_tools()
        assert "governance_list_tasks" in tools

    @patch("governance.client.TypeDBClient")
    def test_typedb_path_returns_tasks(self, mock_cls):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_tasks.return_value = [FakeTask(), FakeTask(id="T-2", phase="P11")]
        mock_cls.return_value = client

        result = json.loads(tools["governance_list_tasks"]())
        assert result["source"] == "typedb"
        assert result["count"] == 2
        assert len(result["tasks"]) == 2
        client.close.assert_called_once()

    @patch("governance.client.TypeDBClient")
    def test_typedb_filter_by_phase(self, mock_cls):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_tasks.return_value = [
            FakeTask(phase="P10"), FakeTask(id="T-2", phase="P11"),
        ]
        mock_cls.return_value = client

        result = json.loads(tools["governance_list_tasks"](phase="P11"))
        assert result["count"] == 1
        assert result["tasks"][0]["phase"] == "P11"

    @patch("governance.client.TypeDBClient")
    def test_typedb_filter_by_status(self, mock_cls):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_tasks.return_value = [
            FakeTask(status="OPEN"), FakeTask(id="T-2", status="DONE"),
        ]
        mock_cls.return_value = client

        result = json.loads(tools["governance_list_tasks"](status="DONE"))
        assert result["count"] == 1
        assert result["tasks"][0]["task_id"] == "T-2"

    @patch("governance.client.TypeDBClient")
    def test_typedb_status_case_insensitive(self, mock_cls):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_tasks.return_value = [FakeTask(status="done")]
        mock_cls.return_value = client

        result = json.loads(tools["governance_list_tasks"](status="DONE"))
        assert result["count"] == 1

    @patch("governance.client.TypeDBClient")
    def test_typedb_connect_fails_falls_back(self, mock_cls):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = False
        mock_cls.return_value = client

        with patch(f"{_MOD}.BACKLOG_DIR", Path("/nonexistent")):
            result = json.loads(tools["governance_list_tasks"]())
        assert result["source"] == "markdown"
        assert result["count"] == 0

    @patch("governance.client.TypeDBClient", side_effect=RuntimeError("No TypeDB"))
    def test_typedb_exception_falls_back(self, mock_cls):
        tools = _register_tools()
        with patch(f"{_MOD}.BACKLOG_DIR", Path("/nonexistent")):
            result = json.loads(tools["governance_list_tasks"]())
        assert result["source"] == "markdown"
        assert result["count"] == 0

    @patch("governance.client.TypeDBClient", side_effect=RuntimeError("No TypeDB"))
    def test_markdown_fallback_parses_tasks(self, mock_cls):
        tools = _register_tools()
        md_content = (
            "| ID | Name | Status | Notes |\n"
            "|----|------|--------|-------|\n"
            "| P7.1 | Build API | \u2705 DONE | shipped |\n"
            "| RD-1 | Research X | \U0001f4cb TODO | new |\n"
            "| FH-2 | Fix bug | \U0001f504 IN_PROGRESS | active |\n"
        )
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = md_content
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_list_tasks"]())

        assert result["source"] == "markdown"
        assert result["count"] == 3
        statuses = [t["status"] for t in result["tasks"]]
        assert "DONE" in statuses
        assert "TODO" in statuses
        assert "IN_PROGRESS" in statuses

    @patch("governance.client.TypeDBClient", side_effect=RuntimeError("No TypeDB"))
    def test_markdown_filter_by_phase(self, mock_cls):
        tools = _register_tools()
        md_content = (
            "| P7.1 | Build | \u2705 DONE | n |\n"
            "| RD-1 | Research | \U0001f4cb TODO | n |\n"
        )
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = md_content
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_list_tasks"](phase="RD"))

        assert result["count"] == 1
        assert result["tasks"][0]["phase"] == "RD"

    @patch("governance.client.TypeDBClient", side_effect=RuntimeError("No TypeDB"))
    def test_markdown_filter_by_status(self, mock_cls):
        tools = _register_tools()
        md_content = (
            "| P7.1 | Build | \u2705 DONE | n |\n"
            "| RD-1 | Research | \U0001f4cb TODO | n |\n"
        )
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = md_content
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_list_tasks"](status="DONE"))

        assert result["count"] == 1

    @patch("governance.client.TypeDBClient", side_effect=RuntimeError("No TypeDB"))
    def test_markdown_skips_headers(self, mock_cls):
        """Headers and separators should be skipped."""
        tools = _register_tools()
        md_content = (
            "| ID | Name | Status | Notes |\n"
            "|-----|------|--------|-------|\n"
            "| Task | Something | x | y |\n"
            "| Pillar | Something | x | y |\n"
            "| P7.1 | Build | DONE | n |\n"
        )
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = md_content
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_list_tasks"]())

        assert result["count"] == 1
        assert result["tasks"][0]["task_id"] == "P7.1"

    @patch("governance.client.TypeDBClient", side_effect=RuntimeError("No TypeDB"))
    def test_markdown_blocked_status(self, mock_cls):
        tools = _register_tools()
        md_content = "| P7.1 | Build | \u23f8\ufe0f BLOCKED | waiting |\n"
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = md_content
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_list_tasks"]())

        assert result["tasks"][0]["status"] == "BLOCKED"

    @patch("governance.client.TypeDBClient")
    def test_typedb_phases_deduped(self, mock_cls):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_tasks.return_value = [
            FakeTask(phase="P10"), FakeTask(id="T-2", phase="P10"),
        ]
        mock_cls.return_value = client

        result = json.loads(tools["governance_list_tasks"]())
        assert result["phases"] == ["P10"]


# ── governance_get_task_deps ──────────────────────────────


class TestGovernanceGetTaskDeps:

    def test_registration(self):
        tools = _register_tools()
        assert "governance_get_task_deps" in tools

    def test_no_backlog_returns_empty(self):
        tools = _register_tools()
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = False
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_get_task_deps"]("RD-1"))
        assert result["task_id"] == "RD-1"
        assert result["blocked_by"] == []
        assert result["blocks"] == []

    def test_phase_dependency_inference_high(self):
        """Tasks > P7 are blocked by P7."""
        tools = _register_tools()
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = "No dependencies section\n"
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_get_task_deps"]("P9.1"))
        assert "P7 (TypeDB-First)" in result["blocked_by"]
        assert "P3 (Stabilization)" in result["blocked_by"]

    def test_phase_dependency_inference_mid(self):
        """Tasks > P3 but <= P7 are only blocked by P3."""
        tools = _register_tools()
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = "No dependencies section\n"
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_get_task_deps"]("P5.1"))
        assert "P3 (Stabilization)" in result["blocked_by"]
        assert "P7 (TypeDB-First)" not in result["blocked_by"]

    def test_phase_dependency_inference_low(self):
        """Tasks <= P3 have no inferred deps."""
        tools = _register_tools()
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = "No dependencies section\n"
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_get_task_deps"]("P2.1"))
        assert result["blocked_by"] == []

    def test_rd_task_no_phase_inference(self):
        """RD- tasks don't get phase-based inferences."""
        tools = _register_tools()
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = False
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_get_task_deps"]("RD-1"))
        assert result["blocked_by"] == []

    def test_deps_from_backlog_file(self):
        """Parse Dependencies: section from backlog."""
        tools = _register_tools()
        md_content = (
            "Dependencies:\n"
            "- P7.1 requires Phase 3 completion\n"
            "- P7.1 depends on Phase 2 work\n"
        )
        mock_backlog = MagicMock()
        mock_backlog_file = MagicMock()
        mock_backlog_file.exists.return_value = True
        mock_backlog_file.read_text.return_value = md_content
        mock_backlog.__truediv__ = MagicMock(return_value=mock_backlog_file)

        with patch(f"{_MOD}.BACKLOG_DIR", mock_backlog):
            result = json.loads(tools["governance_get_task_deps"]("P7.1"))

        # Should find Phase 3 and Phase 2 references
        assert "P3" in result["blocked_by"]
        assert "P2" in result["blocked_by"]
        # Also has inferred deps since P7.1 > P3
        assert "P3 (Stabilization)" in result["blocked_by"]
