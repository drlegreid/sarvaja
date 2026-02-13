"""Batch 144: Unit tests for conflict_checker, mcp_preflight, agent_status."""
import importlib.util
import json
import sys
import types
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_HOOKS = Path(__file__).resolve().parents[2] / ".claude" / "hooks"


def _load_module(name, filepath):
    """Load a module directly from file, bypassing __init__.py."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Pre-wire the hooks package hierarchy for relative imports
_core_base = _load_module("hooks_core_base_b144", _HOOKS / "core" / "base.py")

# Create package stubs so checkers/mcp_preflight.py can do from ..core.base import HookResult
_hooks_pkg = types.ModuleType("hooks_pkg")
_hooks_pkg.__path__ = [str(_HOOKS)]
_hooks_pkg.__package__ = "hooks_pkg"

_core_pkg = types.ModuleType("hooks_pkg.core")
_core_pkg.__path__ = [str(_HOOKS / "core")]
_core_pkg.__package__ = "hooks_pkg.core"
_core_pkg.base = _core_base

_checkers_pkg = types.ModuleType("hooks_pkg.checkers")
_checkers_pkg.__path__ = [str(_HOOKS / "checkers")]
_checkers_pkg.__package__ = "hooks_pkg.checkers"

sys.modules["hooks_pkg"] = _hooks_pkg
sys.modules["hooks_pkg.core"] = _core_pkg
sys.modules["hooks_pkg.core.base"] = _core_base
sys.modules["hooks_pkg.checkers"] = _checkers_pkg


# ===== Module 1: checkers/conflict_checker.py ==================================

_conflict = _load_module("checkers_conflict", _HOOKS / "checkers" / "conflict_checker.py")
run_git_command = _conflict.run_git_command
check_merge_conflicts = _conflict.check_merge_conflicts
_get_status_meaning = _conflict._get_status_meaning
_check_merge_state = _conflict._check_merge_state
scan_for_conflict_markers = _conflict.scan_for_conflict_markers
get_conflict_summary = _conflict.get_conflict_summary


class TestRunGitCommand:
    @patch("subprocess.run")
    def test_success(self, sub_run):
        sub_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        code, out, err = run_git_command(["status"])
        assert code == 0
        assert out == "output"

    @patch("subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("git", 30))
    def test_timeout(self, sub_run):
        code, out, err = run_git_command(["status"])
        assert code == -1
        assert "timed out" in err

    @patch("subprocess.run", side_effect=FileNotFoundError("no git"))
    def test_no_git(self, sub_run):
        code, out, err = run_git_command(["status"])
        assert code == -1
        assert "not found" in err


class TestGetStatusMeaning:
    def test_both_modified(self):
        assert _get_status_meaning("UU") == "both modified"

    def test_both_added(self):
        assert _get_status_meaning("AA") == "both added"

    def test_unknown(self):
        assert _get_status_meaning("XX") == "unmerged"


class TestCheckMergeConflicts:
    @patch.object(_conflict, "run_git_command")
    @patch.object(_conflict, "_check_merge_state")
    def test_no_conflicts(self, merge_state, git_cmd):
        git_cmd.return_value = (0, " M file.py\n?? new.py\n", "")
        merge_state.return_value = {"in_merge": False, "in_conflicted_state": False}
        result = check_merge_conflicts()
        assert result["has_conflicts"] is False
        assert result["conflict_count"] == 0

    @patch.object(_conflict, "run_git_command")
    @patch.object(_conflict, "_check_merge_state")
    def test_with_conflicts(self, merge_state, git_cmd):
        git_cmd.return_value = (0, "UU file.py\nAA other.py\n", "")
        merge_state.return_value = {"in_merge": True, "in_conflicted_state": True}
        result = check_merge_conflicts()
        assert result["has_conflicts"] is True
        assert result["conflict_count"] == 2
        assert result["conflicts"][0]["status"] == "UU"

    @patch.object(_conflict, "run_git_command")
    def test_git_error(self, git_cmd):
        git_cmd.return_value = (1, "", "fatal: not a git repo")
        result = check_merge_conflicts()
        assert result["has_conflicts"] is False
        assert "error" in result


class TestCheckMergeState:
    def test_not_in_merge(self):
        with tempfile.TemporaryDirectory() as td:
            git_dir = Path(td) / ".git"
            git_dir.mkdir()
            with patch.object(_conflict, "PROJECT_ROOT", Path(td)):
                state = _check_merge_state()
                assert state["in_merge"] is False
                assert state["in_conflicted_state"] is False

    def test_in_merge(self):
        with tempfile.TemporaryDirectory() as td:
            git_dir = Path(td) / ".git"
            git_dir.mkdir()
            (git_dir / "MERGE_HEAD").touch()
            with patch.object(_conflict, "PROJECT_ROOT", Path(td)):
                state = _check_merge_state()
                assert state["in_merge"] is True
                assert state["in_conflicted_state"] is True


class TestScanConflictMarkers:
    @patch.object(_conflict, "run_git_command")
    def test_no_markers(self, git_cmd):
        git_cmd.side_effect = [
            (0, "file1.py\nfile2.py\n", ""),  # ls-files
            (1, "", ""),  # grep -l (no matches)
        ]
        result = scan_for_conflict_markers()
        assert result == []

    @patch.object(_conflict, "run_git_command")
    def test_markers_found(self, git_cmd):
        git_cmd.side_effect = [
            (0, "file1.py\nfile2.py\n", ""),  # ls-files
            (0, "file1.py\n", ""),  # grep found markers
        ]
        result = scan_for_conflict_markers()
        assert len(result) == 1
        assert result[0]["file"] == "file1.py"


class TestGetConflictSummary:
    @patch.object(_conflict, "scan_for_conflict_markers")
    @patch.object(_conflict, "check_merge_conflicts")
    def test_clean(self, check, scan):
        check.return_value = {
            "has_conflicts": False, "conflict_count": 0,
            "conflicts": [], "merge_state": {"in_merge": False, "in_conflicted_state": False},
        }
        scan.return_value = []
        result = get_conflict_summary()
        assert result["status"] == "OK"
        assert result["alert_count"] == 0

    @patch.object(_conflict, "scan_for_conflict_markers")
    @patch.object(_conflict, "check_merge_conflicts")
    def test_with_conflicts(self, check, scan):
        check.return_value = {
            "has_conflicts": True, "conflict_count": 1,
            "conflicts": [{"file": "a.py", "status": "UU", "status_meaning": "both modified", "severity": "CRITICAL"}],
            "merge_state": {"in_merge": True, "in_conflicted_state": True},
        }
        scan.return_value = []
        result = get_conflict_summary()
        assert result["status"] == "CRITICAL"
        assert result["alert_count"] >= 2  # conflict + merge in progress


# ===== Module 2: checkers/mcp_preflight.py =====================================
# Needs core.base loaded first — use package-aware loading

def _load_checker_module(name, filepath):
    """Load a checker module with proper package context for relative imports."""
    spec = importlib.util.spec_from_file_location(
        f"hooks_pkg.checkers.{name}", filepath,
        submodule_search_locations=[]
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "hooks_pkg.checkers"
    sys.modules[f"hooks_pkg.checkers.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod

_mcp_pre = _load_checker_module("mcp_preflight", _HOOKS / "checkers" / "mcp_preflight.py")
MCPPreflightChecker = _mcp_pre.MCPPreflightChecker


class TestMCPPreflightChecker:
    def test_init_default(self):
        c = MCPPreflightChecker()
        assert c.project_root is not None

    def test_init_custom_root(self):
        c = MCPPreflightChecker(project_root=Path("/tmp"))
        assert c.project_root == Path("/tmp")


class TestFindDuplicateTools:
    def test_no_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tool_dir = root / "governance" / "mcp_tools"
            tool_dir.mkdir(parents=True)
            (tool_dir / "a.py").write_text("def governance_task_get(): pass\n")
            (tool_dir / "b.py").write_text("def governance_rule_get(): pass\n")
            c = MCPPreflightChecker(project_root=root)
            dups = c.find_duplicate_tools()
            assert len(dups) == 0

    def test_with_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tool_dir = root / "governance" / "mcp_tools"
            tool_dir.mkdir(parents=True)
            (tool_dir / "a.py").write_text("def governance_task_get(): pass\n")
            (tool_dir / "b.py").write_text("def governance_task_get(): pass\n")
            c = MCPPreflightChecker(project_root=root)
            dups = c.find_duplicate_tools()
            assert "governance_task_get" in dups
            assert len(dups["governance_task_get"]) == 2


class TestCheckModuleSyntax:
    def test_valid_syntax(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "governance").mkdir()
            (root / "governance" / "mcp_server_core.py").write_text("x = 1\n")
            c = MCPPreflightChecker(project_root=root)
            errors = c.check_module_syntax()
            assert len(errors) == 0

    def test_syntax_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "governance").mkdir()
            (root / "governance" / "mcp_server_core.py").write_text("def foo(:\n")
            c = MCPPreflightChecker(project_root=root)
            errors = c.check_module_syntax()
            assert len(errors) == 1
            assert "Syntax error" in errors[0]


class TestMCPPreflightCheck:
    def test_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "governance").mkdir()
            (root / "governance" / "mcp_tools").mkdir()
            c = MCPPreflightChecker(project_root=root)
            result = c.check()
            assert result.success is True

    def test_get_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "governance").mkdir()
            (root / "governance" / "mcp_tools").mkdir()
            c = MCPPreflightChecker(project_root=root)
            status = c.get_status()
            assert status["ok"] is True


# ===== Module 3: checkers/agent_status.py ======================================

_agent = _load_module("checkers_agent_status", _HOOKS / "checkers" / "agent_status.py")
load_agent_status = _agent.load_agent_status
save_agent_status = _agent.save_agent_status
update_agent_heartbeat = _agent.update_agent_heartbeat
check_stuck_agents = _agent.check_stuck_agents
check_file_locks = _agent.check_file_locks
acquire_file_lock = _agent.acquire_file_lock
release_file_lock = _agent.release_file_lock
get_agent_status_summary = _agent.get_agent_status_summary


class TestLoadSaveAgentStatus:
    def test_load_missing(self):
        with patch.object(_agent, "STATUS_FILE", Path("/tmp/nonexistent_agent.json")):
            s = load_agent_status()
            assert s["agents"] == {}

    def test_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            with patch.object(_agent, "STATUS_FILE", tmp):
                save_agent_status({"agents": {"a1": {"status": "active"}}})
                loaded = load_agent_status()
                assert loaded["agents"]["a1"]["status"] == "active"
                assert "last_updated" in loaded
        finally:
            tmp.unlink(missing_ok=True)


class TestUpdateAgentHeartbeat:
    def test_new_agent(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "agents" / "status.json"
            locks_dir = Path(td) / "agents" / "locks"
            with patch.object(_agent, "STATUS_FILE", status_file), \
                 patch.object(_agent, "LOCKS_DIR", locks_dir):
                result = update_agent_heartbeat("agent-1", "claude-code", "TASK-001")
                assert result["agent_type"] == "claude-code"
                assert result["current_task"] == "TASK-001"
                assert result["heartbeat_count"] == 1

    def test_increment_heartbeat(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "agents" / "status.json"
            locks_dir = Path(td) / "agents" / "locks"
            with patch.object(_agent, "STATUS_FILE", status_file), \
                 patch.object(_agent, "LOCKS_DIR", locks_dir):
                update_agent_heartbeat("a1", "test")
                result = update_agent_heartbeat("a1", "test")
                assert result["heartbeat_count"] == 2


class TestCheckStuckAgents:
    def test_no_stuck(self):
        now = datetime.now().isoformat()
        status = {"agents": {"a1": {"last_heartbeat": now, "agent_type": "test"}}}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(status, f)
            tmp = Path(f.name)
        try:
            with patch.object(_agent, "STATUS_FILE", tmp):
                stuck = check_stuck_agents()
                assert len(stuck) == 0
        finally:
            tmp.unlink(missing_ok=True)

    def test_stuck_agent(self):
        old = (datetime.now() - timedelta(minutes=10)).isoformat()
        status = {"agents": {"a1": {"last_heartbeat": old, "agent_type": "test", "current_task": "T1"}}}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(status, f)
            tmp = Path(f.name)
        try:
            with patch.object(_agent, "STATUS_FILE", tmp):
                stuck = check_stuck_agents()
                assert len(stuck) == 1
                assert stuck[0]["agent_id"] == "a1"
                assert stuck[0]["severity"] == "CRITICAL"  # >600s
        finally:
            tmp.unlink(missing_ok=True)


class TestFileLocks:
    def test_acquire_release(self):
        with tempfile.TemporaryDirectory() as td:
            locks_dir = Path(td) / "locks"
            with patch.object(_agent, "LOCKS_DIR", locks_dir):
                lock = acquire_file_lock("TODO.md", "agent-1", timeout_seconds=2)
                assert lock is not None
                assert lock.exists()
                released = release_file_lock("TODO.md", "agent-1")
                assert released is True
                assert not lock.exists()

    def test_release_wrong_owner(self):
        with tempfile.TemporaryDirectory() as td:
            locks_dir = Path(td) / "locks"
            with patch.object(_agent, "LOCKS_DIR", locks_dir):
                acquire_file_lock("TODO.md", "agent-1", timeout_seconds=2)
                released = release_file_lock("TODO.md", "agent-2")
                assert released is False

    def test_release_nonexistent(self):
        with tempfile.TemporaryDirectory() as td:
            locks_dir = Path(td) / "locks"
            locks_dir.mkdir(parents=True)
            with patch.object(_agent, "LOCKS_DIR", locks_dir):
                assert release_file_lock("nonexistent.md", "a1") is False

    def test_check_no_stale(self):
        with tempfile.TemporaryDirectory() as td:
            locks_dir = Path(td) / "locks"
            locks_dir.mkdir(parents=True)
            with patch.object(_agent, "LOCKS_DIR", locks_dir):
                stale = check_file_locks()
                assert len(stale) == 0


class TestGetAgentStatusSummary:
    def test_clean(self):
        now = datetime.now().isoformat()
        status = {"agents": {"a1": {"last_heartbeat": now, "agent_type": "test"}}, "last_updated": now}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(status, f)
            tmp = Path(f.name)
        with tempfile.TemporaryDirectory() as td:
            locks_dir = Path(td) / "locks"
            locks_dir.mkdir(parents=True)
            try:
                with patch.object(_agent, "STATUS_FILE", tmp), \
                     patch.object(_agent, "LOCKS_DIR", locks_dir):
                    result = get_agent_status_summary()
                    assert result["status"] == "OK"
                    assert result["agent_count"] == 1
                    assert result["alert_count"] == 0
            finally:
                tmp.unlink(missing_ok=True)
