"""
Unit tests for trace minimizer module.

Per RD-TESTING-STRATEGY TEST-003: Debug workflow trace minimization.

Tests:
- Error classification
- Message extraction
- Stack frame filtering
- Token estimation
- Trace minimization
"""

import pytest

from tests.evidence.trace_minimizer import (
    TraceMinimizer,
    MinimizedTrace,
    MinimizedFrame,
    ErrorCategory,
    minimize_for_llm,
    estimate_compression,
)


# Sample tracebacks for testing
SAMPLE_ASSERTION_ERROR = """
def test_rule_creation():
>       assert rule.status == 'ACTIVE'
E       AssertionError: assert 'INACTIVE' == 'ACTIVE'
E         + where 'INACTIVE' = <Rule RULE-001>.status

tests/test_rules.py:42: AssertionError
"""

SAMPLE_ATTRIBUTE_ERROR = """
Traceback (most recent call last):
  File "tests/test_agents.py", line 25, in test_agent_trust
    score = agent.get_trust_score()
  File "/home/user/project/governance/agents.py", line 100, in get_trust_score
    return self.trust_manager.calculate()
AttributeError: 'NoneType' object has no attribute 'calculate'
"""

SAMPLE_LONG_TRACEBACK = """
Traceback (most recent call last):
  File "/home/user/.venv/lib/python3.13/site-packages/_pytest/runner.py", line 341, in from_call
    result = func()
  File "/home/user/.venv/lib/python3.13/site-packages/_pytest/runner.py", line 262, in <lambda>
    lambda: ihook(item=item, **kwds), when=when, reraise=reraise
  File "/home/user/.venv/lib/python3.13/site-packages/pluggy/_hooks.py", line 513, in __call__
    return self._hookexec(self.name, self._hookimpls, kwargs, firstresult)
  File "/home/user/.venv/lib/python3.13/site-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
  File "/home/user/project/tests/test_rules.py", line 42, in test_rule_creation
    assert rule.status == 'ACTIVE'
  File "/home/user/project/governance/models.py", line 50, in status
    return self._get_status()
AssertionError: Expected ACTIVE but got INACTIVE
"""


class TestErrorClassification:
    """Tests for error classification."""

    def test_classify_assertion_error(self):
        """Test classifying AssertionError."""
        minimizer = TraceMinimizer()
        error_type, category = minimizer.classify_error(SAMPLE_ASSERTION_ERROR)

        assert error_type == "AssertionError"
        assert category == ErrorCategory.ASSERTION

    def test_classify_attribute_error(self):
        """Test classifying AttributeError."""
        minimizer = TraceMinimizer()
        error_type, category = minimizer.classify_error(SAMPLE_ATTRIBUTE_ERROR)

        assert error_type == "AttributeError"
        assert category == ErrorCategory.ATTRIBUTE

    def test_classify_timeout_error(self):
        """Test classifying TimeoutError."""
        minimizer = TraceMinimizer()
        error_type, category = minimizer.classify_error("TimeoutError: Connection timed out")

        assert "Timeout" in error_type
        assert category == ErrorCategory.TIMEOUT

    def test_classify_import_error(self):
        """Test classifying ImportError."""
        minimizer = TraceMinimizer()
        error_type, category = minimizer.classify_error("ImportError: No module named 'missing'")

        assert error_type == "ImportError"
        assert category == ErrorCategory.IMPORT

    def test_classify_value_error(self):
        """Test classifying ValueError."""
        minimizer = TraceMinimizer()
        error_type, category = minimizer.classify_error("ValueError: Invalid value")

        assert error_type == "ValueError"
        assert category == ErrorCategory.VALUE

    def test_classify_unknown_error(self):
        """Test classifying unknown error."""
        minimizer = TraceMinimizer()
        error_type, category = minimizer.classify_error("SomeCustomError: Something happened")

        assert "CustomError" in error_type
        assert category == ErrorCategory.UNKNOWN


class TestMessageExtraction:
    """Tests for error message extraction."""

    def test_extract_assertion_message(self):
        """Test extracting assertion error message."""
        minimizer = TraceMinimizer()
        message = minimizer.extract_message(SAMPLE_ASSERTION_ERROR)

        assert "INACTIVE" in message or "ACTIVE" in message

    def test_extract_attribute_message(self):
        """Test extracting attribute error message."""
        minimizer = TraceMinimizer()
        message = minimizer.extract_message(SAMPLE_ATTRIBUTE_ERROR)

        assert "NoneType" in message or "calculate" in message

    def test_truncate_long_message(self):
        """Test that long messages are truncated."""
        minimizer = TraceMinimizer(max_message_length=50)
        long_error = "AssertionError: " + "x" * 200
        message = minimizer.extract_message(long_error)

        assert len(message) <= 53  # 50 + "..."
        assert message.endswith("...")


