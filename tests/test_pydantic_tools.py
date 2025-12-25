"""
Tests for Pydantic AI Type-Safe Governance Tools (P4.4)

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: R&D-BACKLOG.md Phase 4.4, RULE-017 (Type-Safe Tool Development)
"""

import pytest
import json
from pydantic import ValidationError


class TestInputModelValidation:
    """Tests for input model validation."""

    def test_rule_query_config_exists(self):
        """RuleQueryConfig class exists."""
        from governance.pydantic_tools import RuleQueryConfig
        assert RuleQueryConfig is not None

    def test_rule_query_config_with_defaults(self):
        """RuleQueryConfig works with defaults."""
        from governance.pydantic_tools import RuleQueryConfig

        config = RuleQueryConfig()
        assert config.category is None
        assert config.status is None
        assert config.priority is None
        assert config.include_dependencies is False

    def test_rule_query_config_with_values(self):
        """RuleQueryConfig accepts valid values."""
        from governance.pydantic_tools import RuleQueryConfig

        config = RuleQueryConfig(
            category="governance",
            status="ACTIVE",
            priority="HIGH"
        )
        assert config.category == "governance"
        assert config.status == "ACTIVE"
        assert config.priority == "HIGH"

    def test_rule_query_config_status_literal(self):
        """RuleQueryConfig validates status literal."""
        from governance.pydantic_tools import RuleQueryConfig

        # Valid status
        config = RuleQueryConfig(status="ACTIVE")
        assert config.status == "ACTIVE"

        # Invalid status
        with pytest.raises(ValidationError):
            RuleQueryConfig(status="INVALID")

    def test_dependency_config_exists(self):
        """DependencyConfig class exists."""
        from governance.pydantic_tools import DependencyConfig
        assert DependencyConfig is not None

    def test_dependency_config_requires_rule_id(self):
        """DependencyConfig requires rule_id."""
        from governance.pydantic_tools import DependencyConfig

        with pytest.raises(ValidationError):
            DependencyConfig()

    def test_dependency_config_validates_rule_id(self):
        """DependencyConfig validates rule_id format."""
        from governance.pydantic_tools import DependencyConfig

        # Valid
        config = DependencyConfig(rule_id="RULE-001")
        assert config.rule_id == "RULE-001"

        # Invalid
        with pytest.raises(ValidationError):
            DependencyConfig(rule_id="invalid-id")

    def test_dependency_config_uppercase_rule_id(self):
        """DependencyConfig uppercases rule_id."""
        from governance.pydantic_tools import DependencyConfig

        config = DependencyConfig(rule_id="rule-001")
        assert config.rule_id == "RULE-001"

    def test_trust_score_request_validates_agent_id(self):
        """TrustScoreRequest validates agent_id format."""
        from governance.pydantic_tools import TrustScoreRequest

        # Valid
        request = TrustScoreRequest(agent_id="AGENT-001")
        assert request.agent_id == "AGENT-001"

        # Invalid
        with pytest.raises(ValidationError):
            TrustScoreRequest(agent_id="user-001")

    def test_proposal_config_cross_field_validation(self):
        """ProposalConfig validates cross-field constraints."""
        from governance.pydantic_tools import ProposalConfig

        # modify action requires rule_id
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="modify",
                hypothesis="This is a test hypothesis",
                evidence=["Evidence 1"]
            )

        # create action requires directive
        with pytest.raises(ValidationError):
            ProposalConfig(
                action="create",
                hypothesis="This is a test hypothesis",
                evidence=["Evidence 1"]
            )

    def test_proposal_config_valid(self):
        """ProposalConfig accepts valid configuration."""
        from governance.pydantic_tools import ProposalConfig

        config = ProposalConfig(
            action="create",
            hypothesis="This change is needed because...",
            evidence=["Evidence 1", "Evidence 2"],
            directive="Do this thing"
        )
        assert config.action == "create"
        assert len(config.evidence) == 2


