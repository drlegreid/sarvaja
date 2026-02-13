"""
Unit tests for Task Execution State Transforms.

Batch 156: Tests for agent/governance_ui/state/execution.py
- with_task_execution_log: sets log, loading=False, show=True
- with_task_execution_loading: clears log, loading=True
- with_task_execution_event: appends event to log
- clear_task_execution: resets all execution state
- get_execution_event_style: icon/color lookup
- format_execution_event: event enrichment with style + timestamp
"""

import pytest

from agent.governance_ui.state.execution import (
    with_task_execution_log,
    with_task_execution_loading,
    with_task_execution_event,
    clear_task_execution,
    get_execution_event_style,
    format_execution_event,
)


# ── with_task_execution_log ──────────────────────────────

class TestWithTaskExecutionLog:
    def test_sets_log(self):
        state = {"other": "data"}
        log = [{"event_type": "start"}]
        result = with_task_execution_log(state, log)
        assert result["task_execution_log"] == log
        assert result["task_execution_loading"] is False
        assert result["show_task_execution"] is True

    def test_preserves_existing_state(self):
        state = {"dashboard_tab": 2, "selected_task": "T-1"}
        result = with_task_execution_log(state, [])
        assert result["dashboard_tab"] == 2
        assert result["selected_task"] == "T-1"

    def test_empty_log(self):
        result = with_task_execution_log({}, [])
        assert result["task_execution_log"] == []


# ── with_task_execution_loading ──────────────────────────

class TestWithTaskExecutionLoading:
    def test_sets_loading(self):
        state = {"other": True}
        result = with_task_execution_loading(state)
        assert result["task_execution_loading"] is True
        assert result["task_execution_log"] == []

    def test_clears_previous_log(self):
        state = {"task_execution_log": [{"e": 1}]}
        result = with_task_execution_loading(state)
        assert result["task_execution_log"] == []


# ── with_task_execution_event ────────────────────────────

class TestWithTaskExecutionEvent:
    def test_appends_event(self):
        state = {"task_execution_log": [{"e": 1}]}
        event = {"event_type": "complete", "task_id": "T-1"}
        result = with_task_execution_event(state, event)
        assert len(result["task_execution_log"]) == 2
        assert result["task_execution_log"][1] == event

    def test_creates_log_if_missing(self):
        state = {}
        event = {"event_type": "start"}
        result = with_task_execution_event(state, event)
        assert len(result["task_execution_log"]) == 1

    def test_does_not_mutate_original(self):
        original_log = [{"e": 1}]
        state = {"task_execution_log": original_log}
        with_task_execution_event(state, {"e": 2})
        assert len(original_log) == 1  # Original unchanged


# ── clear_task_execution ─────────────────────────────────

class TestClearTaskExecution:
    def test_clears_all(self):
        state = {
            "task_execution_log": [{"e": 1}],
            "task_execution_loading": True,
            "show_task_execution": True,
        }
        result = clear_task_execution(state)
        assert result["task_execution_log"] == []
        assert result["task_execution_loading"] is False
        assert result["show_task_execution"] is False


# ── get_execution_event_style ────────────────────────────

class TestGetExecutionEventStyle:
    def test_unknown_type_defaults(self):
        style = get_execution_event_style("nonexistent_type")
        assert style["icon"] == "mdi-circle"
        assert style["color"] == "grey"

    def test_known_type_returns_dict(self):
        # Test with a type we know exists in EXECUTION_EVENT_TYPES
        style = get_execution_event_style("start")
        assert "icon" in style
        assert "color" in style


# ── format_execution_event ───────────────────────────────

class TestFormatExecutionEvent:
    def test_adds_icon_and_color(self):
        event = {"event_type": "start", "timestamp": "2026-02-13T10:30:00Z"}
        result = format_execution_event(event)
        assert "icon" in result
        assert "color" in result
        assert result["event_type"] == "start"

    def test_formats_timestamp(self):
        event = {"event_type": "x", "timestamp": "2026-02-13T10:30:45.123Z"}
        result = format_execution_event(event)
        assert result["formatted_time"] == "2026-02-13 10:30:45"

    def test_missing_timestamp(self):
        event = {"event_type": "x"}
        result = format_execution_event(event)
        assert result["formatted_time"] == ""

    def test_preserves_original_fields(self):
        event = {"event_type": "x", "task_id": "T-1", "custom": "data"}
        result = format_execution_event(event)
        assert result["task_id"] == "T-1"
        assert result["custom"] == "data"
