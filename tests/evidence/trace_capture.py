"""
Test Trace Capture - HTTP and MCP trace collection during test execution.

Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level.
Per RD-DEBUG-AUDIT: Correlation ID injection for cross-request tracing.

Usage:
    def test_rule_creation(trace_capture):
        trace_capture.start()

        response = requests.post("/api/rules", json=rule_data,
                                 headers=trace_capture.headers)

        trace_capture.end()
        traces = trace_capture.get_traces()
        # traces contain all HTTP calls with correlation IDs

Created: 2026-01-21
"""

import json
import time
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import patch

import pytest


@dataclass
class TraceRecord:
    """Single trace record for HTTP or MCP call."""

    trace_id: str
    correlation_id: str
    timestamp: str
    trace_type: str  # http, mcp, db

    # HTTP fields
    method: Optional[str] = None
    url: Optional[str] = None
    status_code: Optional[int] = None
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Any] = None
    response_body: Optional[Any] = None
    duration_ms: float = 0.0

    # MCP fields
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[str] = None

    # Error fields
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "trace_type": self.trace_type,
            "method": self.method,
            "url": self.url,
            "status_code": self.status_code,
            "request_headers": self.request_headers,
            "request_body": self._truncate(self.request_body),
            "response_body": self._truncate(self.response_body),
            "duration_ms": self.duration_ms,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self._truncate(self.result, 1000),
            "error": self.error,
        }

    def _truncate(self, value: Any, max_len: int = 2000) -> Any:
        """Truncate large values for storage."""
        if value is None:
            return None
        if isinstance(value, str) and len(value) > max_len:
            return value[:max_len] + f"... (truncated {len(value) - max_len} chars)"
        if isinstance(value, dict):
            serialized = json.dumps(value)
            if len(serialized) > max_len:
                return {"_truncated": True, "_preview": serialized[:500]}
        return value