class TestOutputModels:
    """Tests for output model structures."""

    def test_rule_info_model(self):
        """RuleInfo model works."""
        from governance.pydantic_tools import RuleInfo

        info = RuleInfo(
            rule_id="RULE-001",
            name="Session Evidence",
            category="governance",
            priority="CRITICAL",
            status="ACTIVE"
        )
        assert info.rule_id == "RULE-001"
        assert info.dependencies == []

    def test_rule_query_result_model(self):
        """RuleQueryResult model works."""
        from governance.pydantic_tools import RuleQueryResult

        result = RuleQueryResult(
            success=True,
            total_count=10,
            filtered_count=5,
            query_time_ms=12.5
        )
        assert result.success is True
        assert result.rules == []
        assert result.error is None

    def test_dependency_result_model(self):
        """DependencyResult model works."""
        from governance.pydantic_tools import DependencyResult

        result = DependencyResult(
            success=True,
            rule_id="RULE-001",
            dependencies=["RULE-002", "RULE-003"],
            dependency_depth=2
        )
        assert len(result.dependencies) == 2
        assert result.transitive_dependencies == []

    def test_trust_score_result_model(self):
        """TrustScoreResult model validates ranges."""
        from governance.pydantic_tools import TrustScoreResult

        result = TrustScoreResult(
            success=True,
            agent_id="AGENT-001",
            trust_score=0.85,
            vote_weight=1.0
        )
        assert result.trust_score == 0.85

        # Invalid range
        with pytest.raises(ValidationError):
            TrustScoreResult(
                success=True,
                agent_id="AGENT-001",
                trust_score=1.5,  # > 1.0
                vote_weight=1.0
            )

    def test_impact_analysis_result_model(self):
        """ImpactAnalysisResult model validates risk levels."""
        from governance.pydantic_tools import ImpactAnalysisResult

        result = ImpactAnalysisResult(
            success=True,
            rule_id="RULE-001",
            impact_score=75,
            risk_level="HIGH",
            affected_count=5
        )
        assert result.risk_level == "HIGH"

    def test_health_check_result_model(self):
        """HealthCheckResult model works."""
        from governance.pydantic_tools import HealthCheckResult

        result = HealthCheckResult(
            healthy=True,
            typedb_connected=True,
            rules_count=15,
            active_rules_count=14,
            agents_count=3,
            last_check="2024-12-24T12:00:00"
        )
        assert result.healthy is True
        assert result.issues == []


class TestModelSerialization:
    """Tests for model JSON serialization."""

    def test_rule_query_config_to_dict(self):
        """RuleQueryConfig serializes to dict."""
        from governance.pydantic_tools import RuleQueryConfig

        config = RuleQueryConfig(category="testing", status="ACTIVE")
        d = config.model_dump()

        assert isinstance(d, dict)
        assert d["category"] == "testing"
        assert d["status"] == "ACTIVE"

    def test_rule_query_result_to_json(self):
        """RuleQueryResult serializes to JSON."""
        from governance.pydantic_tools import RuleQueryResult, RuleInfo

        result = RuleQueryResult(
            success=True,
            rules=[
                RuleInfo(
                    rule_id="RULE-001",
                    name="Test",
                    category="test",
                    priority="HIGH",
                    status="ACTIVE"
                )
            ],
            total_count=1,
            filtered_count=1,
            query_time_ms=5.0
        )

        json_str = result.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["success"] is True
        assert len(parsed["rules"]) == 1
        assert parsed["rules"][0]["rule_id"] == "RULE-001"

    def test_dependency_result_to_json(self):
        """DependencyResult serializes to JSON."""
        from governance.pydantic_tools import DependencyResult

        result = DependencyResult(
            success=True,
            rule_id="RULE-001",
            dependencies=["RULE-002"],
            dependents=["RULE-003"],
            dependency_depth=1
        )

        json_str = result.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["rule_id"] == "RULE-001"
        assert "RULE-002" in parsed["dependencies"]


