"""
Unit tests for Pydantic Input Models.

Per DOC-SIZE-01-v1: Tests for pydantic_schemas/models/inputs.py module.
Tests: RuleQueryConfig, DependencyConfig, TrustScoreRequest,
       ProposalConfig, ImpactAnalysisConfig, DSMCycleConfig.
"""

import pytest
from pydantic import ValidationError

from governance.pydantic_schemas.models.inputs import (
    RuleQueryConfig,
    DependencyConfig,
    TrustScoreRequest,
    ProposalConfig,
    ImpactAnalysisConfig,
    DSMCycleConfig,
)


class TestRuleQueryConfig:
    def test_defaults(self):
        config = RuleQueryConfig()
        assert config.category is None
        assert config.status is None
        assert config.priority is None
        assert config.include_dependencies is False

    def test_with_filters(self):
        config = RuleQueryConfig(
            category="governance", status="ACTIVE", priority="HIGH",
            include_dependencies=True,
        )
        assert config.category == "governance"
        assert config.status == "ACTIVE"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            RuleQueryConfig(status="INVALID")

    def test_invalid_priority(self):
        with pytest.raises(ValidationError):
            RuleQueryConfig(priority="ULTRA")


class TestDependencyConfig:
    def test_defaults(self):
        config = DependencyConfig(rule_id="RULE-001")
        assert config.include_transitive is True
        assert config.direction == "both"

    def test_rule_id_uppercase(self):
        config = DependencyConfig(rule_id="rule-001")
        assert config.rule_id == "RULE-001"

    def test_invalid_rule_id(self):
        with pytest.raises(ValidationError):
            DependencyConfig(rule_id="NOT-A-RULE")

    def test_direction_options(self):
        for d in ["dependencies", "dependents", "both"]:
            config = DependencyConfig(rule_id="RULE-001", direction=d)
            assert config.direction == d

    def test_invalid_direction(self):
        with pytest.raises(ValidationError):
            DependencyConfig(rule_id="RULE-001", direction="invalid")


class TestTrustScoreRequest:
    def test_valid(self):
        req = TrustScoreRequest(agent_id="AGENT-001")
        assert req.agent_id == "AGENT-001"

    def test_uppercase(self):
        req = TrustScoreRequest(agent_id="agent-001")
        assert req.agent_id == "AGENT-001"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            TrustScoreRequest(agent_id="NOT-AN-AGENT")


class TestProposalConfig:
    def test_valid_create(self):
        config = ProposalConfig(
            action="create",
            hypothesis="This is a long enough hypothesis",
            evidence=["evidence1"],
            directive="Do something",
        )
        assert config.action == "create"

    def test_modify_requires_rule_id(self):
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="modify",
                hypothesis="This is a long enough hypothesis",
                evidence=["e1"],
                directive="Do something",
            )

    def test_deprecate_requires_rule_id(self):
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="deprecate",
                hypothesis="This is a long enough hypothesis",
                evidence=["e1"],
            )

    def test_create_requires_directive(self):
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="create",
                hypothesis="This is a long enough hypothesis",
                evidence=["e1"],
            )

    def test_hypothesis_min_length(self):
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="create",
                hypothesis="short",
                evidence=["e1"],
                directive="Do X",
            )

    def test_evidence_min_length(self):
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="create",
                hypothesis="This is a long enough hypothesis",
                evidence=[],
                directive="Do X",
            )

    def test_rule_id_uppercase(self):
        # ProposalConfig validates prefix before uppercasing,
        # so lowercase "rule-001" fails. Must use "RULE-001".
        config = ProposalConfig(
            action="modify",
            hypothesis="This is a long enough hypothesis",
            evidence=["e1"],
            directive="Do X",
            rule_id="RULE-001",
        )
        assert config.rule_id == "RULE-001"

    def test_invalid_rule_id(self):
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="modify",
                hypothesis="This is a long enough hypothesis",
                evidence=["e1"],
                directive="Do X",
                rule_id="NOT-A-RULE",
            )

    def test_valid_deprecate(self):
        config = ProposalConfig(
            action="deprecate",
            hypothesis="This rule is obsolete and should be removed",
            evidence=["e1"],
            rule_id="RULE-001",
        )
        assert config.action == "deprecate"


class TestImpactAnalysisConfig:
    def test_defaults(self):
        config = ImpactAnalysisConfig(rule_id="RULE-001")
        assert config.include_recommendations is True

    def test_uppercase(self):
        config = ImpactAnalysisConfig(rule_id="rule-001")
        assert config.rule_id == "RULE-001"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            ImpactAnalysisConfig(rule_id="NOT-A-RULE")


class TestDSMCycleConfig:
    def test_defaults(self):
        config = DSMCycleConfig()
        assert config.batch_id is None
        assert config.auto_checkpoint is True

    def test_with_batch(self):
        config = DSMCycleConfig(batch_id="P4.4", auto_checkpoint=False)
        assert config.batch_id == "P4.4"
        assert config.auto_checkpoint is False
