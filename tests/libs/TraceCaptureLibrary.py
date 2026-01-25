"""
RF-004: Robot Framework Library for Trace Capture.

Wraps tests/evidence/trace_capture.py for Robot Framework tests.
Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TraceCaptureLibrary:
    """Robot Framework library for Trace Capture testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._capture = None
        self._record = None

    # =========================================================================
    # TraceRecord Tests
    # =========================================================================

    def create_http_trace_record(self) -> Dict[str, Any]:
        """Create an HTTP trace record."""
        from tests.evidence.trace_capture import TraceRecord

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
        return {
            "trace_type": trace.trace_type,
            "method": trace.method,
            "status_code": trace.status_code,
            "duration_ms": trace.duration_ms
        }

    def create_mcp_trace_record(self) -> Dict[str, Any]:
        """Create an MCP trace record."""
        from tests.evidence.trace_capture import TraceRecord

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
        return {
            "trace_type": trace.trace_type,
            "tool_name": trace.tool_name,
            "arguments": trace.arguments
        }

    def trace_record_to_dict(self) -> Dict[str, Any]:
        """Create trace record and convert to dict."""
        from tests.evidence.trace_capture import TraceRecord

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
        return trace.to_dict()

    def trace_record_truncation(self) -> Dict[str, Any]:
        """Test that large values are truncated."""
        from tests.evidence.trace_capture import TraceRecord

        large_response = "x" * 5000  # Larger than 2000 char limit

        trace = TraceRecord(
            trace_id="TR-12345678",
            correlation_id="TEST-20260121-ABC123",
            timestamp="2026-01-21T10:00:00",
            trace_type="http",
            response_body=large_response,
        )

        data = trace.to_dict()
        return {
            "is_truncated": "truncated" in str(data.get("response_body", "")),
            "length_under_5000": len(str(data.get("response_body", ""))) < 5000
        }

    # =========================================================================
    # TraceCapture Tests
    # =========================================================================

    def create_trace_capture(self, test_id: str = "test_example") -> bool:
        """Create TraceCapture instance."""
        from tests.evidence.trace_capture import TraceCapture

        self._capture = TraceCapture(test_id=test_id)
        return self._capture is not None

    def get_capture_info(self) -> Dict[str, Any]:
        """Get trace capture info."""
        return {
            "test_id": self._capture.test_id,
            "correlation_id": self._capture.correlation_id,
            "traces_count": len(self._capture.traces),
            "correlation_starts_with_test": self._capture.correlation_id.startswith("TEST-")
        }

    def correlation_id_format_valid(self) -> bool:
        """Check correlation ID format. Per RD-DEBUG-AUDIT."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        parts = capture.correlation_id.split("-")
        return parts[0] == "TEST" and len(parts) >= 3

    def custom_correlation_id(self, custom_id: str) -> bool:
        """Test using custom correlation ID."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example", correlation_id=custom_id)
        return capture.correlation_id == custom_id

    def headers_property(self) -> Dict[str, Any]:
        """Test trace headers for HTTP injection."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        headers = capture.headers
        return {
            "has_correlation_id": "X-Correlation-ID" in headers,
            "has_test_id": "X-Test-ID" in headers,
            "has_trace_enabled": "X-Trace-Enabled" in headers,
            "test_id_value": headers.get("X-Test-ID")
        }

    def start_end_lifecycle(self) -> Dict[str, Any]:
        """Test start/end lifecycle."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")

        before_start = {
            "start_time": capture.start_time,
            "active": capture._active
        }

        capture.start()
        after_start = {
            "start_time_set": capture.start_time is not None,
            "active": capture._active
        }

        capture.end()
        after_end = {
            "end_time_set": capture.end_time is not None,
            "active": capture._active
        }

        return {
            "before_start": before_start,
            "after_start": after_start,
            "after_end": after_end
        }

    def record_http_trace(self) -> Dict[str, Any]:
        """Test recording HTTP trace."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        capture.start()

        trace = capture.record_http(
            method="GET",
            url="/api/rules",
            status_code=200,
            duration_ms=100.0,
        )

        return {
            "traces_count": len(capture.traces),
            "trace_type": trace.trace_type,
            "method": trace.method,
            "correlation_matches": trace.correlation_id == capture.correlation_id
        }

    def record_mcp_trace(self) -> Dict[str, Any]:
        """Test recording MCP trace."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        capture.start()

        trace = capture.record_mcp(
            tool_name="rules_query",
            arguments={"status": "ACTIVE"},
            result='{"count": 10}',
            duration_ms=200.0,
        )

        return {
            "traces_count": len(capture.traces),
            "trace_type": trace.trace_type,
            "tool_name": trace.tool_name
        }

    def get_traces_as_dicts(self) -> Dict[str, Any]:
        """Test getting all traces as dictionaries."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        capture.start()

        capture.record_http(method="GET", url="/api/rules", status_code=200)
        capture.record_mcp(tool_name="health_check", result="ok")

        traces = capture.get_traces()

        return {
            "count": len(traces),
            "all_dicts": all(isinstance(t, dict) for t in traces),
            "first_type": traces[0]["trace_type"] if traces else None,
            "second_type": traces[1]["trace_type"] if len(traces) > 1 else None
        }

    def get_summary(self) -> Dict[str, Any]:
        """Test trace capture summary."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        capture.start()

        capture.record_http(method="GET", url="/api/rules", status_code=200, duration_ms=100)
        capture.record_http(method="POST", url="/api/rules", status_code=201, duration_ms=150)
        capture.record_http(method="GET", url="/api/rules/1", status_code=404, duration_ms=50)
        capture.record_mcp(tool_name="health_check", duration_ms=25)

        capture.end()
        return capture.get_summary()

    def capture_context_manager(self) -> Dict[str, Any]:
        """Test context manager for trace capture."""
        from tests.evidence.trace_capture import TraceCapture

        capture = TraceCapture(test_id="test_example")
        active_in_context = False

        with capture.capture_context() as ctx:
            active_in_context = ctx._active
            ctx.record_http(method="GET", url="/api/test", status_code=200)

        return {
            "active_in_context": active_in_context,
            "active_after_context": capture._active,
            "traces_count": len(capture.traces)
        }

    # =========================================================================
    # RequestsTraceAdapter Tests
    # =========================================================================

    def adapter_initialization(self) -> bool:
        """Test adapter initialization."""
        from tests.evidence.trace_capture import TraceCapture, RequestsTraceAdapter

        capture = TraceCapture(test_id="test_example")
        adapter = RequestsTraceAdapter(capture)

        return adapter.trace_capture == capture

    def adapter_patches_requests(self) -> Dict[str, Any]:
        """Test that adapter patches requests library."""
        import requests
        from tests.evidence.trace_capture import TraceCapture, RequestsTraceAdapter

        capture = TraceCapture(test_id="test_example")
        adapter = RequestsTraceAdapter(capture)
        capture.start()

        original_request = requests.Session.request

        with adapter.patch():
            patched_request = requests.Session.request
            is_patched = patched_request != original_request

        is_restored = requests.Session.request == original_request

        return {
            "is_patched": is_patched,
            "is_restored": is_restored
        }

    # =========================================================================
    # Link Traces to Evidence Tests
    # =========================================================================

    def link_traces_to_evidence(self) -> Dict[str, Any]:
        """Test linking traces to evidence record."""
        from tests.evidence.trace_capture import TraceCapture, link_traces_to_evidence

        evidence = {
            "test_id": "test_example",
            "name": "test_example",
            "status": "passed",
            "duration_ms": 500,
        }

        capture = TraceCapture(test_id="test_example")
        capture.start()
        capture.record_http(method="GET", url="/api/rules", status_code=200)
        capture.end()

        result = link_traces_to_evidence(evidence, capture)

        return {
            "has_traces": "traces" in result,
            "has_trace_summary": "trace_summary" in result,
            "has_correlation_id": "correlation_id" in result,
            "traces_count": len(result.get("traces", [])),
            "correlation_matches": result.get("correlation_id") == capture.correlation_id
        }
