"""
Unit tests for Batch Routing Mixin.

Per DOC-SIZE-01-v1: Tests for router/batch.py module.
Tests: BatchRoutingMixin.route_auto, route_batch, ID patterns.
"""

import pytest
from unittest.mock import MagicMock

from governance.router.batch import BatchRoutingMixin


class _TestBatchRouter(BatchRoutingMixin):
    """Concrete class for testing batch routing mixin."""

    def __init__(self):
        self._rule_calls = []
        self._decision_calls = []
        self._session_calls = []

    def route_rule(self, **kwargs):
        self._rule_calls.append(kwargs)
        return {"success": True, "item_type": "rule"}

    def route_decision(self, **kwargs):
        self._decision_calls.append(kwargs)
        return {"success": True, "item_type": "decision"}

    def route_session(self, **kwargs):
        self._session_calls.append(kwargs)
        return {"success": True, "item_type": "session"}


# ---------------------------------------------------------------------------
# ID patterns
# ---------------------------------------------------------------------------
class TestPatterns:
    """Tests for ID pattern matching."""

    def test_rule_pattern_matches(self):
        assert BatchRoutingMixin.RULE_PATTERN.match("RULE-001")
        assert BatchRoutingMixin.RULE_PATTERN.match("RULE-999")

    def test_rule_pattern_rejects_invalid(self):
        assert not BatchRoutingMixin.RULE_PATTERN.match("RULE-1")
        assert not BatchRoutingMixin.RULE_PATTERN.match("RULE-ABCD")
        assert not BatchRoutingMixin.RULE_PATTERN.match("rule-001")

    def test_decision_pattern_matches(self):
        assert BatchRoutingMixin.DECISION_PATTERN.match("DECISION-001")
        assert BatchRoutingMixin.DECISION_PATTERN.match("DECISION-999")

    def test_decision_pattern_rejects_invalid(self):
        assert not BatchRoutingMixin.DECISION_PATTERN.match("DECISION-1")
        assert not BatchRoutingMixin.DECISION_PATTERN.match("DEC-001")

    def test_session_pattern_matches(self):
        assert BatchRoutingMixin.SESSION_PATTERN.match("SESSION-2026-02-11")
        assert BatchRoutingMixin.SESSION_PATTERN.match("SESSION-2026-02-11-CHAT-TEST")

    def test_session_pattern_rejects_invalid(self):
        assert not BatchRoutingMixin.SESSION_PATTERN.match("SESSION-INVALID")
        assert not BatchRoutingMixin.SESSION_PATTERN.match("SESS-2026-02-11")


# ---------------------------------------------------------------------------
# route_auto
# ---------------------------------------------------------------------------
class TestRouteAuto:
    """Tests for route_auto()."""

    def test_detects_rule(self):
        router = _TestBatchRouter()
        result = router.route_auto("RULE-001", {"name": "Test"})
        assert result["type"] == "rule"
        assert result["success"] is True
        assert len(router._rule_calls) == 1

    def test_detects_decision(self):
        router = _TestBatchRouter()
        result = router.route_auto("DECISION-001", {"name": "Test"})
        assert result["type"] == "decision"
        assert result["success"] is True

    def test_detects_session(self):
        router = _TestBatchRouter()
        result = router.route_auto("SESSION-2026-02-11-TEST", {"content": "x"})
        assert result["type"] == "session"
        assert result["success"] is True

    def test_unknown_type(self):
        router = _TestBatchRouter()
        result = router.route_auto("UNKNOWN-001", {})
        assert result["success"] is False
        assert result["type"] == "unknown"
        assert "error" in result

    def test_passes_data_to_rule(self):
        router = _TestBatchRouter()
        router.route_auto("RULE-001", {"name": "My Rule", "directive": "Do X"})
        assert router._rule_calls[0]["name"] == "My Rule"
        assert router._rule_calls[0]["directive"] == "Do X"


# ---------------------------------------------------------------------------
# route_batch
# ---------------------------------------------------------------------------
class TestRouteBatch:
    """Tests for route_batch()."""

    def test_empty_batch(self):
        router = _TestBatchRouter()
        result = router.route_batch([])
        assert result["total"] == 0
        assert result["succeeded"] == 0
        assert result["failed"] == 0

    def test_single_rule(self):
        router = _TestBatchRouter()
        result = router.route_batch([{"type": "rule", "rule_id": "RULE-001", "name": "R1"}])
        assert result["total"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0

    def test_mixed_types(self):
        router = _TestBatchRouter()
        items = [
            {"type": "rule", "rule_id": "RULE-001", "name": "R1"},
            {"type": "decision", "decision_id": "DECISION-001", "name": "D1"},
            {"type": "session", "session_id": "SESSION-2026-02-11-TEST"},
        ]
        result = router.route_batch(items)
        assert result["total"] == 3
        assert result["succeeded"] == 3
        assert len(result["results"]) == 3

    def test_unknown_type_fails(self):
        router = _TestBatchRouter()
        result = router.route_batch([{"type": "unknown_type"}])
        assert result["total"] == 1
        assert result["failed"] == 1

    def test_exception_counted_as_failure(self):
        router = _TestBatchRouter()
        # Override route_rule to raise
        router.route_rule = MagicMock(side_effect=ValueError("bad"))
        result = router.route_batch([{"type": "rule", "rule_id": "R-1"}])
        assert result["failed"] == 1
        assert "bad" in result["results"][0]["error"]

    def test_batch_counts(self):
        router = _TestBatchRouter()
        items = [
            {"type": "rule", "rule_id": "RULE-001", "name": "ok"},
            {"type": "invalid"},  # fails
            {"type": "rule", "rule_id": "RULE-002", "name": "ok2"},
        ]
        result = router.route_batch(items)
        assert result["succeeded"] == 2
        assert result["failed"] == 1
        assert result["total"] == 3

    def test_results_list_matches_input(self):
        router = _TestBatchRouter()
        items = [
            {"type": "rule", "rule_id": "RULE-001", "name": "R"},
            {"type": "session", "session_id": "S-1"},
        ]
        result = router.route_batch(items)
        assert len(result["results"]) == 2
