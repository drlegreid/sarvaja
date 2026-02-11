"""
Unit Tests for Trace Event Query Param Parsing.

Per GAP-UI-TRACE-001: Trace bar request params visibility.
Tests the _parse_endpoint functionality for query parameter extraction.

Created: 2026-01-21
"""

import pytest
from agent.governance_ui.trace_bar.trace_event import TraceEvent, TraceType


class TestTraceEventQueryParams:
    """Tests for query parameter parsing."""

    def test_parse_endpoint_simple_path(self):
        """Endpoint without query params returns path only."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules",
            endpoint="/rules",
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] == "/rules"
        assert data["query_params"] is None

    def test_parse_endpoint_with_single_param(self):
        """Endpoint with single query param is parsed."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules?search=test",
            endpoint="/rules?search=test",
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] == "/rules"
        assert data["query_params"] == {"search": "test"}

    def test_parse_endpoint_with_multiple_params(self):
        """Endpoint with multiple query params is parsed."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules?search=test&limit=10&offset=0",
            endpoint="/rules?search=test&limit=10&offset=0",
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] == "/rules"
        assert data["query_params"]["search"] == "test"
        assert data["query_params"]["limit"] == "10"
        assert data["query_params"]["offset"] == "0"

    def test_parse_endpoint_with_repeated_param(self):
        """Endpoint with repeated param values returns list."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules?tag=a&tag=b&tag=c",
            endpoint="/rules?tag=a&tag=b&tag=c",
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] == "/rules"
        assert data["query_params"]["tag"] == ["a", "b", "c"]

    def test_parse_endpoint_none(self):
        """None endpoint returns None path and params."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="API call",
            endpoint=None,
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] is None
        assert data["query_params"] is None

    def test_parse_endpoint_empty_query(self):
        """Endpoint with empty query string returns no params."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules?",
            endpoint="/rules?",
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] == "/rules"
        assert data["query_params"] is None

    def test_parse_endpoint_with_encoded_value(self):
        """URL-encoded params are decoded."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules?search=hello%20world",
            endpoint="/rules?search=hello%20world",
            method="GET"
        )
        data = event.to_dict()

        assert data["path"] == "/rules"
        assert data["query_params"]["search"] == "hello world"


class TestTraceEventToDict:
    """Tests for to_dict serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict includes all trace event fields."""
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="GET /rules",
            endpoint="/rules?limit=10",
            method="GET",
            status_code=200,
            duration_ms=150,
            request_body={"filter": "active"},
            response_body={"rules": []},
            request_headers={"Authorization": "Bearer xxx"}
        )
        data = event.to_dict()

        assert data["event_type"] == "api_call"
        assert data["message"] == "GET /rules"
        assert data["path"] == "/rules"
        assert data["query_params"] == {"limit": "10"}
        assert data["method"] == "GET"
        assert data["status_code"] == 200
        assert data["duration_ms"] == 150
        assert data["request_body"] == {"filter": "active"}
        assert data["response_body"] == {"rules": []}
        assert data["request_headers"] == {"Authorization": "Bearer xxx"}

    def test_to_dict_ui_action_no_query_params(self):
        """UI action events have no query params."""
        event = TraceEvent(
            event_type=TraceType.UI_ACTION,
            message="click on button",
            action="click",
            component="submit-btn",
            target="form"
        )
        data = event.to_dict()

        assert data["event_type"] == "ui_action"
        assert data["path"] is None
        assert data["query_params"] is None
        assert data["action"] == "click"
        assert data["component"] == "submit-btn"


class TestTraceEventFromDict:
    """Tests for from_dict deserialization."""

    def test_basic_roundtrip(self):
        event = TraceEvent(
            event_type=TraceType.API_CALL,
            message="test",
            endpoint="/api/test",
            status_code=200,
            duration_ms=50,
        )
        d = event.to_dict()
        restored = TraceEvent.from_dict(d)
        assert restored.event_type == TraceType.API_CALL
        assert restored.message == "test"
        assert restored.status_code == 200

    def test_defaults(self):
        restored = TraceEvent.from_dict({})
        assert restored.event_type == TraceType.API_CALL
        assert restored.message == ""
        assert restored.method == "GET"

    def test_invalid_timestamp_uses_now(self):
        from datetime import datetime
        restored = TraceEvent.from_dict({"timestamp": "not-a-date"})
        assert isinstance(restored.timestamp, datetime)


class TestTraceEventFormatDisplay:
    """Tests for format_display()."""

    def test_api_call_ok(self):
        e = TraceEvent(
            event_type=TraceType.API_CALL, message="",
            endpoint="/api/rules", method="GET",
            status_code=200, duration_ms=42,
        )
        display = e.format_display()
        assert "GET" in display
        assert "42ms" in display
        assert "OK" in display

    def test_api_call_error(self):
        e = TraceEvent(
            event_type=TraceType.API_CALL, message="",
            endpoint="/api/bad", method="POST",
            status_code=500, duration_ms=100,
        )
        assert "ERR" in e.format_display()

    def test_ui_action(self):
        e = TraceEvent(
            event_type=TraceType.UI_ACTION, message="",
            action="click", component="RuleCard",
        )
        display = e.format_display()
        assert "UI:" in display
        assert "click" in display

    def test_error(self):
        e = TraceEvent(
            event_type=TraceType.ERROR, message="generic",
            error_message="Connection refused",
        )
        assert "ERROR:" in e.format_display()
        assert "Connection refused" in e.format_display()

    def test_mcp_call(self):
        e = TraceEvent(
            event_type=TraceType.MCP_CALL, message="health_check",
            duration_ms=150,
        )
        display = e.format_display()
        assert "MCP:" in display
        assert "150ms" in display


class TestTraceEventProperties:
    """Tests for is_error and css_class properties."""

    def test_error_type_is_error(self):
        e = TraceEvent(event_type=TraceType.ERROR, message="err")
        assert e.is_error is True

    def test_500_status_is_error(self):
        e = TraceEvent(event_type=TraceType.API_CALL, message="", status_code=500)
        assert e.is_error is True

    def test_200_not_error(self):
        e = TraceEvent(event_type=TraceType.API_CALL, message="", status_code=200)
        assert e.is_error is False

    def test_css_class_error(self):
        e = TraceEvent(event_type=TraceType.ERROR, message="")
        assert e.css_class == "trace-error"

    def test_css_class_api(self):
        e = TraceEvent(event_type=TraceType.API_CALL, message="", status_code=200)
        assert e.css_class == "trace-api-call"

    def test_css_class_mcp(self):
        e = TraceEvent(event_type=TraceType.MCP_CALL, message="")
        assert e.css_class == "trace-mcp-call"
