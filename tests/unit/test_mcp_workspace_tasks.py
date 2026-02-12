"""
Unit tests for Workspace Task Scanning MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/workspace_tasks.py module.
Tests: register_workspace_task_tools — workspace_scan_tasks,
       workspace_capture_tasks, workspace_list_sources.
"""

import json
from unittest.mock import patch, MagicMock

import pytest


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


_P = "governance.mcp_tools.workspace_tasks"


@pytest.fixture(autouse=True)
def _format_mcp():
    with patch(f"{_P}.format_mcp_result",
               side_effect=lambda x: json.dumps(x)):
        yield


def _register():
    from governance.mcp_tools.workspace_tasks import register_workspace_task_tools
    mcp = _CaptureMCP()
    register_workspace_task_tools(mcp)
    return mcp.tools


def _make_task(task_id="T-1", name="Test task", status="OPEN", source_file="TODO.md"):
    t = MagicMock()
    t.task_id = task_id
    t.name = name
    t.status = status
    t.source_file = source_file
    return t


class TestWorkspaceScanTasks:
    def test_success(self):
        tools = _register()
        tasks = [_make_task(), _make_task("T-2", "Task 2", "DONE")]
        with patch("governance.workspace_scanner.scan_workspace", return_value=tasks):
            result = json.loads(tools["workspace_scan_tasks"]())
        assert result["total_tasks"] == 2
        assert result["sources"] == 1

    def test_multiple_sources(self):
        tools = _register()
        tasks = [
            _make_task("T-1", source_file="TODO.md"),
            _make_task("T-2", source_file="PHASE-1.md"),
        ]
        with patch("governance.workspace_scanner.scan_workspace", return_value=tasks):
            result = json.loads(tools["workspace_scan_tasks"]())
        assert result["sources"] == 2

    def test_empty(self):
        tools = _register()
        with patch("governance.workspace_scanner.scan_workspace", return_value=[]):
            result = json.loads(tools["workspace_scan_tasks"]())
        assert result["total_tasks"] == 0

    def test_exception(self):
        tools = _register()
        with patch("governance.workspace_scanner.scan_workspace",
                   side_effect=Exception("scan error")):
            result = json.loads(tools["workspace_scan_tasks"]())
        assert "error" in result

    def test_sample_limit(self):
        tools = _register()
        tasks = [_make_task(f"T-{i}") for i in range(5)]
        with patch("governance.workspace_scanner.scan_workspace", return_value=tasks):
            result = json.loads(tools["workspace_scan_tasks"]())
        # Sample limited to 3 per source
        assert len(result["by_source"]["TODO.md"]["sample"]) == 3

    def test_status_counting(self):
        tools = _register()
        tasks = [
            _make_task("T-1", status="OPEN"),
            _make_task("T-2", status="OPEN"),
            _make_task("T-3", status="DONE"),
        ]
        with patch("governance.workspace_scanner.scan_workspace", return_value=tasks):
            result = json.loads(tools["workspace_scan_tasks"]())
        statuses = result["by_source"]["TODO.md"]["statuses"]
        assert statuses["OPEN"] == 2
        assert statuses["DONE"] == 1


class TestWorkspaceCaptureTasks:
    def test_success(self):
        tools = _register()
        with patch("governance.workspace_scanner.capture_workspace_tasks",
                   return_value={"scanned": 10, "inserted": 5, "updated": 2}):
            result = json.loads(tools["workspace_capture_tasks"]())
        assert result["scanned"] == 10
        assert result["inserted"] == 5

    def test_exception(self):
        tools = _register()
        with patch("governance.workspace_scanner.capture_workspace_tasks",
                   side_effect=Exception("sync error")):
            result = json.loads(tools["workspace_capture_tasks"]())
        assert "error" in result


class TestWorkspaceListSources:
    def test_with_todo(self):
        tools = _register()
        with patch("governance.workspace_scanner.WORKSPACE_ROOT", "/tmp/test"), \
             patch("os.path.exists", side_effect=lambda p: "TODO" in p), \
             patch("os.path.join", side_effect=lambda *args: "/".join(args)):
            result = json.loads(tools["workspace_list_sources"]())
        assert "TODO.md" in result["sources"]

    def test_with_phases_and_rd(self):
        tools = _register()
        def mock_exists(path):
            return True
        def mock_listdir(path):
            if "phases" in path:
                return ["PHASE-1.md", "PHASE-2.md", "README.md"]
            if "rd" in path:
                return ["RD-001.md", "other.txt"]
            return []
        with patch("governance.workspace_scanner.WORKSPACE_ROOT", "/tmp/test"), \
             patch("os.path.exists", side_effect=mock_exists), \
             patch("os.path.join", side_effect=lambda *args: "/".join(args)), \
             patch("os.listdir", side_effect=mock_listdir):
            result = json.loads(tools["workspace_list_sources"]())
        # TODO.md + 2 PHASE files + 1 RD file = 4
        assert result["source_count"] == 4

    def test_no_directories(self):
        tools = _register()
        with patch("governance.workspace_scanner.WORKSPACE_ROOT", "/tmp/test"), \
             patch("os.path.exists", return_value=False), \
             patch("os.path.join", side_effect=lambda *args: "/".join(args)):
            result = json.loads(tools["workspace_list_sources"]())
        assert result["source_count"] == 0
