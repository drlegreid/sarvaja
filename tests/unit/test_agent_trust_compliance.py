"""
Unit tests for Agent Trust Compliance Mixin.

Per DOC-SIZE-01-v1: Tests for extracted agent_trust_compliance.py.
Tests: get_compliance_status, get_compliance_summary, get_agent_metrics, get_system_metrics.
"""

import pytest
from dataclasses import dataclass

from agent.agent_trust_compliance import AgentTrustComplianceMixin
from agent.agent_trust_models import ActionRecord, ComplianceStatus


class MockTrustSystem(AgentTrustComplianceMixin):
    """Test host for the mixin."""

    GOVERNANCE_RULES = ["RULE-001", "RULE-002"]

    def __init__(self):
        self._trust_scores = {}
        self._action_history = {}
        self._compliance_cache = {}

    def get_trust_score(self, agent_id):
        return self._trust_scores.get(agent_id, 0.5)

    def get_trust_level(self, agent_id):
        score = self.get_trust_score(agent_id)
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        return "LOW"

    def is_trusted(self, agent_id):
        return self.get_trust_score(agent_id) >= 0.7


class TestGetComplianceStatus:
    """Tests for get_compliance_status()."""

    def test_compliant_agent(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-1"] = 0.9
        sys._action_history["agent-1"] = [
            ActionRecord("agent-1", "read", True, "2026-01-01T00:00:00", 0.01),
        ]
        result = sys.get_compliance_status("agent-1")
        assert result["compliant"] is True
        assert result["violations"] == []

    def test_non_compliant_agent(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-2"] = 0.3
        sys._action_history["agent-2"] = [
            ActionRecord("agent-2", "bad_action", False, "2026-01-01T00:00:00", -0.05),
        ]
        result = sys.get_compliance_status("agent-2")
        assert result["compliant"] is False
        assert "bad_action" in result["violations"]

    def test_caches_result(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-3"] = 0.9
        sys._action_history["agent-3"] = []
        result1 = sys.get_compliance_status("agent-3")
        result2 = sys.get_compliance_status("agent-3")
        assert result1["last_check"] == result2["last_check"]

    def test_no_history(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-4"] = 0.5
        result = sys.get_compliance_status("agent-4")
        assert result["compliant"] is True

    def test_caps_violations_at_5(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-5"] = 0.2
        sys._action_history["agent-5"] = [
            ActionRecord("agent-5", f"bad_{i}", False, "2026-01-01", -0.01)
            for i in range(10)
        ]
        result = sys.get_compliance_status("agent-5")
        assert len(result["violations"]) == 5


class TestGetComplianceSummary:
    """Tests for get_compliance_summary()."""

    def test_all_compliant(self):
        sys = MockTrustSystem()
        sys._trust_scores = {"a": 0.9, "b": 0.8}
        sys._action_history = {"a": [], "b": []}
        result = sys.get_compliance_summary()
        assert result["total_agents"] == 2
        assert result["compliant_agents"] == 2
        assert result["compliance_rate"] == 1.0

    def test_mixed_compliance(self):
        sys = MockTrustSystem()
        sys._trust_scores = {"good": 0.9, "bad": 0.3}
        sys._action_history = {
            "good": [],
            "bad": [ActionRecord("bad", "violation", False, "2026-01-01", -0.1)],
        }
        result = sys.get_compliance_summary()
        assert result["compliant_agents"] == 1
        assert result["non_compliant_agents"] == 1

    def test_empty(self):
        sys = MockTrustSystem()
        result = sys.get_compliance_summary()
        assert result["total_agents"] == 0
        assert result["compliance_rate"] == 0.0


class TestGetAgentMetrics:
    """Tests for get_agent_metrics()."""

    def test_with_history(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-1"] = 0.85
        sys._action_history["agent-1"] = [
            ActionRecord("agent-1", "read", True, "2026-01-01", 0.01),
            ActionRecord("agent-1", "write", True, "2026-01-02", 0.01),
            ActionRecord("agent-1", "bad", False, "2026-01-03", -0.05),
        ]
        result = sys.get_agent_metrics("agent-1")
        assert result["total_actions"] == 3
        assert result["compliant_actions"] == 2
        assert result["trust_score"] == 0.85
        assert result["trust_level"] == "HIGH"
        assert result["is_trusted"] is True

    def test_no_history(self):
        sys = MockTrustSystem()
        sys._trust_scores["agent-2"] = 0.4
        result = sys.get_agent_metrics("agent-2")
        assert result["total_actions"] == 0
        assert result["last_action"] is None


class TestGetSystemMetrics:
    """Tests for get_system_metrics()."""

    def test_with_agents(self):
        sys = MockTrustSystem()
        sys._trust_scores = {"a": 0.9, "b": 0.6, "c": 0.3}
        sys._action_history = {"a": [], "b": [], "c": []}
        result = sys.get_system_metrics()
        assert result["total_agents"] == 3
        assert abs(result["average_trust_score"] - 0.6) < 1e-9
        assert "trust_levels" in result
        assert "compliance_summary" in result

    def test_empty_system(self):
        sys = MockTrustSystem()
        result = sys.get_system_metrics()
        assert result["total_agents"] == 0
        assert result["total_actions_recorded"] == 0