class TraceCapture:
    """
    Captures HTTP and MCP traces during test execution.

    Provides correlation ID injection and trace collection for test evidence.
    """

    def __init__(self, test_id: str, correlation_id: Optional[str] = None):
        """Initialize trace capture for a test.

        Args:
            test_id: Test identifier (pytest nodeid)
            correlation_id: Optional correlation ID (auto-generated if not provided)
        """
        self.test_id = test_id
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.traces: List[TraceRecord] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._active = False
        self._original_request = None
        self._lock = threading.Lock()

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for this test."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique = uuid.uuid4().hex[:8].upper()
        return f"TEST-{timestamp}-{unique}"

    @property
    def headers(self) -> Dict[str, str]:
        """Get headers to inject into HTTP requests for tracing."""
        return {
            "X-Correlation-ID": self.correlation_id,
            "X-Test-ID": self.test_id,
            "X-Trace-Enabled": "true",
        }

    def start(self) -> None:
        """Start trace capture."""
        self.start_time = datetime.now()
        self._active = True
        self.traces = []

    def end(self) -> None:
        """End trace capture."""
        self.end_time = datetime.now()
        self._active = False

    def record_http(
        self,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        request_headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Any] = None,
        response_body: Optional[Any] = None,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> TraceRecord:
        """Record an HTTP trace."""
        trace = TraceRecord(
            trace_id=f"TR-{uuid.uuid4().hex[:8].upper()}",
            correlation_id=self.correlation_id,
            timestamp=datetime.now().isoformat(),
            trace_type="http",
            method=method,
            url=url,
            status_code=status_code,
            request_headers=request_headers,
            request_body=request_body,
            response_body=response_body,
            duration_ms=duration_ms,
            error=error,
        )
        with self._lock:
            self.traces.append(trace)
        return trace

    def record_mcp(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> TraceRecord:
        """Record an MCP tool call trace."""
        trace = TraceRecord(
            trace_id=f"TR-{uuid.uuid4().hex[:8].upper()}",
            correlation_id=self.correlation_id,
            timestamp=datetime.now().isoformat(),
            trace_type="mcp",
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            duration_ms=duration_ms,
            error=error,
        )
        with self._lock:
            self.traces.append(trace)
        return trace

    def get_traces(self) -> List[Dict[str, Any]]:
        """Get all captured traces as dictionaries."""
        return [trace.to_dict() for trace in self.traces]

    def get_summary(self) -> Dict[str, Any]:
        """Get trace capture summary."""
        http_traces = [t for t in self.traces if t.trace_type == "http"]
        mcp_traces = [t for t in self.traces if t.trace_type == "mcp"]
        errors = [t for t in self.traces if t.error]

        total_duration = sum(t.duration_ms for t in self.traces)

        return {
            "test_id": self.test_id,
            "correlation_id": self.correlation_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_traces": len(self.traces),
            "http_traces": len(http_traces),
            "mcp_traces": len(mcp_traces),
            "errors": len(errors),
            "total_duration_ms": total_duration,
            "status_codes": self._count_status_codes(http_traces),
        }

    def _count_status_codes(self, http_traces: List[TraceRecord]) -> Dict[str, int]:
        """Count HTTP status codes."""
        counts: Dict[str, int] = {}
        for trace in http_traces:
            if trace.status_code:
                key = f"{trace.status_code // 100}xx"
                counts[key] = counts.get(key, 0) + 1
        return counts

    @contextmanager
    def capture_context(self):
        """Context manager for trace capture."""
        self.start()
        try:
            yield self
        finally:
            self.end()


class RequestsTraceAdapter:
    """
    Adapter for capturing requests library HTTP calls.

    Usage:
        adapter = RequestsTraceAdapter(trace_capture)
        with adapter.patch():
            response = requests.get("/api/rules")
            # Automatically captured!
    """

    def __init__(self, trace_capture: TraceCapture):
        """Initialize adapter with trace capture instance."""
        self.trace_capture = trace_capture
        self._original_request = None

    @contextmanager
    def patch(self):
        """Patch requests library to capture all HTTP calls."""
        try:
            import requests
        except ImportError:
            yield
            return

        original_request = requests.Session.request

        def traced_request(session, method, url, **kwargs):
            # Inject correlation headers
            headers = kwargs.get("headers", {}) or {}
            headers.update(self.trace_capture.headers)
            kwargs["headers"] = headers

            # Capture request body
            request_body = kwargs.get("json") or kwargs.get("data")

            start_time = time.time()
            error = None
            response = None

            try:
                response = original_request(session, method, url, **kwargs)
                return response
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Parse response body if available
                response_body = None
                status_code = None
                if response is not None:
                    status_code = response.status_code
                    try:
                        response_body = response.json()
                    except (ValueError, AttributeError):
                        response_body = (
                            response.text[:500] if hasattr(response, "text") else None
                        )

                self.trace_capture.record_http(
                    method=method,
                    url=url,
                    status_code=status_code,
                    request_headers=dict(headers),
                    request_body=request_body,
                    response_body=response_body,
                    duration_ms=duration_ms,
                    error=error,
                )

        requests.Session.request = traced_request
        try:
            yield
        finally:
            requests.Session.request = original_request


# Pytest fixtures for trace capture


@pytest.fixture
def trace_capture(request):
    """
    Pytest fixture for HTTP/MCP trace capture.

    Usage:
        def test_api_call(trace_capture):
            with trace_capture.capture_context():
                response = requests.get("/api/rules",
                                        headers=trace_capture.headers)

            assert len(trace_capture.traces) > 0
            summary = trace_capture.get_summary()
            assert summary["errors"] == 0
    """
    test_id = request.node.nodeid
    capture = TraceCapture(test_id=test_id)
    yield capture


@pytest.fixture
def auto_trace_capture(request, trace_capture):
    """
    Pytest fixture that automatically captures all requests library calls.

    Usage:
        def test_api_call(auto_trace_capture):
            # No need to pass headers - automatically injected!
            response = requests.get("/api/rules")

            summary = auto_trace_capture.get_summary()
            assert summary["http_traces"] > 0
    """
    adapter = RequestsTraceAdapter(trace_capture)
    with adapter.patch():
        trace_capture.start()
        yield trace_capture
    trace_capture.end()


# Integration with BDD Evidence Collector


def link_traces_to_evidence(
    evidence_record: Dict[str, Any],
    trace_capture: TraceCapture,
) -> Dict[str, Any]:
    """
    Link trace data to test evidence record.

    Per TEST-002: Evidence collection at trace level.

    Args:
        evidence_record: Evidence record from BDDEvidenceCollector
        trace_capture: TraceCapture instance with recorded traces

    Returns:
        Enhanced evidence record with trace data
    """
    evidence_record["traces"] = trace_capture.get_traces()
    evidence_record["trace_summary"] = trace_capture.get_summary()
    evidence_record["correlation_id"] = trace_capture.correlation_id
    return evidence_record
