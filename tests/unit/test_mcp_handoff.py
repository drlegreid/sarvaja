"""
Unit tests for Task Handoff MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/handoff.py module.
Tests: register_handoff_tools — handoff_create, handoffs_pending,
       handoff_complete, handoff_get, handoff_route.
"""

import json
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _format_mcp():
    with patch("governance.mcp_tools.handoff.format_mcp_result",
               side_effect=lambda x: json.dumps(x)):
        yield


_P = "governance.mcp_tools.handoff"


def _register():
    from governance.mcp_tools.handoff import register_handoff_tools
    mcp = _CaptureMCP()
    register_handoff_tools(mcp)
    return mcp.tools


def _make_handoff(task_id="T-1", status="PENDING"):
    h = MagicMock()
    h.task_id = task_id
    h.status = status
    h.evidence_gathered = []
    h.to_dict.return_value = {"task_id": task_id, "status": status}
    return h


class TestHandoffCreate:
    def test_success(self):
        tools = _register()
        handoff = _make_handoff()
        with patch(f"{_P}.create_handoff", return_value=handoff), \
             patch(f"{_P}.write_handoff_evidence", return_value=Path("/evidence/file.md")):
            result = json.loads(tools["handoff_create"](
                task_id="T-1", title="Test", from_agent="RESEARCH",
                to_agent="CODING", context_summary="context",
                recommended_action="implement",
            ))
        assert result["status"] == "created"
        assert "evidence_file" in result

    def test_with_optional_params(self):
        tools = _register()
        handoff = _make_handoff()
        with patch(f"{_P}.create_handoff", return_value=handoff) as mock_create, \
             patch(f"{_P}.write_handoff_evidence", return_value=Path("/evidence/file.md")):
            tools["handoff_create"](
                task_id="T-1", title="Test", from_agent="RESEARCH",
                to_agent="CODING", context_summary="context",
                recommended_action="implement",
                files_examined="file1.py|file2.py",
                evidence_gathered="e1|e2",
                action_steps="step1|step2",
                linked_rules="RULE-001,RULE-002",
                constraints="c1|c2",
                priority="HIGH",
                source_session_id="SESSION-2026-01-01-TEST",
            )
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["files_examined"] == ["file1.py", "file2.py"]
        assert call_kwargs["linked_rules"] == ["RULE-001", "RULE-002"]
        assert call_kwargs["priority"] == "HIGH"

    def test_empty_optional_params(self):
        tools = _register()
        handoff = _make_handoff()
        with patch(f"{_P}.create_handoff", return_value=handoff) as mock_create, \
             patch(f"{_P}.write_handoff_evidence", return_value=Path("/evidence/file.md")):
            tools["handoff_create"](
                task_id="T-1", title="Test", from_agent="R",
                to_agent="C", context_summary="ctx",
                recommended_action="act",
            )
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["files_examined"] == []
        assert call_kwargs["constraints"] == []

    def test_exception(self):
        tools = _register()
        with patch(f"{_P}.create_handoff", side_effect=Exception("fail")):
            result = json.loads(tools["handoff_create"](
                task_id="T-1", title="Test", from_agent="R",
                to_agent="C", context_summary="ctx",
                recommended_action="act",
            ))
        assert "error" in result


class TestHandoffsPending:
    def test_success(self):
        tools = _register()
        h = _make_handoff()
        with patch(f"{_P}.get_pending_handoffs", return_value=[h]):
            result = json.loads(tools["handoffs_pending"]())
        assert result["count"] == 1
        assert len(result["handoffs"]) == 1

    def test_filtered(self):
        tools = _register()
        with patch(f"{_P}.get_pending_handoffs", return_value=[]) as mock_get:
            tools["handoffs_pending"](for_agent="CODING")
        mock_get.assert_called_with(for_agent="CODING")

    def test_exception(self):
        tools = _register()
        with patch(f"{_P}.get_pending_handoffs", side_effect=Exception("fail")):
            result = json.loads(tools["handoffs_pending"]())
        assert "error" in result


class TestHandoffComplete:
    def test_success(self):
        tools = _register()
        handoff = _make_handoff()
        with patch(f"{_P}.Path") as mock_path_cls:
            mock_filepath = MagicMock()
            mock_filepath.exists.return_value = True
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_filepath)
            mock_path_cls.__class__ = Path
            # Mock evidence_dir from __file__
            with patch(f"{_P}.read_handoff_evidence", return_value=handoff), \
                 patch(f"{_P}.write_handoff_evidence"):
                result = json.loads(tools["handoff_complete"](
                    task_id="T-1", from_agent="research", to_agent="coding",
                    completion_notes="Done",
                ))
        assert result["status"] == "completed"

    def test_not_found(self):
        tools = _register()
        with patch(f"{_P}.Path") as mock_path_cls:
            mock_filepath = MagicMock()
            mock_filepath.exists.return_value = False
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_filepath)
            result = json.loads(tools["handoff_complete"](
                task_id="T-1", from_agent="R", to_agent="C",
            ))
        assert "error" in result

    def test_parse_failure(self):
        tools = _register()
        with patch(f"{_P}.Path") as mock_path_cls:
            mock_filepath = MagicMock()
            mock_filepath.exists.return_value = True
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_filepath)
            with patch(f"{_P}.read_handoff_evidence", return_value=None):
                result = json.loads(tools["handoff_complete"](
                    task_id="T-1", from_agent="R", to_agent="C",
                ))
        assert "Failed to parse" in result["error"]

    def test_exception(self):
        tools = _register()
        with patch(f"{_P}.Path", side_effect=Exception("path error")):
            result = json.loads(tools["handoff_complete"](
                task_id="T-1", from_agent="R", to_agent="C",
            ))
        assert "error" in result


class TestHandoffGet:
    def test_success(self):
        tools = _register()
        handoff = _make_handoff()
        with patch(f"{_P}.Path") as mock_path_cls:
            mock_filepath = MagicMock()
            mock_filepath.exists.return_value = True
            mock_filepath.__str__ = MagicMock(return_value="/evidence/file.md")
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_filepath)
            with patch(f"{_P}.read_handoff_evidence", return_value=handoff):
                result = json.loads(tools["handoff_get"](
                    task_id="T-1", from_agent="R", to_agent="C",
                ))
        assert "handoff" in result

    def test_not_found(self):
        tools = _register()
        with patch(f"{_P}.Path") as mock_path_cls:
            mock_filepath = MagicMock()
            mock_filepath.exists.return_value = False
            mock_path_cls.return_value.__truediv__ = MagicMock(return_value=mock_filepath)
            result = json.loads(tools["handoff_get"](
                task_id="T-1", from_agent="R", to_agent="C",
            ))
        assert "error" in result


class TestHandoffRoute:
    def test_rd_task(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="RD-001"))
        assert result["recommended_agent"] == "RESEARCH"

    def test_ui_gap(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="GAP-UI-001"))
        assert result["recommended_agent"] == "CODING"

    def test_mcp_gap(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="GAP-MCP-001"))
        assert result["recommended_agent"] == "CODING"

    def test_data_gap(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="GAP-DATA-001"))
        assert result["recommended_agent"] == "CURATOR"

    def test_high_phase(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="P12"))
        assert result["recommended_agent"] == "CURATOR"

    def test_low_phase(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="P5"))
        assert result["recommended_agent"] == "RESEARCH"

    def test_default(self):
        tools = _register()
        result = json.loads(tools["handoff_route"](task_id="SOME-TASK"))
        assert result["recommended_agent"] == "RESEARCH"
