"""
RF-004: Robot Framework Library for Session Test Result Capture.

Wraps governance/session_collector/capture.py for Robot Framework tests.
Per GAP-TEST-EVIDENCE-002: Event-based test reporting via Document Service.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SessionTestResultLibrary:
    """Robot Framework library for Session Test Result functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'
    ROBOT_LIBRARY_VERSION = '1.0.0'

    def __init__(self):
        self._collector = None
        self._session_available = None

    def check_session_available(self) -> bool:
        """Check if SessionCollector is available."""
        if self._session_available is None:
            try:
                from governance.session_collector.capture import SessionCaptureMixin
                from governance.session_collector.models import SessionEvent
                self._session_available = True
            except ImportError:
                self._session_available = False
        return self._session_available

    def create_mock_collector(self, session_id: str = "SESSION-TEST") -> bool:
        """Create a mock collector for testing."""
        if not self.check_session_available():
            return False

        from governance.session_collector.capture import SessionCaptureMixin

        class MockCollector(SessionCaptureMixin):
            def __init__(self, sid):
                self.session_id = sid
                self.events = []

        self._collector = MockCollector(session_id)
        return True

    def capture_test_result(
        self,
        test_id: str,
        name: str,
        category: str,
        status: str,
        duration_ms: float = 0.0,
        intent: str = None,
        error_message: str = None,
        linked_rules: List[str] = None,
        linked_gaps: List[str] = None
    ) -> bool:
        """Capture a test result in the mock collector."""
        if not self._collector:
            return False

        kwargs = {
            "test_id": test_id,
            "name": name,
            "category": category,
            "status": status,
            "duration_ms": float(duration_ms) if duration_ms else 0.0,
        }
        if intent:
            kwargs["intent"] = intent
        if error_message:
            kwargs["error_message"] = error_message
        if linked_rules:
            kwargs["linked_rules"] = linked_rules
        if linked_gaps:
            kwargs["linked_gaps"] = linked_gaps

        self._collector.capture_test_result(**kwargs)
        return True

    def get_event_count(self) -> int:
        """Get count of captured events."""
        return len(self._collector.events) if self._collector else 0

    def get_last_event(self) -> Dict[str, Any]:
        """Get the last captured event as dict."""
        if not self._collector or not self._collector.events:
            return {}
        event = self._collector.events[-1]
        return {
            "event_type": event.event_type,
            "content": event.content,
            "metadata": event.metadata
        }

    def get_event_at(self, index: int) -> Dict[str, Any]:
        """Get event at specific index as dict."""
        if not self._collector or index >= len(self._collector.events):
            return {}
        event = self._collector.events[int(index)]
        return {
            "event_type": event.event_type,
            "content": event.content,
            "metadata": event.metadata
        }

    def get_event_metadata(self, key: str) -> Any:
        """Get metadata value from last event."""
        event = self.get_last_event()
        return event.get("metadata", {}).get(key)

    def event_content_contains(self, text: str) -> bool:
        """Check if last event content contains text."""
        event = self.get_last_event()
        return text in event.get("content", "")

    def create_full_collector(self, topic: str) -> bool:
        """Create a full SessionCollector."""
        if not self.check_session_available():
            return False

        from governance.session_collector import SessionCollector
        self._collector = SessionCollector(topic, session_type="test")
        return True