class TestMCPWrappers:
    """Tests for MCP wrapper functions."""

    def test_query_rules_mcp_exists(self):
        """query_rules_mcp function exists."""
        from governance.pydantic_tools import query_rules_mcp
        assert query_rules_mcp is not None
        assert callable(query_rules_mcp)

    def test_analyze_dependencies_mcp_exists(self):
        """analyze_dependencies_mcp function exists."""
        from governance.pydantic_tools import analyze_dependencies_mcp
        assert analyze_dependencies_mcp is not None
        assert callable(analyze_dependencies_mcp)

    def test_calculate_trust_score_mcp_exists(self):
        """calculate_trust_score_mcp function exists."""
        from governance.pydantic_tools import calculate_trust_score_mcp
        assert calculate_trust_score_mcp is not None
        assert callable(calculate_trust_score_mcp)

    def test_analyze_impact_mcp_exists(self):
        """analyze_impact_mcp function exists."""
        from governance.pydantic_tools import analyze_impact_mcp
        assert analyze_impact_mcp is not None
        assert callable(analyze_impact_mcp)

    def test_health_check_mcp_exists(self):
        """health_check_mcp function exists."""
        from governance.pydantic_tools import health_check_mcp
        assert health_check_mcp is not None
        assert callable(health_check_mcp)


class TestTypedFunctions:
    """Tests for type-safe function implementations."""

    def test_query_rules_typed_exists(self):
        """query_rules_typed function exists."""
        from governance.pydantic_tools import query_rules_typed
        assert query_rules_typed is not None
        assert callable(query_rules_typed)

    def test_analyze_dependencies_typed_exists(self):
        """analyze_dependencies_typed function exists."""
        from governance.pydantic_tools import analyze_dependencies_typed
        assert analyze_dependencies_typed is not None
        assert callable(analyze_dependencies_typed)

    def test_calculate_trust_score_typed_exists(self):
        """calculate_trust_score_typed function exists."""
        from governance.pydantic_tools import calculate_trust_score_typed
        assert calculate_trust_score_typed is not None
        assert callable(calculate_trust_score_typed)

    def test_create_proposal_typed_exists(self):
        """create_proposal_typed function exists."""
        from governance.pydantic_tools import create_proposal_typed
        assert create_proposal_typed is not None
        assert callable(create_proposal_typed)

    def test_create_proposal_typed_works(self):
        """create_proposal_typed returns valid ProposalResult."""
        from governance.pydantic_tools import (
            create_proposal_typed,
            ProposalConfig,
            ProposalResult
        )

        config = ProposalConfig(
            action="create",
            hypothesis="This is a test hypothesis for the proposal",
            evidence=["Evidence item 1"],
            directive="New directive"
        )

        result = create_proposal_typed(config)

        assert isinstance(result, ProposalResult)
        assert result.success is True
        assert result.proposal_id is not None
        assert result.proposal_id.startswith("PROPOSAL-")
        assert result.status == "pending"

    def test_analyze_impact_typed_exists(self):
        """analyze_impact_typed function exists."""
        from governance.pydantic_tools import analyze_impact_typed
        assert analyze_impact_typed is not None
        assert callable(analyze_impact_typed)

    def test_health_check_typed_exists(self):
        """health_check_typed function exists."""
        from governance.pydantic_tools import health_check_typed
        assert health_check_typed is not None
        assert callable(health_check_typed)


class TestFieldValidators:
    """Tests for Pydantic field validators."""

    def test_rule_id_validator_uppercase(self):
        """Rule ID validator uppercases input."""
        from governance.pydantic_tools import DependencyConfig

        config = DependencyConfig(rule_id="rule-005")
        assert config.rule_id == "RULE-005"

    def test_rule_id_validator_rejects_invalid(self):
        """Rule ID validator rejects invalid format."""
        from governance.pydantic_tools import DependencyConfig

        with pytest.raises(ValidationError) as exc_info:
            DependencyConfig(rule_id="REG-001")

        assert "must start with 'RULE-'" in str(exc_info.value)

    def test_agent_id_validator_uppercase(self):
        """Agent ID validator uppercases input."""
        from governance.pydantic_tools import TrustScoreRequest

        request = TrustScoreRequest(agent_id="agent-003")
        assert request.agent_id == "AGENT-003"

    def test_agent_id_validator_rejects_invalid(self):
        """Agent ID validator rejects invalid format."""
        from governance.pydantic_tools import TrustScoreRequest

        with pytest.raises(ValidationError) as exc_info:
            TrustScoreRequest(agent_id="USER-001")

        assert "must start with 'AGENT-'" in str(exc_info.value)

    def test_hypothesis_min_length(self):
        """ProposalConfig enforces hypothesis min length."""
        from governance.pydantic_tools import ProposalConfig

        with pytest.raises(ValidationError):
            ProposalConfig(
                action="create",
                hypothesis="Short",  # Too short (min 10)
                evidence=["Evidence"],
                directive="Do this"
            )

    def test_evidence_min_length(self):
        """ProposalConfig enforces evidence min length."""
        from governance.pydantic_tools import ProposalConfig

        with pytest.raises(ValidationError):
            ProposalConfig(
                action="create",
                hypothesis="This is a valid hypothesis",
                evidence=[],  # Empty list
                directive="Do this"
            )


