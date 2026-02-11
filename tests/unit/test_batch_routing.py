"""
Unit tests for Batch Routing Mixin.

Per P7.3: Tests for BatchRoutingMixin auto-detection and batch routing.
"""

import pytest
from unittest.mock import MagicMock

from governance.router.batch import BatchRoutingMixin


class _TestRouter(BatchRoutingMixin):
    """Concrete test class implementing required route methods."""

    def route_rule(self, rule_id=None, **data):
        return {"success": True, "rule_id": rule_id, **data}

    def route_decision(self, decision_id=None, **data):
        return {"success": True, "decision_id": decision_id, **data}

    def route_session(self, session_id=None, **data):
        return {"success": True, "session_id": session_id, **data}


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------
class TestPatterns:
    """Tests for ID pattern regex matching."""

    def test_rule_pattern_matches(self):
        assert BatchRoutingMixin.RULE_PATTERN.match("RULE-001")
        assert BatchRoutingMixin.RULE_PATTERN.match("RULE-999")

    def test_rule_pattern_rejects(self):
        assert not BatchRoutingMixin.RULE_PATTERN.match("RULE-01")
        assert not BatchRoutingMixin.RULE_PATTERN.match("RULE-1234")
        assert not BatchRoutingMixin.RULE_PATTERN.match("rule-001")
        assert not BatchRoutingMixin.RULE_PATTERN.match("TASK-001")

    def test_decision_pattern_matches(self):
        assert BatchRoutingMixin.DECISION_PATTERN.match("DECISION-001")
        assert BatchRoutingMixin.DECISION_PATTERN.match("DECISION-123")

    def test_decision_pattern_rejects(self):
        assert not BatchRoutingMixin.DECISION_PATTERN.match("DECISION-01")
        assert not BatchRoutingMixin.DECISION_PATTERN.match("decision-001")
        assert not BatchRoutingMixin.DECISION_PATTERN.match("DEC-001")

    def test_session_pattern_matches(self):
        assert BatchRoutingMixin.SESSION_PATTERN.match("SESSION-2026-02-11")
        assert BatchRoutingMixin.SESSION_PATTERN.match("SESSION-2026-02-11-TOPIC")
        assert BatchRoutingMixin.SESSION_PATTERN.match("SESSION-2024-12-25-LONG-TOPIC-NAME")

    def test_session_pattern_rejects(self):
        assert not BatchRoutingMixin.SESSION_PATTERN.match("SESSION-2026-02")
        assert not BatchRoutingMixin.SESSION_PATTERN.match("session-2026-02-11")
        assert not BatchRoutingMixin.SESSION_PATTERN.match("SESS-2026-02-11")


# ---------------------------------------------------------------------------
# route_auto
# ---------------------------------------------------------------------------
class TestRouteAuto:
    """Tests for route_auto() auto-detection."""

    def setup_method(self):
        self.router = _TestRouter()

    def test_detects_rule(self):
        result = self.router.route_auto("RULE-001", {"action": "query"})
        assert result["type"] == "rule"
        assert result["success"] is True
        assert result["rule_id"] == "RULE-001"

    def test_detects_decision(self):
        result = self.router.route_auto("DECISION-042", {"action": "vote"})
        assert result["type"] == "decision"
        assert result["success"] is True
        assert result["decision_id"] == "DECISION-042"

    def test_detects_session(self):
        result = self.router.route_auto("SESSION-2026-02-11-TEST", {"action": "view"})
        assert result["type"] == "session"
        assert result["success"] is True
        assert result["session_id"] == "SESSION-2026-02-11-TEST"

    def test_unknown_identifier(self):
        result = self.router.route_auto("TASK-001", {})
        assert result["type"] == "unknown"
        assert result["success"] is False
        assert "error" in result

    def test_empty_identifier(self):
        result = self.router.route_auto("", {})
        assert result["type"] == "unknown"
        assert result["success"] is False

    def test_data_passed_through(self):
        result = self.router.route_auto("RULE-001", {"extra": "value"})
        assert result["extra"] == "value"


# ---------------------------------------------------------------------------
# route_batch
# ---------------------------------------------------------------------------
class TestRouteBatch:
    """Tests for route_batch() batch processing."""

    def setup_method(self):
        self.router = _TestRouter()

    def test_empty_batch(self):
        result = self.router.route_batch([])
        assert result["total"] == 0
        assert result["succeeded"] == 0
        assert result["failed"] == 0
        assert result["results"] == []

    def test_single_rule(self):
        items = [{"type": "rule", "rule_id": "RULE-001"}]
        result = self.router.route_batch(items)
        assert result["total"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0

    def test_mixed_types(self):
        items = [
            {"type": "rule", "rule_id": "RULE-001"},
            {"type": "decision", "decision_id": "DECISION-001"},
            {"type": "session", "session_id": "SESSION-2026-02-11-TEST"},
        ]
        result = self.router.route_batch(items)
        assert result["total"] == 3
        assert result["succeeded"] == 3
        assert result["failed"] == 0

    def test_unknown_type_fails(self):
        items = [{"type": "unknown_type", "id": "X-1"}]
        result = self.router.route_batch(items)
        assert result["total"] == 1
        assert result["succeeded"] == 0
        assert result["failed"] == 1
        assert "error" in result["results"][0]

    def test_missing_type_fails(self):
        items = [{"rule_id": "RULE-001"}]  # no 'type' key
        result = self.router.route_batch(items)
        assert result["failed"] == 1

    def test_exception_in_route_counted_as_failure(self):
        """When route method raises, should count as failure."""
        router = _TestRouter()
        router.route_rule = MagicMock(side_effect=ValueError("test error"))
        items = [{"type": "rule", "rule_id": "RULE-001"}]
        result = router.route_batch(items)
        assert result["failed"] == 1
        assert "test error" in result["results"][0]["error"]

    def test_partial_success(self):
        router = _TestRouter()
        router.route_decision = MagicMock(return_value={"success": False, "error": "denied"})
        items = [
            {"type": "rule", "rule_id": "RULE-001"},
            {"type": "decision", "decision_id": "DECISION-001"},
        ]
        result = router.route_batch(items)
        assert result["succeeded"] == 1
        assert result["failed"] == 1

    def test_results_collected(self):
        items = [
            {"type": "rule", "rule_id": "RULE-001"},
            {"type": "rule", "rule_id": "RULE-002"},
        ]
        result = self.router.route_batch(items)
        assert len(result["results"]) == 2
        assert result["results"][0]["rule_id"] == "RULE-001"
        assert result["results"][1]["rule_id"] == "RULE-002"