class TestFrameFiltering:
    """Tests for stack frame filtering."""

    def test_is_framework_code_pytest(self):
        """Test detecting pytest framework code."""
        minimizer = TraceMinimizer()

        assert minimizer.is_framework_code("/home/user/.venv/lib/python3.13/site-packages/_pytest/runner.py")
        assert minimizer.is_framework_code("/home/user/.venv/lib/python3.13/site-packages/pytest/__init__.py")

    def test_is_framework_code_pluggy(self):
        """Test detecting pluggy framework code."""
        minimizer = TraceMinimizer()

        assert minimizer.is_framework_code("/site-packages/pluggy/_hooks.py")

    def test_is_user_code(self):
        """Test detecting user code."""
        minimizer = TraceMinimizer()

        assert not minimizer.is_framework_code("/home/user/project/tests/test_rules.py")
        assert not minimizer.is_framework_code("/home/user/project/governance/models.py")

    def test_parse_traceback(self):
        """Test parsing traceback into frames."""
        minimizer = TraceMinimizer()
        frames = minimizer.parse_traceback(SAMPLE_ATTRIBUTE_ERROR)

        assert len(frames) >= 2
        assert any("test_agents.py" in f.file for f in frames)

    def test_filter_frames_user_only(self):
        """Test filtering to user code only."""
        minimizer = TraceMinimizer(max_frames=5, include_user_code_only=True)
        frames = minimizer.parse_traceback(SAMPLE_LONG_TRACEBACK)
        filtered = minimizer.filter_frames(frames)

        # Should only have user code frames
        for frame in filtered:
            assert frame.is_user_code

    def test_filter_frames_max_count(self):
        """Test limiting max frames."""
        minimizer = TraceMinimizer(max_frames=2)
        frames = minimizer.parse_traceback(SAMPLE_LONG_TRACEBACK)
        filtered = minimizer.filter_frames(frames)

        assert len(filtered) <= 2


class TestMinimizedFrame:
    """Tests for MinimizedFrame dataclass."""

    def test_frame_creation(self):
        """Test creating a MinimizedFrame."""
        frame = MinimizedFrame(
            file="/home/user/project/tests/test_rules.py",
            line=42,
            function="test_rule_creation",
            code="assert rule.status == 'ACTIVE'",
        )

        assert frame.line == 42
        assert frame.is_user_code is True

    def test_format_compact(self):
        """Test compact formatting."""
        frame = MinimizedFrame(
            file="/home/user/project/tests/test_rules.py",
            line=42,
            function="test_rule_creation",
            code="assert rule.status == 'ACTIVE'",
        )

        formatted = frame.format_compact()
        assert "test_rules.py:42" in formatted
        assert "test_rule_creation()" in formatted


class TestMinimizedTrace:
    """Tests for MinimizedTrace dataclass."""

    def test_trace_creation(self):
        """Test creating a MinimizedTrace."""
        trace = MinimizedTrace(
            test_id="tests/test_rules.py::test_rule_creation",
            error_type="AssertionError",
            error_category=ErrorCategory.ASSERTION,
            error_message="Expected ACTIVE but got INACTIVE",
        )

        assert trace.error_category == ErrorCategory.ASSERTION
        assert "ACTIVE" in trace.error_message

    def test_to_dict(self):
        """Test converting to dictionary."""
        trace = MinimizedTrace(
            correlation_id="TEST-20260121-ABC123",
            test_id="test_example",
            error_type="AssertionError",
            error_category=ErrorCategory.ASSERTION,
            error_message="Test failed",
            original_tokens=1000,
            minimized_tokens=100,
        )

        data = trace.to_dict()

        assert data["correlation_id"] == "TEST-20260121-ABC123"
        assert data["error_category"] == ErrorCategory.ASSERTION
        assert data["compression"]["original_tokens"] == 1000
        assert "90%" in data["compression"]["ratio"]

    def test_format_compact(self):
        """Test compact formatting."""
        trace = MinimizedTrace(
            error_type="AssertionError",
            error_category=ErrorCategory.ASSERTION,
            error_message="Expected ACTIVE",
            bdd_context="THEN the rule should be active",
            correlation_id="TEST-ABC",
        )

        formatted = trace.format_compact()

        assert "[ASSERTION]" in formatted
        assert "AssertionError" in formatted
        assert "BDD:" in formatted
        assert "TEST-ABC" in formatted


