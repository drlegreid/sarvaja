"""
Unit tests for Loader State Transform Functions.

Per DOC-SIZE-01-v1: Tests for extracted loaders/transforms.py module.
Tests: set_loading_start, set_loading_complete, set_loading_error,
       get_loader_state, update_progress, format_trace_status.
"""

import time
import pytest
from unittest.mock import MagicMock

from agent.governance_ui.loaders.transforms import (
    set_loading_start,
    set_loading_complete,
    set_loading_error,
    get_loader_state,
    update_progress,
    format_trace_status,
)
from agent.governance_ui.loaders.loader_state import LoaderState, APITrace


class MockState:
    """Mock Trame state object."""
    pass


class TestSetLoadingStart:
    """Tests for set_loading_start()."""

    def test_sets_loading_flag(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        assert state.rules_loading is True

    def test_sets_loader_dict(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules", "GET")
        loader = state.rules_loader
        assert isinstance(loader, dict)
        assert loader["is_loading"] is True
        assert loader["trace"]["endpoint"] == "/api/rules"
        assert loader["trace"]["method"] == "GET"
        assert loader["trace"]["status"] == "loading"

    def test_default_method_is_get(self):
        state = MockState()
        set_loading_start(state, "sessions", "/api/sessions")
        assert state.sessions_loader["trace"]["method"] == "GET"

    def test_post_method(self):
        state = MockState()
        set_loading_start(state, "tasks", "/api/tasks", "POST")
        assert state.tasks_loader["trace"]["method"] == "POST"

    def test_request_id_populated(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        assert state.rules_loader["trace"]["request_id"] != ""


class TestSetLoadingComplete:
    """Tests for set_loading_complete()."""

    def test_sets_loading_false(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_complete(state, "rules", status_code=200, items_count=10)
        assert state.rules_loading is False

    def test_success_status(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_complete(state, "rules", status_code=200)
        loader = state.rules_loader
        assert loader["has_error"] is False
        assert loader["trace"]["status"] == "success"
        assert loader["trace"]["status_code"] == 200

    def test_error_status_code(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_complete(state, "rules", status_code=500)
        loader = state.rules_loader
        assert loader["has_error"] is True
        assert loader["trace"]["status"] == "error"

    def test_items_count(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_complete(state, "rules", items_count=42)
        assert state.rules_loader["items_count"] == 42

    def test_duration_from_start_time(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        start = time.time() - 0.1  # 100ms ago
        set_loading_complete(state, "rules", start_time=start)
        duration = state.rules_loader["trace"]["duration_ms"]
        assert duration >= 90  # At least 90ms

    def test_preserves_endpoint_from_start(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules", "GET")
        set_loading_complete(state, "rules")
        assert state.rules_loader["trace"]["endpoint"] == "/api/rules"

    def test_no_prior_state(self):
        state = MockState()
        set_loading_complete(state, "rules", status_code=200, items_count=5)
        assert state.rules_loading is False
        assert state.rules_loader["items_count"] == 5


class TestSetLoadingError:
    """Tests for set_loading_error()."""

    def test_sets_error_state(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_error(state, "rules", "Connection refused")
        loader = state.rules_loader
        assert loader["has_error"] is True
        assert loader["error_message"] == "Connection refused"
        assert loader["is_loading"] is False
        assert state.rules_loading is False

    def test_error_trace_status(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_error(state, "rules", "Timeout", status_code=504)
        assert state.rules_loader["trace"]["status"] == "error"
        assert state.rules_loader["trace"]["status_code"] == 504

    def test_default_status_code_500(self):
        state = MockState()
        set_loading_error(state, "tasks", "Unknown error")
        assert state.tasks_loader["trace"]["status_code"] == 500

    def test_duration_from_start_time(self):
        state = MockState()
        start = time.time() - 0.05
        set_loading_error(state, "sessions", "error", start_time=start)
        duration = state.sessions_loader["trace"]["duration_ms"]
        assert duration >= 40


class TestGetLoaderState:
    """Tests for get_loader_state()."""

    def test_returns_loader_state(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        ls = get_loader_state(state, "rules")
        assert isinstance(ls, LoaderState)
        assert ls.is_loading is True

    def test_empty_state_returns_default(self):
        state = MockState()
        ls = get_loader_state(state, "nonexistent")
        assert isinstance(ls, LoaderState)
        assert ls.is_loading is False

    def test_after_complete(self):
        state = MockState()
        set_loading_start(state, "rules", "/api/rules")
        set_loading_complete(state, "rules", items_count=10)
        ls = get_loader_state(state, "rules")
        assert ls.is_loading is False
        assert ls.items_count == 10


class TestUpdateProgress:
    """Tests for update_progress()."""

    def test_sets_progress(self):
        state = MockState()
        set_loading_start(state, "tasks", "/api/tasks")
        update_progress(state, "tasks", 50, 5, 10)
        loader = state.tasks_loader
        assert loader["progress"]["progress_percent"] == 50
        assert loader["progress"]["items_loaded"] == 5
        assert loader["progress"]["total_items"] == 10

    def test_no_prior_state(self):
        state = MockState()
        update_progress(state, "rules", 100, 20)
        loader = state.rules_loader
        assert loader["progress"]["progress_percent"] == 100
        assert loader["progress"]["items_loaded"] == 20
        assert loader["progress"]["total_items"] is None


class TestFormatTraceStatus:
    """Tests for format_trace_status()."""

    def test_no_trace(self):
        ls = LoaderState()
        assert format_trace_status(ls) == ""

    def test_basic_trace(self):
        ls = LoaderState(trace=APITrace(
            endpoint="/api/rules", method="GET",
        ))
        result = format_trace_status(ls)
        assert "GET" in result
        assert "/api/rules" in result

    def test_with_duration(self):
        ls = LoaderState(trace=APITrace(
            endpoint="/api/rules", method="GET", duration_ms=150,
        ))
        result = format_trace_status(ls)
        assert "150ms" in result

    def test_with_success_status_code(self):
        ls = LoaderState(trace=APITrace(
            endpoint="/api/rules", method="GET",
            status_code=200, duration_ms=100,
        ))
        result = format_trace_status(ls)
        assert "200 OK" in result

    def test_with_error_status_code(self):
        ls = LoaderState(trace=APITrace(
            endpoint="/api/rules", method="GET",
            status_code=500, duration_ms=50,
        ))
        result = format_trace_status(ls)
        assert "500 ERROR" in result

    def test_zero_duration_excluded(self):
        ls = LoaderState(trace=APITrace(
            endpoint="/api/rules", method="GET", duration_ms=0,
        ))
        result = format_trace_status(ls)
        assert "ms" not in result