class TestLiteralTypes:
    """Tests for Literal type constraints."""

    def test_status_literal_values(self):
        """RuleQueryConfig accepts valid status values."""
        from governance.pydantic_tools import RuleQueryConfig

        for status in ["ACTIVE", "DRAFT", "DEPRECATED"]:
            config = RuleQueryConfig(status=status)
            assert config.status == status

    def test_priority_literal_values(self):
        """RuleQueryConfig accepts valid priority values."""
        from governance.pydantic_tools import RuleQueryConfig

        for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            config = RuleQueryConfig(priority=priority)
            assert config.priority == priority

    def test_action_literal_values(self):
        """ProposalConfig accepts valid action values."""
        from governance.pydantic_tools import ProposalConfig

        # create action
        config = ProposalConfig(
            action="create",
            hypothesis="Valid hypothesis here",
            evidence=["Evidence 1"],
            directive="New directive"
        )
        assert config.action == "create"

    def test_direction_literal_values(self):
        """DependencyConfig accepts valid direction values."""
        from governance.pydantic_tools import DependencyConfig

        for direction in ["dependencies", "dependents", "both"]:
            config = DependencyConfig(rule_id="RULE-001", direction=direction)
            assert config.direction == direction

    def test_risk_level_literal_values(self):
        """ImpactAnalysisResult accepts valid risk levels."""
        from governance.pydantic_tools import ImpactAnalysisResult

        for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            result = ImpactAnalysisResult(
                success=True,
                rule_id="RULE-001",
                impact_score=50,
                risk_level=level,
                affected_count=3
            )
            assert result.risk_level == level


class TestFieldConstraints:
    """Tests for Field constraints (ge, le, min_length)."""

    def test_trust_score_range(self):
        """TrustScoreResult enforces 0-1 range for trust_score."""
        from governance.pydantic_tools import TrustScoreResult

        # Valid range
        result = TrustScoreResult(
            success=True,
            agent_id="AGENT-001",
            trust_score=0.5,
            vote_weight=1.0
        )
        assert result.trust_score == 0.5

        # Below range
        with pytest.raises(ValidationError):
            TrustScoreResult(
                success=True,
                agent_id="AGENT-001",
                trust_score=-0.1,
                vote_weight=1.0
            )

        # Above range
        with pytest.raises(ValidationError):
            TrustScoreResult(
                success=True,
                agent_id="AGENT-001",
                trust_score=1.1,
                vote_weight=1.0
            )

    def test_impact_score_range(self):
        """ImpactAnalysisResult enforces 0-100 range for impact_score."""
        from governance.pydantic_tools import ImpactAnalysisResult

        # Valid
        result = ImpactAnalysisResult(
            success=True,
            rule_id="RULE-001",
            impact_score=75,
            risk_level="HIGH",
            affected_count=5
        )
        assert result.impact_score == 75

        # Above range
        with pytest.raises(ValidationError):
            ImpactAnalysisResult(
                success=True,
                rule_id="RULE-001",
                impact_score=150,
                risk_level="HIGH",
                affected_count=5
            )

    def test_count_fields_non_negative(self):
        """Count fields enforce non-negative values."""
        from governance.pydantic_tools import RuleQueryResult

        # Valid
        result = RuleQueryResult(
            success=True,
            total_count=0,
            filtered_count=0,
            query_time_ms=0
        )
        assert result.total_count == 0

        # Negative
        with pytest.raises(ValidationError):
            RuleQueryResult(
                success=True,
                total_count=-1,
                filtered_count=0,
                query_time_ms=0
            )
