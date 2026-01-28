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
