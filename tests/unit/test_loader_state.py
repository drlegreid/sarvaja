"""
Unit tests for Loader State Data Classes.

Per DOC-SIZE-01-v1: Tests for extracted loaders/loader_state.py module.
Tests: APITrace, ProgressInfo, LoaderState, get_initial_loader_states.
"""

import pytest
from datetime import datetime

from agent.governance_ui.loaders.loader_state import (
    APITrace,
    ProgressInfo,
    LoaderState,
    COMPONENT_LOADERS,
    get_initial_loader_states,
)


class TestAPITrace:
    """Tests for APITrace dataclass."""

    def test_defaults(self):
        t = APITrace()
        assert t.endpoint == ""
        assert t.method == "GET"
        assert t.status == "pending"
        assert t.status_code is None
        assert t.duration_ms == 0
        assert t.request_id != ""

    def test_to_dict(self):
        now = datetime.now()
        t = APITrace(
            endpoint="/api/rules",
            method="GET",
            status="success",
            status_code=200,
            start_time=now,
            end_time=now,
            duration_ms=42,
        )
        d = t.to_dict()
        assert d["endpoint"] == "/api/rules"
        assert d["status_code"] == 200
        assert d["duration_ms"] == 42
        assert d["start_time"] is not None

    def test_to_dict_no_times(self):
        t = APITrace()
        d = t.to_dict()
        assert d["start_time"] is None
        assert d["end_time"] is None


class TestProgressInfo:
    """Tests for ProgressInfo dataclass."""

    def test_defaults(self):
        p = ProgressInfo()
        assert p.progress_percent == 0
        assert p.items_loaded == 0
        assert p.total_items is None
        assert p.current_page == 1

    def test_to_dict(self):
        p = ProgressInfo(
            progress_percent=50,
            items_loaded=10,
            total_items=20,
            current_page=2,
            total_pages=5,
        )
        d = p.to_dict()
        assert d["progress_percent"] == 50
        assert d["total_pages"] == 5


class TestLoaderState:
    """Tests for LoaderState dataclass."""

    def test_defaults(self):
        ls = LoaderState()
        assert ls.is_loading is False
        assert ls.has_error is False
        assert ls.trace is None
        assert ls.progress is None

    def test_to_dict(self):
        ls = LoaderState(
            is_loading=True,
            trace=APITrace(endpoint="/api/rules"),
            items_count=42,
        )
        d = ls.to_dict()
        assert d["is_loading"] is True
        assert d["trace"]["endpoint"] == "/api/rules"
        assert d["items_count"] == 42

    def test_to_dict_no_trace(self):
        ls = LoaderState()
        d = ls.to_dict()
        assert d["trace"] is None
        assert d["progress"] is None

    def test_from_dict_basic(self):
        data = {
            "is_loading": True,
            "has_error": False,
            "error_message": "",
            "items_count": 10,
        }
        ls = LoaderState.from_dict(data)
        assert ls.is_loading is True
        assert ls.items_count == 10

    def test_from_dict_with_trace(self):
        data = {
            "trace": {
                "endpoint": "/api/rules",
                "method": "GET",
                "status": "success",
                "status_code": 200,
                "request_id": "abc123",
            },
        }
        ls = LoaderState.from_dict(data)
        assert ls.trace is not None
        assert ls.trace.endpoint == "/api/rules"
        assert ls.trace.status_code == 200

    def test_from_dict_with_progress(self):
        data = {
            "progress": {
                "progress_percent": 75,
                "items_loaded": 15,
                "total_items": 20,
            },
        }
        ls = LoaderState.from_dict(data)
        assert ls.progress is not None
        assert ls.progress.progress_percent == 75
        assert ls.progress.items_loaded == 15

    def test_from_dict_empty(self):
        ls = LoaderState.from_dict({})
        assert ls.is_loading is False
        assert ls.trace is None
        assert ls.progress is None

    def test_roundtrip(self):
        ls = LoaderState(
            is_loading=True,
            has_error=True,
            error_message="timeout",
            trace=APITrace(endpoint="/api/test", method="POST"),
            items_count=5,
        )
        d = ls.to_dict()
        restored = LoaderState.from_dict(d)
        assert restored.is_loading is True
        assert restored.has_error is True
        assert restored.error_message == "timeout"
        assert restored.trace.endpoint == "/api/test"
        assert restored.trace.method == "POST"


class TestComponentLoaders:
    """Tests for COMPONENT_LOADERS and get_initial_loader_states."""

    def test_has_required_components(self):
        assert "rules" in COMPONENT_LOADERS
        assert "sessions" in COMPONENT_LOADERS
        assert "tasks" in COMPONENT_LOADERS
        assert "agents" in COMPONENT_LOADERS

    def test_initial_states_structure(self):
        states = get_initial_loader_states()
        for comp in COMPONENT_LOADERS:
            assert f"{comp}_loader" in states
            assert f"{comp}_loading" in states
            assert states[f"{comp}_loading"] is False

    def test_initial_loader_not_loading(self):
        states = get_initial_loader_states()
        for comp in COMPONENT_LOADERS:
            loader = states[f"{comp}_loader"]
            assert loader["is_loading"] is False
            assert loader["has_error"] is False
