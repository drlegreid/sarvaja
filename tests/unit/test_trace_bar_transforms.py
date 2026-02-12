"""
Unit tests for Trace Bar State Transform Functions.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/trace_bar/transforms.py module.
Tests: add_api_trace, add_ui_action_trace, add_error_trace, add_mcp_trace,
       _add_trace_event, clear_traces, toggle_trace_bar, set_trace_filter,
       get_filtered_traces.
"""

from types import SimpleNamespace

from agent.governance_ui.trace_bar.transforms import (
    MAX_TRACE_EVENTS,
    add_api_trace,
    add_ui_action_trace,
    add_error_trace,
    add_mcp_trace,
    clear_traces,
    toggle_trace_bar,
    set_trace_filter,
    get_filtered_traces,
)


def _make_state(**overrides):
    """Create a minimal mock state with trace defaults."""
    defaults = {
        "trace_events": [],
        "trace_events_count": 0,
        "trace_error_count": 0,
        "trace_api_count": 0,
        "trace_last_event": None,
        "trace_summary": {},
        "trace_bar_expanded": False,
        "trace_filter": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── add_api_trace ────────────────────────────────────────


class TestAddApiTrace:
    def test_basic(self):
        state = _make_state()
        add_api_trace(state, "/api/sessions", method="GET", status_code=200)
        assert state.trace_events_count == 1
        event = state.trace_events[0]
        assert event["event_type"] == "api_call"
        assert event["endpoint"] == "/api/sessions"
        assert event["method"] == "GET"
        assert event["status_code"] == 200

    def test_message_format(self):
        state = _make_state()
        add_api_trace(state, "/api/rules", method="POST", status_code=201)
        assert state.trace_events[0]["message"] == "POST /api/rules"

    def test_with_request_body(self):
        state = _make_state()
        body = {"name": "test"}
        add_api_trace(state, "/api/tasks", request_body=body)
        assert state.trace_events[0]["request_body"] == {"name": "test"}

    def test_truncates_large_body(self):
        state = _make_state()
        large_body = {"data": "x" * 6000}
        add_api_trace(state, "/api/data", request_body=large_body)
        rb = state.trace_events[0]["request_body"]
        assert rb["_truncated"] is True
        assert "_size" in rb
        assert "_preview" in rb

    def test_truncates_large_response(self):
        state = _make_state()
        large_resp = {"result": "y" * 6000}
        add_api_trace(state, "/api/data", response_body=large_resp)
        rb = state.trace_events[0]["response_body"]
        assert rb["_truncated"] is True

    def test_none_bodies_preserved(self):
        state = _make_state()
        add_api_trace(state, "/api/x")
        assert state.trace_events[0]["request_body"] is None
        assert state.trace_events[0]["response_body"] is None

    def test_duration_ms(self):
        state = _make_state()
        add_api_trace(state, "/api/slow", duration_ms=1500)
        assert state.trace_events[0]["duration_ms"] == 1500

    def test_request_headers(self):
        state = _make_state()
        headers = {"Authorization": "Bearer token"}
        add_api_trace(state, "/api/secure", request_headers=headers)
        assert state.trace_events[0]["request_headers"] == headers


# ── add_ui_action_trace ──────────────────────────────────


class TestAddUiActionTrace:
    def test_basic(self):
        state = _make_state()
        add_ui_action_trace(state, "click", "SessionTable")
        assert state.trace_events_count == 1
        event = state.trace_events[0]
        assert event["event_type"] == "ui_action"
        assert event["action"] == "click"
        assert event["component"] == "SessionTable"

    def test_message_format(self):
        state = _make_state()
        add_ui_action_trace(state, "navigate", "Sidebar", target="/rules")
        assert state.trace_events[0]["message"] == "navigate on Sidebar"

    def test_target_stored(self):
        state = _make_state()
        add_ui_action_trace(state, "input", "SearchBox", target="filter")
        assert state.trace_events[0]["target"] == "filter"


# ── add_error_trace ──────────────────────────────────────


class TestAddErrorTrace:
    def test_basic(self):
        state = _make_state()
        add_error_trace(state, "Connection refused")
        assert state.trace_events_count == 1
        event = state.trace_events[0]
        assert event["event_type"] == "error"
        assert event["message"] == "Connection refused"
        assert event["error_message"] == "Connection refused"

    def test_with_endpoint(self):
        state = _make_state()
        add_error_trace(state, "Not found", endpoint="/api/missing", status_code=404)
        event = state.trace_events[0]
        assert event["endpoint"] == "/api/missing"
        assert event["status_code"] == 404

    def test_increments_error_count(self):
        state = _make_state()
        add_error_trace(state, "error1")
        add_error_trace(state, "error2")
        assert state.trace_error_count == 2


# ── add_mcp_trace ────────────────────────────────────────


class TestAddMcpTrace:
    def test_success(self):
        state = _make_state()
        add_mcp_trace(state, "health_check", duration_ms=50, success=True)
        event = state.trace_events[0]
        assert event["event_type"] == "mcp_call"
        assert "health_check" in event["message"]
        assert "OK" in event["message"]
        assert event["status_code"] == 200

    def test_failure(self):
        state = _make_state()
        add_mcp_trace(state, "rule_create", success=False)
        event = state.trace_events[0]
        assert "ERROR" in event["message"]
        assert event["status_code"] == 500

    def test_duration(self):
        state = _make_state()
        add_mcp_trace(state, "task_list", duration_ms=250)
        assert state.trace_events[0]["duration_ms"] == 250


# ── _add_trace_event (internal, tested via public API) ───


class TestAddTraceEventInternal:
    def test_appends_events(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_api_trace(state, "/b")
        assert len(state.trace_events) == 2

    def test_max_events_cap(self):
        state = _make_state()
        for i in range(MAX_TRACE_EVENTS + 20):
            add_api_trace(state, f"/api/{i}")
        assert len(state.trace_events) == MAX_TRACE_EVENTS
        # Oldest events trimmed, newest kept
        last = state.trace_events[-1]
        assert f"/api/{MAX_TRACE_EVENTS + 19}" in last["message"]

    def test_summary_computed(self):
        state = _make_state()
        add_api_trace(state, "/api/sessions", status_code=200)
        add_ui_action_trace(state, "click", "Button")
        add_error_trace(state, "oops")
        summary = state.trace_summary
        assert summary["total"] == 3
        assert summary["api_calls"] == 1
        assert summary["ui_actions"] == 1
        assert summary["errors"] == 1

    def test_error_count_from_status_code(self):
        state = _make_state()
        add_api_trace(state, "/api/fail", status_code=500)
        assert state.trace_error_count == 1

    def test_error_count_from_type(self):
        state = _make_state()
        add_error_trace(state, "error without status code")
        assert state.trace_error_count == 1

    def test_api_count_tracked(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_api_trace(state, "/b")
        add_ui_action_trace(state, "click", "X")
        assert state.trace_api_count == 2

    def test_last_event_set(self):
        state = _make_state()
        add_api_trace(state, "/api/last")
        assert state.trace_last_event is not None
        assert "/api/last" in state.trace_last_event


# ── clear_traces ─────────────────────────────────────────


class TestClearTraces:
    def test_clears_all(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_error_trace(state, "err")
        clear_traces(state)
        assert state.trace_events == []
        assert state.trace_events_count == 0
        assert state.trace_error_count == 0
        assert state.trace_last_event is None

    def test_summary_reset(self):
        state = _make_state()
        add_api_trace(state, "/a")
        clear_traces(state)
        assert state.trace_summary["total"] == 0
        assert state.trace_summary["errors"] == 0
        assert state.trace_summary["api_calls"] == 0
        assert state.trace_summary["ui_actions"] == 0


# ── toggle_trace_bar ─────────────────────────────────────


class TestToggleTraceBar:
    def test_toggle_on(self):
        state = _make_state(trace_bar_expanded=False)
        toggle_trace_bar(state)
        assert state.trace_bar_expanded is True

    def test_toggle_off(self):
        state = _make_state(trace_bar_expanded=True)
        toggle_trace_bar(state)
        assert state.trace_bar_expanded is False

    def test_double_toggle(self):
        state = _make_state(trace_bar_expanded=False)
        toggle_trace_bar(state)
        toggle_trace_bar(state)
        assert state.trace_bar_expanded is False


# ── set_trace_filter ─────────────────────────────────────


class TestSetTraceFilter:
    def test_set_api_call(self):
        state = _make_state()
        set_trace_filter(state, "api_call")
        assert state.trace_filter == "api_call"

    def test_set_none(self):
        state = _make_state(trace_filter="error")
        set_trace_filter(state, None)
        assert state.trace_filter is None


# ── get_filtered_traces ──────────────────────────────────


class TestGetFilteredTraces:
    def test_no_filter_returns_all(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_ui_action_trace(state, "click", "X")
        add_error_trace(state, "err")
        result = get_filtered_traces(state)
        assert len(result) == 3

    def test_filter_api_calls(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_ui_action_trace(state, "click", "X")
        add_error_trace(state, "err")
        set_trace_filter(state, "api_call")
        result = get_filtered_traces(state)
        assert len(result) == 1
        assert result[0]["event_type"] == "api_call"

    def test_filter_ui_actions(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_ui_action_trace(state, "click", "X")
        set_trace_filter(state, "ui_action")
        result = get_filtered_traces(state)
        assert len(result) == 1
        assert result[0]["event_type"] == "ui_action"

    def test_filter_errors(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_error_trace(state, "err")
        set_trace_filter(state, "error")
        result = get_filtered_traces(state)
        assert len(result) == 1
        assert result[0]["event_type"] == "error"

    def test_filter_mcp_calls(self):
        state = _make_state()
        add_api_trace(state, "/a")
        add_mcp_trace(state, "tool_x")
        set_trace_filter(state, "mcp_call")
        result = get_filtered_traces(state)
        assert len(result) == 1
        assert result[0]["event_type"] == "mcp_call"

    def test_empty_events(self):
        state = _make_state()
        result = get_filtered_traces(state)
        assert result == []

    def test_filter_no_matches(self):
        state = _make_state()
        add_api_trace(state, "/a")
        set_trace_filter(state, "error")
        result = get_filtered_traces(state)
        assert result == []
