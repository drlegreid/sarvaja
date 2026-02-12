"""
Unit tests for Orchestrator Workspace Launcher.

Per DOC-SIZE-01-v1: Tests for orchestrator/launcher.py module.
Tests: LaunchConfig, LaunchResult, get_workspaces_dir, get_workspace_path,
       list_workspaces, validate_workspace, prepare_launch_environment,
       launch_workspace, launch_all_pending, generate_launch_script.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.orchestrator.launcher import (
    LaunchConfig,
    LaunchResult,
    get_workspaces_dir,
    get_workspace_path,
    list_workspaces,
    validate_workspace,
    prepare_launch_environment,
    launch_workspace,
    launch_for_handoff,
    launch_all_pending,
    generate_launch_script,
)


class TestLaunchConfig:
    def test_to_dict(self):
        cfg = LaunchConfig(workspace_path=Path("/tmp/ws"), agent_role="CODING")
        d = cfg.to_dict()
        assert d["workspace_path"] == "/tmp/ws"
        assert d["agent_role"] == "CODING"
        assert d["background"] is False

    def test_with_task(self):
        cfg = LaunchConfig(
            workspace_path=Path("/tmp/ws"), agent_role="RESEARCH",
            task_id="T-1", task_context={"key": "val"},
        )
        d = cfg.to_dict()
        assert d["task_id"] == "T-1"
        assert d["task_context"]["key"] == "val"


class TestLaunchResult:
    def test_defaults(self):
        r = LaunchResult(success=True, agent_role="CODING", workspace_path="/tmp")
        assert r.pid is None
        assert r.error is None
        assert r.launched_at  # auto-filled

    def test_with_error(self):
        r = LaunchResult(success=False, agent_role="X", workspace_path="/tmp",
                         error="command not found")
        assert r.error == "command not found"


class TestGetWorkspacesDir:
    def test_default_path(self):
        result = get_workspaces_dir()
        assert result.name == "workspaces"

    def test_custom_root(self):
        result = get_workspaces_dir(Path("/custom/root"))
        assert result == Path("/custom/root/workspaces")


class TestGetWorkspacePath:
    def test_lowercase(self):
        result = get_workspace_path("CODING")
        assert "coding" in str(result)

    def test_custom_root(self):
        result = get_workspace_path("RESEARCH", Path("/myproject"))
        assert result == Path("/myproject/workspaces/research")


class TestListWorkspaces:
    def test_no_workspaces_dir(self, tmp_path):
        result = list_workspaces(tmp_path)
        assert result == []

    def test_with_valid_workspaces(self, tmp_path):
        ws_dir = tmp_path / "workspaces"
        # Create a valid workspace
        coding = ws_dir / "coding"
        coding.mkdir(parents=True)
        (coding / "CLAUDE.md").write_text("# Coding Agent")
        # Create invalid workspace (no CLAUDE.md)
        invalid = ws_dir / "invalid"
        invalid.mkdir()
        result = list_workspaces(tmp_path)
        assert "CODING" in result
        assert "INVALID" not in result


class TestValidateWorkspace:
    def test_valid(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / "coding"
        ws_dir.mkdir(parents=True)
        (ws_dir / "CLAUDE.md").write_text("# Agent")
        (ws_dir / ".mcp.json").write_text("{}")
        (ws_dir / "skills").mkdir()
        assert validate_workspace("CODING", tmp_path) is True

    def test_no_workspace(self, tmp_path):
        assert validate_workspace("NONEXISTENT", tmp_path) is False

    def test_missing_claude_md(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / "coding"
        ws_dir.mkdir(parents=True)
        (ws_dir / ".mcp.json").write_text("{}")
        (ws_dir / "skills").mkdir()
        assert validate_workspace("CODING", tmp_path) is False

    def test_missing_mcp_json(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / "coding"
        ws_dir.mkdir(parents=True)
        (ws_dir / "CLAUDE.md").write_text("# Agent")
        (ws_dir / "skills").mkdir()
        assert validate_workspace("CODING", tmp_path) is False

    def test_missing_skills(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / "coding"
        ws_dir.mkdir(parents=True)
        (ws_dir / "CLAUDE.md").write_text("# Agent")
        (ws_dir / ".mcp.json").write_text("{}")
        assert validate_workspace("CODING", tmp_path) is False


class TestPrepareEnvironment:
    def test_basic(self):
        env = prepare_launch_environment("CODING")
        assert env["AGENT_ROLE"] == "CODING"
        assert env["AGENT_WORKSPACE"] == "coding"
        assert "TYPEDB_HOST" in env

    def test_with_task(self):
        env = prepare_launch_environment("RESEARCH", task_id="T-1",
                                          task_context={"priority": "HIGH"})
        assert env["TASK_ID"] == "T-1"
        assert '"priority"' in env["TASK_CONTEXT"]

    def test_no_task(self):
        env = prepare_launch_environment("CODING")
        assert "TASK_ID" not in env
        assert "TASK_CONTEXT" not in env


class TestLaunchWorkspace:
    def test_invalid_workspace(self, tmp_path):
        result = launch_workspace("NONEXISTENT", project_root=tmp_path)
        assert result.success is False
        assert "Invalid workspace" in result.error

    def test_dry_run(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / "coding"
        ws_dir.mkdir(parents=True)
        (ws_dir / "CLAUDE.md").write_text("# Agent")
        (ws_dir / ".mcp.json").write_text("{}")
        (ws_dir / "skills").mkdir()
        result = launch_workspace("CODING", project_root=tmp_path, dry_run=True)
        assert result.success is True
        assert "DRY RUN" in result.error

    def test_with_handoff(self, tmp_path):
        ws_dir = tmp_path / "workspaces" / "coding"
        ws_dir.mkdir(parents=True)
        (ws_dir / "CLAUDE.md").write_text("# Agent")
        (ws_dir / ".mcp.json").write_text("{}")
        (ws_dir / "skills").mkdir()
        handoff = MagicMock()
        handoff.to_dict.return_value = {"task_id": "T-1"}
        handoff.task_id = "T-1"
        result = launch_workspace("CODING", handoff=handoff,
                                   project_root=tmp_path, dry_run=True)
        assert result.success is True


class TestLaunchForHandoff:
    def test_delegates(self, tmp_path):
        handoff = MagicMock()
        handoff.to_agent = "CODING"
        handoff.to_dict.return_value = {}
        handoff.task_id = "T-1"
        result = launch_for_handoff(handoff, project_root=tmp_path, dry_run=True)
        assert result.agent_role == "CODING"


class TestLaunchAllPending:
    @patch("governance.orchestrator.launcher.get_pending_handoffs")
    def test_no_pending(self, mock_get):
        mock_get.return_value = []
        results = launch_all_pending(dry_run=True)
        assert results == []

    @patch("governance.orchestrator.launcher.get_pending_handoffs")
    def test_with_pending(self, mock_get, tmp_path):
        h = MagicMock()
        h.to_agent = "CODING"
        h.to_dict.return_value = {}
        h.task_id = "T-1"
        mock_get.return_value = [h]
        results = launch_all_pending(project_root=tmp_path, dry_run=True)
        assert len(results) == 1


class TestGenerateLaunchScript:
    def test_default_roles(self):
        script = generate_launch_script()
        assert "#!/bin/bash" in script
        assert "claude" in script

    def test_write_to_file(self, tmp_path):
        output = tmp_path / "launch.sh"
        script = generate_launch_script(output_path=output)
        assert output.exists()
        assert output.read_text() == script
