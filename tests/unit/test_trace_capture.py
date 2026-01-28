"""
Unit tests for trace capture module.

Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level.

Tests:
- TraceCapture initialization and correlation ID generation
- HTTP trace recording
- MCP trace recording
- Trace summary generation
- RequestsTraceAdapter patching
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from tests.evidence.trace_capture import (
    TraceCapture,
    TraceRecord,
    RequestsTraceAdapter,
    link_traces_to_evidence,
)


# Local fixture for this test module
@pytest.fixture
def trace_capture(request):
    """Fixture for HTTP/MCP trace capture."""
    test_id = request.node.nodeid
    capture = TraceCapture(test_id=test_id)
    yield capture


class TestTraceRecord:
    """Tests for TraceRecord dataclass."""

    def test_http_trace_record_creation(self):
        """Test creating an HTTP trace record."""
        trace = TraceRecord(
            trace_id="TR-12345678",
            correlation_id="TEST-20260121-ABC123",
            timestamp="2026-01-21T10:00:00",
            trace_type="http",
            method="GET",
            url="/api/rules",
            status_code=200,
            duration_ms=150.5,
        )

        assert trace.trace_type == "http"
        assert trace.method == "GET"
        assert trace.status_code == 200
        assert trace.duration_ms == 150.5

    def test_mcp_trace_record_creation(self):
        """Test creating an MCP trace record."""
        trace = TraceRecord(
            trace_id="TR-87654321",
            correlation_id="TEST-20260121-DEF456",
            timestamp="2026-01-21T10:01:00",
            trace_type="mcp",
            tool_name="rules_query",
            arguments={"status": "ACTIVE"},
            result='{"rules": []}',
            duration_ms=250.0,
        )

        assert trace.trace_type == "mcp"
        assert trace.tool_name == "rules_query"
        assert trace.arguments == {"status": "ACTIVE"}

    def test_trace_record_to_dict(self):
        """Test converting trace record to dictionary."""
        trace = TraceRecord(
            trace_id="TR-12345678",
            correlation_id="TEST-20260121-ABC123",
            timestamp="2026-01-21T10:00:00",
            trace_type="http",
            method="POST",
            url="/api/rules",
            status_code=201,
            request_body={"name": "Test Rule"},
            response_body={"rule_id": "RULE-001"},
            duration_ms=100.0,
        )

        data = trace.to_dict()

        assert data["trace_id"] == "TR-12345678"
        assert data["correlation_id"] == "TEST-20260121-ABC123"
        assert data["trace_type"] == "http"
        assert data["method"] == "POST"
        assert data["status_code"] == 201
        assert data["request_body"] == {"name": "Test Rule"}

    def test_trace_record_truncation(self):
        """Test that large values are truncated."""
        large_response = "x" * 5000  # Larger than 2000 char limit

        trace = TraceRecord(
            trace_id="TR-12345678",
            correlation_id="TEST-20260121-ABC123",
            timestamp="2026-01-21T10:00:00",
            trace_type="http",
            response_body=large_response,
        )

        data = trace.to_dict()
        assert "truncated" in data["response_body"]
        assert len(data["response_body"]) < 5000


class TestTraceCapture:
    """Tests for TraceCapture class."""

    def test_trace_capture_initialization(self):
        """Test TraceCapture initialization."""
        capture = TraceCapture(test_id="tests/test_example.py::test_func")

        assert capture.test_id == "tests/test_example.py::test_func"
        assert capture.correlation_id.startswith("TEST-")
        assert len(capture.traces) == 0

    def test_correlation_id_format(self):
        """Test correlation ID format. Per RD-DEBUG-AUDIT."""
        capture = TraceCapture(test_id="test_example")

        # Format: TEST-YYYYMMDD-HHMMSS-XXXXXXXX
        parts = capture.correlation_id.split("-")
        assert parts[0] == "TEST"
        assert len(parts) >= 3

    def test_custom_correlation_id(self):
        """Test using custom correlation ID."""
        custom_id = "CUSTOM-CORR-12345"
        capture = TraceCapture(test_id="test_example", correlation_id=custom_id)

        assert capture.correlation_id == custom_id

    def test_headers_property(self):
        """Test trace headers for HTTP injection."""
        capture = TraceCapture(test_id="test_example")
        headers = capture.headers

        assert "X-Correlation-ID" in headers
        assert "X-Test-ID" in headers
        assert "X-Trace-Enabled" in headers
        assert headers["X-Test-ID"] == "test_example"

    def test_start_end_lifecycle(self):
        """Test start/end lifecycle."""
        capture = TraceCapture(test_id="test_example")

        assert capture.start_time is None
        assert capture._active is False

        capture.start()
        assert capture.start_time is not None
        assert capture._active is True

        capture.end()
        assert capture.end_time is not None
        assert capture._active is False

    def test_record_http_trace(self):
        """Test recording HTTP trace."""
        capture = TraceCapture(test_id="test_example")
        capture.start()

        trace = capture.record_http(
            method="GET",
            url="/api/rules",
            status_code=200,
            duration_ms=100.0,
        )

        assert len(capture.traces) == 1
        assert trace.trace_type == "http"
        assert trace.method == "GET"
        assert trace.correlation_id == capture.correlation_id

    def test_record_mcp_trace(self):
        """Test recording MCP trace."""
        capture = TraceCapture(test_id="test_example")
        capture.start()

        trace = capture.record_mcp(
            tool_name="rules_query",
            arguments={"status": "ACTIVE"},
            result='{"count": 10}',
            duration_ms=200.0,
        )

        assert len(capture.traces) == 1
        assert trace.trace_type == "mcp"
        assert trace.tool_name == "rules_query"

    def test_get_traces(self):
        """Test getting all traces as dictionaries."""
        capture = TraceCapture(test_id="test_example")
        capture.start()

        capture.record_http(method="GET", url="/api/rules", status_code=200)
        capture.record_mcp(tool_name="health_check", result="ok")

        traces = capture.get_traces()

        assert len(traces) == 2
        assert all(isinstance(t, dict) for t in traces)
        assert traces[0]["trace_type"] == "http"
        assert traces[1]["trace_type"] == "mcp"

    def test_get_summary(self):
        """Test trace capture summary."""
        capture = TraceCapture(test_id="test_example")
        capture.start()

        capture.record_http(method="GET", url="/api/rules", status_code=200, duration_ms=100)
        capture.record_http(method="POST", url="/api/rules", status_code=201, duration_ms=150)
        capture.record_http(method="GET", url="/api/rules/1", status_code=404, duration_ms=50)
        capture.record_mcp(tool_name="health_check", duration_ms=25)

        capture.end()
        summary = capture.get_summary()

        assert summary["test_id"] == "test_example"
        assert summary["total_traces"] == 4
        assert summary["http_traces"] == 3
        assert summary["mcp_traces"] == 1
        assert summary["total_duration_ms"] == 325
        assert summary["status_codes"]["2xx"] == 2
        assert summary["status_codes"]["4xx"] == 1

    def test_capture_context_manager(self):
        """Test context manager for trace capture."""
        capture = TraceCapture(test_id="test_example")

        with capture.capture_context() as ctx:
            assert ctx._active is True
            ctx.record_http(method="GET", url="/api/test", status_code=200)

        assert capture._active is False
        assert len(capture.traces) == 1


class TestRequestsTraceAdapter:
    """Tests for RequestsTraceAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        capture = TraceCapture(test_id="test_example")
        adapter = RequestsTraceAdapter(capture)

        assert adapter.trace_capture == capture

    def test_adapter_patches_requests(self):
        """Test that adapter patches requests library."""
        import requests

        capture = TraceCapture(test_id="test_example")
        adapter = RequestsTraceAdapter(capture)
        capture.start()

        # Save original request method
        original_request = requests.Session.request

        with adapter.patch():
            # After patch, Session.request should be our traced version
            patched_request = requests.Session.request
            assert patched_request != original_request

        # After context, original should be restored
        assert requests.Session.request == original_request


