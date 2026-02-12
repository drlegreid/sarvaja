"""
Unit tests for Agent Dataclass Models.

Per DOC-SIZE-01-v1: Tests for agent/agent_trust_models.py + agent/rule_impact_models.py.
Tests: ActionRecord, ComplianceStatus, ImpactResult, GraphNode, GraphEdge.
"""

from agent.agent_trust_models import ActionRecord, ComplianceStatus
from agent.rule_impact_models import ImpactResult, GraphNode, GraphEdge


# ── ActionRecord ──────────────────────────────────────


class TestActionRecord:
    def test_fields(self):
        record = ActionRecord(
            agent_id="bot-1",
            action="rule_query",
            compliant=True,
            timestamp="2026-02-11T10:00:00",
            trust_delta=0.01,
        )
        assert record.agent_id == "bot-1"
        assert record.action == "rule_query"
        assert record.compliant is True
        assert record.trust_delta == 0.01

    def test_non_compliant(self):
        record = ActionRecord("bot-1", "violation", False, "2026-02-11", -0.05)
        assert record.compliant is False
        assert record.trust_delta == -0.05


# ── ComplianceStatus ──────────────────────────────────


class TestComplianceStatus:
    def test_compliant(self):
        status = ComplianceStatus(
            agent_id="bot-1",
            compliant=True,
            rules=["R-1", "R-2"],
            violations=[],
            last_check="2026-02-11T10:00:00",
        )
        assert status.compliant is True
        assert len(status.rules) == 2
        assert len(status.violations) == 0

    def test_non_compliant(self):
        status = ComplianceStatus(
            agent_id="bot-1",
            compliant=False,
            rules=["R-1"],
            violations=["Missing evidence"],
            last_check="2026-02-11",
        )
        assert status.compliant is False
        assert len(status.violations) == 1


# ── ImpactResult ──────────────────────────────────────


class TestImpactResult:
    def test_fields(self):
        result = ImpactResult(
            rule_id="R-1",
            change_type="deprecate",
            affected=["R-2", "R-3"],
            impact_score=0.7,
            warnings=["High impact change"],
        )
        assert result.rule_id == "R-1"
        assert result.change_type == "deprecate"
        assert len(result.affected) == 2
        assert result.impact_score == 0.7

    def test_no_impact(self):
        result = ImpactResult("R-1", "modify", [], 0.0, [])
        assert result.impact_score == 0.0
        assert len(result.warnings) == 0


# ── GraphNode ─────────────────────────────────────────


class TestGraphNode:
    def test_fields(self):
        node = GraphNode(
            rule_id="R-1", name="Rule One", priority="HIGH", category="governance")
        assert node.rule_id == "R-1"
        assert node.name == "Rule One"
        assert node.priority == "HIGH"
        assert node.category == "governance"


# ── GraphEdge ─────────────────────────────────────────


class TestGraphEdge:
    def test_fields(self):
        edge = GraphEdge(source="R-1", target="R-2", relationship="depends_on")
        assert edge.source == "R-1"
        assert edge.target == "R-2"
        assert edge.relationship == "depends_on"

    def test_conflict_edge(self):
        edge = GraphEdge("R-1", "R-3", "conflicts_with")
        assert edge.relationship == "conflicts_with"
