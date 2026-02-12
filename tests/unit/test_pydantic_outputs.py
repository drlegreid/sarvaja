"""
Unit tests for Pydantic Output Models.

Per DOC-SIZE-01-v1: Tests for pydantic_schemas/models/outputs.py module.
Tests: RuleInfo, RuleQueryResult, DependencyResult, TrustScoreResult,
       ProposalResult, ImpactAnalysisResult, HealthCheckResult.
"""

import pytest
from pydantic import ValidationError

from governance.pydantic_schemas.models.outputs import (
    RuleInfo,
    RuleQueryResult,
    DependencyResult,
    TrustScoreResult,
    ProposalResult,
    ImpactAnalysisResult,
    HealthCheckResult,
)


class TestRuleInfo:
    def test_minimal(self):
        r = RuleInfo(rule_id="R-1", name="Test", category="GOV",
                     priority="HIGH", status="ACTIVE")
        assert r.dependencies == []
        assert r.dependents == []

    def test_with_deps(self):
        r = RuleInfo(rule_id="R-1", name="Test", category="GOV",
                     priority="HIGH", status="ACTIVE",
                     dependencies=["R-2"], dependents=["R-3"])
        assert r.dependencies == ["R-2"]


class TestRuleQueryResult:
    def test_success(self):
        r = RuleQueryResult(success=True, total_count=5, filtered_count=3,
                            query_time_ms=12.5)
        assert r.rules == []
        assert r.error is None

    def test_with_error(self):
        r = RuleQueryResult(success=False, total_count=0, filtered_count=0,
                            query_time_ms=0, error="connection failed")
        assert r.error == "connection failed"

    def test_negative_count_rejected(self):
        with pytest.raises(ValidationError):
            RuleQueryResult(success=True, total_count=-1, filtered_count=0,
                            query_time_ms=0)


class TestDependencyResult:
    def test_success(self):
        r = DependencyResult(success=True, rule_id="R-1", dependency_depth=2,
                             dependencies=["R-2"], transitive_dependencies=["R-3"])
        assert r.dependency_depth == 2

    def test_depth_required(self):
        with pytest.raises(ValidationError):
            DependencyResult(success=True, rule_id="R-1")

    def test_negative_depth_rejected(self):
        with pytest.raises(ValidationError):
            DependencyResult(success=True, rule_id="R-1", dependency_depth=-1)


class TestTrustScoreResult:
    def test_success(self):
        r = TrustScoreResult(success=True, agent_id="A-1", trust_score=0.85,
                             vote_weight=0.7)
        assert r.components == {}

    def test_invalid_trust_score(self):
        with pytest.raises(ValidationError):
            TrustScoreResult(success=True, agent_id="A-1", trust_score=1.5,
                             vote_weight=0.7)

    def test_with_components(self):
        r = TrustScoreResult(success=True, agent_id="A-1", trust_score=0.8,
                             vote_weight=0.6,
                             components={"compliance": 0.9, "accuracy": 0.7})
        assert r.components["compliance"] == 0.9


class TestProposalResult:
    def test_success(self):
        r = ProposalResult(success=True, action="create",
                           message="Created", proposal_id="PROP-1")
        assert r.status == "pending"

    def test_with_error(self):
        r = ProposalResult(success=False, action="create",
                           message="Failed", status="error", error="bad input")
        assert r.status == "error"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            ProposalResult(success=True, action="create",
                           message="test", status="invalid")


class TestImpactAnalysisResult:
    def test_success(self):
        r = ImpactAnalysisResult(success=True, rule_id="R-1",
                                 impact_score=45.0, risk_level="MEDIUM",
                                 affected_count=3)
        assert r.recommendations == []

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            ImpactAnalysisResult(success=True, rule_id="R-1",
                                 impact_score=101, risk_level="LOW",
                                 affected_count=0)

    def test_invalid_risk_level(self):
        with pytest.raises(ValidationError):
            ImpactAnalysisResult(success=True, rule_id="R-1",
                                 impact_score=50, risk_level="EXTREME",
                                 affected_count=0)


class TestHealthCheckResult:
    def test_healthy(self):
        r = HealthCheckResult(healthy=True, typedb_connected=True,
                              rules_count=50, active_rules_count=45,
                              agents_count=5, last_check="2026-01-01T00:00:00")
        assert r.chromadb_connected is False
        assert r.issues == []

    def test_unhealthy(self):
        r = HealthCheckResult(healthy=False, typedb_connected=False,
                              rules_count=0, active_rules_count=0,
                              agents_count=0, last_check="2026-01-01",
                              issues=["TypeDB unreachable"])
        assert len(r.issues) == 1
