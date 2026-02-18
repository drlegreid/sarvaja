"""
Unit Tests for Session Test Result Capture.

Per GAP-TEST-EVIDENCE-002: Event-based test reporting via Document Service.
Tests the session_test_result functionality.

Created: 2026-01-21
"""

import pytest

# Check if session collector is available
try:
    from governance.session_collector.capture import SessionCaptureMixin
    from governance.session_collector.models import SessionEvent
    SESSION_AVAILABLE = True
except ImportError:
    SESSION_AVAILABLE = False


@pytest.mark.skipif(not SESSION_AVAILABLE, reason="SessionCollector not available")
class TestSessionTestResult:
    """Tests for capture_test_result method."""

    def test_capture_test_result_basic(self):
        """capture_test_result creates test_result event."""
        # Create a mock collector with mixin
        class MockCollector(SessionCaptureMixin):
            def __init__(self):
                self.session_id = "SESSION-2026-01-21-TEST"
                self.events = []

        collector = MockCollector()

        # Capture a test result
        collector.capture_test_result(
            test_id="tests/unit/test_auth.py::test_login",
            name="test_login",
            category="unit",
            status="passed",
            duration_ms=150.0,
            intent="User login with valid credentials"
        )

        assert len(collector.events) == 1
        event = collector.events[0]
        assert event.event_type == "test_result"
        assert "PASSED: test_login" in event.content
        assert event.metadata["test_id"] == "tests/unit/test_auth.py::test_login"
        assert event.metadata["status"] == "passed"
        assert event.metadata["category"] == "unit"
        assert event.metadata["duration_ms"] == 150.0

    def test_capture_test_result_with_rules(self):
        """capture_test_result includes linked rules."""
        class MockCollector(SessionCaptureMixin):
            def __init__(self):
                self.session_id = "SESSION-2026-01-21-TEST"
                self.events = []

        collector = MockCollector()

        collector.capture_test_result(
            test_id="test_rule_compliance",
            name="test_rule_compliance",
            category="integration",
            status="passed",
            duration_ms=200.0,
            linked_rules=["RULE-001", "SESSION-EVID-01-v1"],
            linked_gaps=["GAP-TEST-001"]
        )

        event = collector.events[0]
        assert "RULE-001" in event.metadata["linked_rules"]
        assert "SESSION-EVID-01-v1" in event.metadata["linked_rules"]
        assert "GAP-TEST-001" in event.metadata["linked_gaps"]

    def test_capture_test_result_failed(self):
        """capture_test_result captures error message for failed tests."""
        class MockCollector(SessionCaptureMixin):
            def __init__(self):
                self.session_id = "SESSION-2026-01-21-TEST"
                self.events = []

        collector = MockCollector()

        collector.capture_test_result(
            test_id="test_failing",
            name="test_failing",
            category="unit",
            status="failed",
            duration_ms=50.0,
            error_message="AssertionError: Expected True but got False"
        )

        event = collector.events[0]
        assert event.metadata["status"] == "failed"
        assert "AssertionError" in event.metadata["error_message"]
        assert "FAILED: test_failing" in event.content

    def test_capture_test_result_error_truncation(self):
        """capture_test_result truncates long error messages."""
        class MockCollector(SessionCaptureMixin):
            def __init__(self):
                self.session_id = "SESSION-2026-01-21-TEST"
                self.events = []

        collector = MockCollector()

        # Create a very long error message
        long_error = "Error: " + "x" * 1000

        collector.capture_test_result(
            test_id="test_long_error",
            name="test_long_error",
            category="unit",
            status="failed",
            error_message=long_error
        )

        event = collector.events[0]
        assert len(event.metadata["error_message"]) <= 503  # 500 + "..."

    def test_capture_test_result_skipped(self):
        """capture_test_result handles skipped tests."""
        class MockCollector(SessionCaptureMixin):
            def __init__(self):
                self.session_id = "SESSION-2026-01-21-TEST"
                self.events = []

        collector = MockCollector()

        collector.capture_test_result(
            test_id="test_skipped",
            name="test_skipped",
            category="e2e",
            status="skipped",
            duration_ms=0.0,
            intent="Skipped due to missing fixture"
        )

        event = collector.events[0]
        assert event.metadata["status"] == "skipped"
        assert event.metadata["category"] == "e2e"
        assert "SKIPPED: test_skipped" in event.content


class TestSessionTestResultIntegration:
    """Integration tests for session test result with full collector."""

    @pytest.mark.skipif(not SESSION_AVAILABLE, reason="SessionCollector not available")
    def test_capture_test_result_full_collector(self):
        """Test capture_test_result with full SessionCollector."""
        from governance.session_collector import SessionCollector

        collector = SessionCollector("TEST-EVIDENCE", session_type="test")

        # Capture multiple test results
        collector.capture_test_result(
            test_id="test_1",
            name="test_1",
            category="unit",
            status="passed",
            duration_ms=100.0,
            intent="First test"
        )
        collector.capture_test_result(
            test_id="test_2",
            name="test_2",
            category="unit",
            status="failed",
            duration_ms=50.0,
            error_message="Test failed"
        )

        # Verify events were captured
        test_events = [e for e in collector.events if e.event_type == "test_result"]
        assert len(test_events) == 2

        # Verify first test
        assert test_events[0].metadata["status"] == "passed"
        assert test_events[0].metadata["test_id"] == "test_1"

        # Verify second test
        assert test_events[1].metadata["status"] == "failed"
        assert test_events[1].metadata["error_message"] == "Test failed"
