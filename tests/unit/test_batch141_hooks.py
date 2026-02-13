"""Batch 141: Unit tests for entropy_cli, destructive checker, context_monitor."""
import importlib.util
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_HOOKS = Path(__file__).resolve().parents[2] / ".claude" / "hooks"
sys.path.insert(0, str(_HOOKS))


def _load_module(name, filepath):
    """Load a module directly from file, bypassing __init__.py."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ===== Module 1: entropy_cli.py ==============================================

from entropy_cli import (
    get_default_state,
    get_entropy_level,
    increment_and_check,
    load_state,
    save_state,
    show_status,
    reset_state,
    MEDIUM_THRESHOLD,
    HIGH_THRESHOLD,
    CRITICAL_THRESHOLD,
)


class TestGetEntropyLevel:
    def test_low(self):
        assert get_entropy_level(0) == "LOW"
        assert get_entropy_level(49) == "LOW"

    def test_medium(self):
        assert get_entropy_level(50) == "MEDIUM"
        assert get_entropy_level(99) == "MEDIUM"

    def test_high(self):
        assert get_entropy_level(100) == "HIGH"
        assert get_entropy_level(149) == "HIGH"

    def test_critical(self):
        assert get_entropy_level(150) == "CRITICAL"
        assert get_entropy_level(500) == "CRITICAL"


class TestGetDefaultState:
    def test_fields(self):
        s = get_default_state()
        assert s["tool_count"] == 0
        assert s["warnings_shown"] == 0
        assert "session_start" in s
        assert s["history"] == []


class TestEntropySaveLoad:
    def test_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            with patch("entropy_cli.STATE_FILE", tmp):
                state = {"tool_count": 42, "check_count": 10}
                save_state(state)
                loaded = load_state()
                assert loaded["tool_count"] == 42
        finally:
            tmp.unlink(missing_ok=True)

    def test_load_missing_file(self):
        with patch("entropy_cli.STATE_FILE", Path("/tmp/nonexistent_12345.json")):
            s = load_state()
            assert s["tool_count"] == 0


class TestIncrementAndCheck:
    def _run_increment(self, tool_count=0, warnings_shown=0, last_warning_at=0):
        state = {
            "tool_count": tool_count,
            "check_count": 0,
            "warnings_shown": warnings_shown,
            "last_warning_at": last_warning_at,
            "session_start": datetime.now().isoformat(),
            "history": [],
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(state, f)
            tmp = Path(f.name)
        try:
            with patch("entropy_cli.STATE_FILE", tmp):
                code = increment_and_check(quiet=True)
                final = json.loads(tmp.read_text())
                return code, final
        finally:
            tmp.unlink(missing_ok=True)

    def test_low_no_warning(self):
        code, state = self._run_increment(tool_count=10)
        assert code == 0
        assert state["tool_count"] == 11

    def test_medium_first_warning(self):
        code, state = self._run_increment(tool_count=MEDIUM_THRESHOLD - 1)
        assert code == 1  # warning
        assert state["warnings_shown"] == 1

    def test_high_warning(self):
        code, state = self._run_increment(
            tool_count=HIGH_THRESHOLD + 14, warnings_shown=1, last_warning_at=MEDIUM_THRESHOLD
        )
        assert code == 1
        assert state["warnings_shown"] == 2

    def test_critical_first_crossing(self):
        code, state = self._run_increment(
            tool_count=CRITICAL_THRESHOLD - 1, warnings_shown=2, last_warning_at=HIGH_THRESHOLD
        )
        assert code == 1


class TestResetState:
    def test_resets_tool_count(self):
        state = {"tool_count": 100, "session_hash": "OLD", "history": []}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(state, f)
            tmp = Path(f.name)
        try:
            with patch("entropy_cli.STATE_FILE", tmp):
                code = reset_state()
                final = json.loads(tmp.read_text())
                assert final["tool_count"] == 0
                assert code == 0
        finally:
            tmp.unlink(missing_ok=True)

    def test_warns_on_critical_previous(self):
        state = {"tool_count": 200, "session_hash": "H", "history": []}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(state, f)
            tmp = Path(f.name)
        try:
            with patch("entropy_cli.STATE_FILE", tmp):
                code = reset_state()
                assert code == 1  # non-blocking warning
        finally:
            tmp.unlink(missing_ok=True)


# ===== Module 2: checkers/destructive.py =====================================

_destr = _load_module("checkers_destructive", _HOOKS / "checkers" / "destructive.py")
check_destructive_command = _destr.check_destructive_command
format_warning = _destr.format_warning
get_safe_alternative = _destr.get_safe_alternative
DestructiveCheckResult = _destr.DestructiveCheckResult


class TestCheckDestructive:
    def test_safe_command(self):
        r = check_destructive_command("ls -la")
        assert r.is_destructive is False
        assert r.is_blocked is False

    def test_rm_rf(self):
        r = check_destructive_command("rm -rf /tmp/test")
        assert r.is_destructive is True
        assert r.is_blocked is False

    def test_rm_rf_root_blocked(self):
        r = check_destructive_command("rm -rf /")
        assert r.is_blocked is True

    def test_git_reset_hard(self):
        r = check_destructive_command("git reset --hard HEAD~1")
        assert r.is_destructive is True
        assert "uncommitted" in r.risk_description.lower()

    def test_git_push_force(self):
        r = check_destructive_command("git push --force origin main")
        assert r.is_destructive is True

    def test_podman_prune(self):
        r = check_destructive_command("podman system prune -a")
        assert r.is_destructive is True

    def test_drop_table(self):
        r = check_destructive_command("DROP TABLE users")
        assert r.is_destructive is True

    def test_delete_without_where(self):
        r = check_destructive_command("DELETE FROM users;")
        assert r.is_destructive is True

    def test_typeql_delete(self):
        r = check_destructive_command('match $t isa task; delete $t;')
        assert r.is_destructive is True

    def test_git_push_f(self):
        r = check_destructive_command("git push -f origin main")
        assert r.is_destructive is True


class TestFormatWarning:
    def test_blocked(self):
        r = DestructiveCheckResult(True, True, "p", "System destruction", "rm -rf /")
        msg = format_warning(r)
        assert "BLOCKED" in msg
        assert "NEVER allowed" in msg

    def test_destructive(self):
        r = DestructiveCheckResult(True, False, "p", "Recursive deletion", "rm -rf tmp")
        msg = format_warning(r)
        assert "WARNING" in msg
        assert "SAFETY-DESTR-01" in msg

    def test_safe(self):
        r = DestructiveCheckResult(False, False, None, None, "ls")
        assert format_warning(r) == ""


class TestGetSafeAlternative:
    def test_rm_alternative(self):
        r = DestructiveCheckResult(True, False, "p", "rm -rf: Recursive file deletion", "rm -rf tmp")
        alt = get_safe_alternative(r)
        assert alt is not None
        assert "rm -i" in alt

    def test_git_reset_alternative(self):
        r = DestructiveCheckResult(True, False, "p", "git reset --hard: Loses changes", "git reset --hard")
        alt = get_safe_alternative(r)
        assert "stash" in alt

    def test_no_alternative(self):
        r = DestructiveCheckResult(True, False, "p", "Unknown risk", "some command")
        assert get_safe_alternative(r) is None


# ===== Module 3: checkers/context_monitor.py =================================

_ctx = _load_module("checkers_context_monitor", _HOOKS / "checkers" / "context_monitor.py")
cm_default_state = _ctx.get_default_state
capture_context = _ctx.capture_context
get_level = _ctx.get_level
format_status = _ctx.format_status
check_warning = _ctx.check_warning


class TestContextGetLevel:
    def test_low(self):
        assert get_level(0) == "LOW"
        assert get_level(49.9) == "LOW"

    def test_medium(self):
        assert get_level(50) == "MEDIUM"

    def test_high(self):
        assert get_level(75) == "HIGH"

    def test_critical(self):
        assert get_level(90) == "CRITICAL"


class TestCaptureContext:
    def test_with_context_window(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(cm_default_state(), f)
            tmp = Path(f.name)
        try:
            with patch.object(_ctx, "STATE_FILE", tmp):
                state = capture_context({
                    "context_window": {
                        "total_input_tokens": 50000,
                        "total_output_tokens": 10000,
                        "context_window_size": 200000,
                        "used_percentage": 30.0,
                        "remaining_percentage": 70.0,
                    }
                })
                assert state["total_input_tokens"] == 50000
                assert state["used_percentage"] == 30.0
                assert state["tool_count"] == 1
                assert len(state["history"]) == 1
        finally:
            tmp.unlink(missing_ok=True)

    def test_without_context_window(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(cm_default_state(), f)
            tmp = Path(f.name)
        try:
            with patch.object(_ctx, "STATE_FILE", tmp):
                state = capture_context({})
                assert state["tool_count"] == 1
                assert state["total_input_tokens"] == 0
        finally:
            tmp.unlink(missing_ok=True)


class TestCheckWarning:
    def test_no_warning_low(self):
        assert check_warning({"used_percentage": 30}) is None

    def test_medium_warning(self):
        w = check_warning({"used_percentage": 55, "total_input_tokens": 100000})
        assert w is not None
        assert "MEDIUM" in w

    def test_high_warning(self):
        w = check_warning({"used_percentage": 80, "total_input_tokens": 160000})
        assert "HIGH" in w

    def test_critical_warning(self):
        w = check_warning({"used_percentage": 95, "total_input_tokens": 190000})
        assert "CRITICAL" in w
        assert "SAVE" in w


class TestFormatStatus:
    def test_output(self):
        s = format_status({"used_percentage": 42.5, "total_input_tokens": 85000,
                           "total_output_tokens": 15000, "context_window_size": 200000,
                           "tool_count": 30, "last_updated": "2026-02-13T10:00:00"})
        assert "42.5%" in s
        assert "85,000" in s
        assert "Tool Calls: 30" in s
