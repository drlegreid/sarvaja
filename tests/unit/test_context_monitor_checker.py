"""
Unit tests for Context Monitor Checker.

Batch 158b: Tests for .claude/hooks/checkers/context_monitor.py
- get_default_state, load_state, save_state
- capture_context
- get_level, format_status, check_warning
"""

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_module():
    mod_path = (
        Path(__file__).parent.parent.parent
        / ".claude" / "hooks" / "checkers" / "context_monitor.py"
    )
    spec = importlib.util.spec_from_file_location("context_monitor", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()
get_default_state = _mod.get_default_state
load_state = _mod.load_state
save_state = _mod.save_state
capture_context = _mod.capture_context
get_level = _mod.get_level
format_status = _mod.format_status
check_warning = _mod.check_warning


# ── get_default_state ─────────────────────────────────────

class TestGetDefaultState:
    def test_has_required_keys(self):
        state = get_default_state()
        for key in ["total_input_tokens", "total_output_tokens",
                     "context_window_size", "used_percentage",
                     "remaining_percentage", "tool_count", "history"]:
            assert key in state

    def test_defaults(self):
        state = get_default_state()
        assert state["total_input_tokens"] == 0
        assert state["context_window_size"] == 200000
        assert state["used_percentage"] == 0.0
        assert state["history"] == []


# ── load_state / save_state ───────────────────────────────

class TestLoadSaveState:
    def test_load_missing_file(self, tmp_path):
        fake_path = tmp_path / "nonexistent.json"
        with patch.object(_mod, "STATE_FILE", fake_path):
            state = load_state()
        assert state["total_input_tokens"] == 0

    def test_save_and_load(self, tmp_path):
        state_file = tmp_path / "state.json"
        with patch.object(_mod, "STATE_FILE", state_file):
            state = {"total_input_tokens": 1000, "tool_count": 5, "history": []}
            save_state(state)
            loaded = load_state()
        assert loaded["total_input_tokens"] == 1000
        assert loaded["tool_count"] == 5
        assert "last_updated" in loaded

    def test_load_corrupt_json(self, tmp_path):
        state_file = tmp_path / "bad.json"
        state_file.write_text("{corrupt")
        with patch.object(_mod, "STATE_FILE", state_file):
            state = load_state()
        assert state["total_input_tokens"] == 0  # fallback to default


# ── capture_context ───────────────────────────────────────

class TestCaptureContext:
    def test_captures_context_window(self, tmp_path):
        state_file = tmp_path / "ctx.json"
        with patch.object(_mod, "STATE_FILE", state_file):
            hook_data = {
                "context_window": {
                    "total_input_tokens": 50000,
                    "total_output_tokens": 10000,
                    "context_window_size": 200000,
                    "used_percentage": 30.0,
                    "remaining_percentage": 70.0,
                }
            }
            state = capture_context(hook_data)
        assert state["total_input_tokens"] == 50000
        assert state["used_percentage"] == 30.0

    def test_increments_tool_count(self, tmp_path):
        state_file = tmp_path / "ctx.json"
        with patch.object(_mod, "STATE_FILE", state_file):
            capture_context({})
            state = capture_context({})
        assert state["tool_count"] == 2

    def test_history_capped_at_20(self, tmp_path):
        state_file = tmp_path / "ctx.json"
        with patch.object(_mod, "STATE_FILE", state_file):
            for i in range(25):
                capture_context({
                    "context_window": {"used_percentage": float(i)}
                })
            state = load_state()
        assert len(state["history"]) == 20

    def test_empty_hook_data(self, tmp_path):
        state_file = tmp_path / "ctx.json"
        with patch.object(_mod, "STATE_FILE", state_file):
            state = capture_context({})
        assert state["tool_count"] == 1
        assert state["total_input_tokens"] == 0


# ── get_level ─────────────────────────────────────────────

class TestGetLevel:
    def test_low(self):
        assert get_level(10.0) == "LOW"
        assert get_level(49.9) == "LOW"

    def test_medium(self):
        assert get_level(50.0) == "MEDIUM"
        assert get_level(74.9) == "MEDIUM"

    def test_high(self):
        assert get_level(75.0) == "HIGH"
        assert get_level(89.9) == "HIGH"

    def test_critical(self):
        assert get_level(90.0) == "CRITICAL"
        assert get_level(100.0) == "CRITICAL"


# ── format_status ─────────────────────────────────────────

class TestFormatStatus:
    def test_includes_all_fields(self):
        state = {
            "used_percentage": 55.0,
            "total_input_tokens": 110000,
            "total_output_tokens": 5000,
            "context_window_size": 200000,
            "tool_count": 42,
            "last_updated": "2026-02-13T10:00:00",
        }
        text = format_status(state)
        assert "MEDIUM" in text
        assert "55.0%" in text
        assert "110,000" in text
        assert "42" in text

    def test_default_state(self):
        state = get_default_state()
        text = format_status(state)
        assert "LOW" in text
        assert "0.0%" in text


# ── check_warning ─────────────────────────────────────────

class TestCheckWarning:
    def test_no_warning_below_50(self):
        assert check_warning({"used_percentage": 30.0}) is None

    def test_medium_warning(self):
        warn = check_warning({"used_percentage": 55.0, "total_input_tokens": 110000})
        assert warn is not None
        assert "MEDIUM" in warn

    def test_high_warning(self):
        warn = check_warning({"used_percentage": 80.0, "total_input_tokens": 160000})
        assert "HIGH" in warn

    def test_critical_warning(self):
        warn = check_warning({"used_percentage": 95.0, "total_input_tokens": 190000})
        assert "CRITICAL" in warn
        assert "SAVE CONTEXT" in warn