class TestLinkTracesToEvidence:
    """Tests for linking traces to evidence."""

    def test_link_traces_to_evidence(self):
        """Test linking traces to evidence record."""
        # Create evidence record
        evidence = {
            "test_id": "test_example",
            "name": "test_example",
            "status": "passed",
            "duration_ms": 500,
        }

        # Create trace capture with some traces
        capture = TraceCapture(test_id="test_example")
        capture.start()
        capture.record_http(method="GET", url="/api/rules", status_code=200)
        capture.end()

        # Link traces
        result = link_traces_to_evidence(evidence, capture)

        assert "traces" in result
        assert "trace_summary" in result
        assert "correlation_id" in result
        assert len(result["traces"]) == 1
        assert result["correlation_id"] == capture.correlation_id


# Fixture-based tests


class TestTraceFixtures:
    """Tests for pytest fixtures."""

    def test_trace_capture_fixture_available(self, trace_capture):
        """Test that trace_capture fixture is available."""
        assert isinstance(trace_capture, TraceCapture)

    def test_fixture_creates_correlation_id(self, trace_capture):
        """Test fixture creates correlation ID."""
        assert trace_capture.correlation_id is not None
        assert trace_capture.correlation_id.startswith("TEST-")

    def test_fixture_manual_recording(self, trace_capture):
        """Test manual trace recording with fixture."""
        trace_capture.start()
        trace_capture.record_http(method="GET", url="/api/test", status_code=200)
        trace_capture.end()

        assert len(trace_capture.traces) == 1