class TestTraceMinimizer:
    """Tests for TraceMinimizer class."""

    def test_minimizer_initialization(self):
        """Test minimizer initialization."""
        minimizer = TraceMinimizer(max_frames=5, max_message_length=100)

        assert minimizer.max_frames == 5
        assert minimizer.max_message_length == 100

    def test_estimate_tokens(self):
        """Test token estimation."""
        minimizer = TraceMinimizer()

        # ~4 chars per token
        assert minimizer.estimate_tokens("a" * 40) == 10
        assert minimizer.estimate_tokens("") == 0

    def test_minimize_traceback(self):
        """Test minimizing a full traceback."""
        minimizer = TraceMinimizer()
        result = minimizer.minimize_traceback(
            SAMPLE_ASSERTION_ERROR,
            test_id="tests/test_rules.py::test_rule_creation",
        )

        assert isinstance(result, MinimizedTrace)
        assert result.error_type == "AssertionError"
        assert result.error_category == ErrorCategory.ASSERTION
        assert result.minimized_tokens < result.original_tokens

    def test_minimize_empty_traceback(self):
        """Test minimizing empty traceback."""
        minimizer = TraceMinimizer()
        result = minimizer.minimize_traceback("", test_id="test_empty")

        assert result.error_message == "No traceback"

    def test_minimize_traceback_with_context(self):
        """Test minimizing with BDD context."""
        minimizer = TraceMinimizer()
        result = minimizer.minimize_traceback(
            SAMPLE_ASSERTION_ERROR,
            test_id="test_example",
            correlation_id="CORR-123",
            bdd_context="THEN the rule should be active",
        )

        assert result.correlation_id == "CORR-123"
        assert result.bdd_context == "THEN the rule should be active"

    def test_minimize_traces_collection(self):
        """Test minimizing a collection of traces."""
        minimizer = TraceMinimizer()
        traces = [
            {"url": "/api/rules", "status_code": 200, "correlation_id": "CORR-1"},
            {"url": "/api/rules", "status_code": 404, "error": "Not found", "correlation_id": "CORR-1"},
            {"url": "/api/agents", "status_code": 500, "error": "Server error", "correlation_id": "CORR-2"},
        ]

        result = minimizer.minimize_traces(traces)

        assert result["total_traces"] == 3
        assert result["error_traces"] == 2  # Only 404 and 500
        assert result["correlation_groups"] == 2
        assert "compression" in result


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_minimize_for_llm(self):
        """Test minimize_for_llm function."""
        result = minimize_for_llm(
            SAMPLE_ASSERTION_ERROR,
            test_id="test_example",
            max_frames=2,
        )

        assert isinstance(result, str)
        assert "[ASSERTION]" in result
        assert len(result) < len(SAMPLE_ASSERTION_ERROR)

    def test_estimate_compression(self):
        """Test estimate_compression function."""
        original = "x" * 1000
        minimized = "x" * 100

        result = estimate_compression(original, minimized)

        assert result["original_tokens"] == 250
        assert result["minimized_tokens"] == 25
        assert "90%" in result["ratio"]
        assert result["saved_tokens"] == 225


class TestIntegration:
    """Integration tests for trace minimization."""

    def test_full_workflow(self):
        """Test full minimization workflow."""
        minimizer = TraceMinimizer(max_frames=3, max_message_length=150)

        # Minimize traceback
        result = minimizer.minimize_traceback(
            SAMPLE_LONG_TRACEBACK,
            test_id="tests/test_rules.py::test_rule_creation",
            correlation_id="TEST-20260121-FULL",
            bdd_context="THEN the rule should be active",
        )

        # Verify structure
        assert result.test_id == "tests/test_rules.py::test_rule_creation"
        assert result.correlation_id == "TEST-20260121-FULL"
        assert result.error_category == ErrorCategory.ASSERTION

        # Verify compression
        assert result.minimized_tokens < result.original_tokens
        compression_ratio = 1 - (result.minimized_tokens / result.original_tokens)
        assert compression_ratio > 0.5  # At least 50% compression

        # Verify output formats
        dict_output = result.to_dict()
        assert "compression" in dict_output

        compact_output = result.format_compact()
        assert len(compact_output) < len(SAMPLE_LONG_TRACEBACK)

    def test_minimizer_preserves_essential_info(self):
        """Test that minimization preserves essential debugging info."""
        minimizer = TraceMinimizer()

        result = minimizer.minimize_traceback(SAMPLE_ASSERTION_ERROR)

        # Must have error type and message
        assert result.error_type is not None
        assert result.error_message is not None
        assert len(result.error_message) > 0

        # Compact format must be usable
        compact = result.format_compact()
        assert result.error_type in compact
