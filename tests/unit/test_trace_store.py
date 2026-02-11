"""
Unit tests for Trace Store.

Per DOC-SIZE-01-v1: Tests for extracted trace_bar/trace_store.py module.
Tests: TraceStore (add, filter, clear, serialization, properties),
       get_initial_trace_state.
"""

import pytest

from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType
from agent.governance_ui.trace_bar.trace_store import TraceStore, get_initial_trace_state


@pytest.fixture
def store():
    return TraceStore()


def _api(msg="test", status=200):
    return TraceEvent(event_type=TraceType.API_CALL, message=msg, status_code=status)


def _error(msg="err"):
    return TraceEvent(event_type=TraceType.ERROR, message=msg, error_message=msg)


def _ui(msg="click"):
    return TraceEvent(event_type=TraceType.UI_ACTION, message=msg, action="click")


class TestTraceStoreAddEvent:
    """Tests for add_event()."""

    def test_add_single(self, store):
        store.add_event(_api())
        assert store.event_count == 1

    def test_add_multiple(self, store):
        for _ in range(5):
            store.add_event(_api())
        assert store.event_count == 5

    def test_respects_max_events(self):
        store = TraceStore(max_events=3)
        for i in range(5):
            store.add_event(_api(f"msg-{i}"))
        assert store.event_count == 3
        assert store.events[0].message == "msg-2"


class TestTraceStoreFilter:
    """Tests for get_filtered_events()."""

    def test_no_filter_returns_all(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.add_event(_ui())
        assert len(store.get_filtered_events()) == 3

    def test_filter_by_type(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.add_event(_api())
        store.filter_type = TraceType.API_CALL
        result = store.get_filtered_events()
        assert len(result) == 2
        assert all(e.event_type == TraceType.API_CALL for e in result)

    def test_filter_errors_only(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.filter_type = TraceType.ERROR
        result = store.get_filtered_events()
        assert len(result) == 1


class TestTraceStoreClear:
    """Tests for clear()."""

    def test_clear(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.clear()
        assert store.event_count == 0


class TestTraceStoreSerialization:
    """Tests for to_dict() and from_dict()."""

    def test_to_dict(self, store):
        store.add_event(_api("test"))
        d = store.to_dict()
        assert len(d["events"]) == 1
        assert d["max_events"] == 100
        assert d["filter_type"] is None

    def test_to_dict_with_filter(self, store):
        store.filter_type = TraceType.ERROR
        d = store.to_dict()
        assert d["filter_type"] == "error"

    def test_from_dict(self):
        data = {
            "events": [
                {"event_type": "api_call", "message": "test", "status_code": 200},
            ],
            "max_events": 50,
            "filter_type": "error",
        }
        store = TraceStore.from_dict(data)
        assert store.event_count == 1
        assert store.max_events == 50
        assert store.filter_type == TraceType.ERROR

    def test_from_dict_empty(self):
        store = TraceStore.from_dict({})
        assert store.event_count == 0
        assert store.max_events == 100

    def test_from_dict_invalid_filter(self):
        store = TraceStore.from_dict({"filter_type": "invalid"})
        assert store.filter_type is None


class TestTraceStoreProperties:
    """Tests for properties."""

    def test_error_count(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.add_event(_api(status=500))
        assert store.error_count == 2  # ERROR type + 500 status

    def test_api_call_count(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.add_event(_api())
        assert store.api_call_count == 2

    def test_last_event(self, store):
        store.add_event(_api("first"))
        store.add_event(_api("second"))
        assert store.last_event.message == "second"

    def test_last_event_empty(self, store):
        assert store.last_event is None


class TestTraceStoreSummary:
    """Tests for get_summary()."""

    def test_summary(self, store):
        store.add_event(_api())
        store.add_event(_error())
        store.add_event(_ui())
        summary = store.get_summary()
        assert summary["total"] == 3
        assert summary["errors"] == 1
        assert summary["api_calls"] == 1
        assert summary["ui_actions"] == 1
        assert summary["last_event"] is not None

    def test_summary_empty(self, store):
        summary = store.get_summary()
        assert summary["total"] == 0
        assert summary["last_event"] is None


class TestGetInitialTraceState:
    """Tests for get_initial_trace_state()."""

    def test_has_required_keys(self):
        state = get_initial_trace_state()
        assert "trace_bar_visible" in state
        assert "trace_bar_expanded" in state
        assert "trace_events" in state
        assert "trace_filter" in state
        assert "trace_summary" in state

    def test_defaults(self):
        state = get_initial_trace_state()
        assert state["trace_bar_visible"] is True
        assert state["trace_bar_expanded"] is False
        assert state["trace_events"] == []
        assert state["trace_filter"] is None
        assert state["trace_summary"]["total"] == 0
