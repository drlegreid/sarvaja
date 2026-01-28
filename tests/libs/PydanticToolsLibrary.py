"""
Robot Framework Library for Pydantic AI Type-Safe Governance Tools Tests.

Per RULE-004: Exploratory Testing & Executable Specification
Per RULE-017: Type-Safe Tool Development
Migrated from tests/test_pydantic_tools.py
"""
from robot.api.deco import keyword


class PydanticToolsLibrary:
    """Library for testing Pydantic governance tools."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Input Model Validation Tests
    # =============================================================================

    @keyword("Rule Query Config Exists")
    def rule_query_config_exists(self):
        """RuleQueryConfig class exists."""
        try:
            from governance.pydantic_tools import RuleQueryConfig
            return {"exists": RuleQueryConfig is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Query Config With Defaults")
    def rule_query_config_with_defaults(self):
        """RuleQueryConfig works with defaults."""
        try:
            from governance.pydantic_tools import RuleQueryConfig
            config = RuleQueryConfig()
            return {
                "category_none": config.category is None,
                "status_none": config.status is None,
                "priority_none": config.priority is None,
                "include_deps_false": config.include_dependencies is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Query Config With Values")
    def rule_query_config_with_values(self):
        """RuleQueryConfig accepts valid values."""
        try:
            from governance.pydantic_tools import RuleQueryConfig
            config = RuleQueryConfig(
                category="governance",
                status="ACTIVE",
                priority="HIGH"
            )
            return {
                "category_correct": config.category == "governance",
                "status_correct": config.status == "ACTIVE",
                "priority_correct": config.priority == "HIGH"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Query Config Validates Status")
    def rule_query_config_validates_status(self):
        """RuleQueryConfig validates status literal."""
        try:
            from governance.pydantic_tools import RuleQueryConfig
            from pydantic import ValidationError

            # Valid status
            config = RuleQueryConfig(status="ACTIVE")
            valid_works = config.status == "ACTIVE"

            # Invalid status
            rejects_invalid = False
            try:
                RuleQueryConfig(status="INVALID")
            except ValidationError:
                rejects_invalid = True

            return {
                "valid_works": valid_works,
                "rejects_invalid": rejects_invalid
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dependency Config Exists")
    def dependency_config_exists(self):
        """DependencyConfig class exists."""
        try:
            from governance.pydantic_tools import DependencyConfig
            return {"exists": DependencyConfig is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dependency Config Requires Rule Id")
    def dependency_config_requires_rule_id(self):
        """DependencyConfig requires rule_id."""
        try:
            from governance.pydantic_tools import DependencyConfig
            from pydantic import ValidationError

            requires = False
            try:
                DependencyConfig()
            except ValidationError:
                requires = True

            return {"requires_rule_id": requires}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dependency Config Validates Rule Id")
    def dependency_config_validates_rule_id(self):
        """DependencyConfig validates rule_id format."""
        try:
            from governance.pydantic_tools import DependencyConfig
            from pydantic import ValidationError

            # Valid
            config = DependencyConfig(rule_id="RULE-001")
            valid_works = config.rule_id == "RULE-001"

            # Invalid
            rejects_invalid = False
            try:
                DependencyConfig(rule_id="invalid-id")
            except ValidationError:
                rejects_invalid = True

            return {
                "valid_works": valid_works,
                "rejects_invalid": rejects_invalid
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Dependency Config Uppercases Rule Id")
    def dependency_config_uppercases_rule_id(self):
        """DependencyConfig uppercases rule_id."""
        try:
            from governance.pydantic_tools import DependencyConfig
            config = DependencyConfig(rule_id="rule-001")
            return {"uppercased": config.rule_id == "RULE-001"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Output Models Tests
    # =============================================================================

    @keyword("Rule Info Model Works")
    def rule_info_model_works(self):
        """RuleInfo model works."""
        try:
            from governance.pydantic_tools import RuleInfo
            info = RuleInfo(
                rule_id="RULE-001",
                name="Session Evidence",
                category="governance",
                priority="CRITICAL",
                status="ACTIVE"
            )
            return {
                "rule_id_correct": info.rule_id == "RULE-001",
                "dependencies_empty": info.dependencies == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Query Result Model Works")
    def rule_query_result_model_works(self):
        """RuleQueryResult model works."""
        try:
            from governance.pydantic_tools import RuleQueryResult
            result = RuleQueryResult(
                success=True,
                total_count=10,
                filtered_count=5,
                query_time_ms=12.5
            )
            return {
                "success": result.success is True,
                "rules_empty": result.rules == [],
                "error_none": result.error is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Score Result Validates Range")
    def trust_score_result_validates_range(self):
        """TrustScoreResult validates 0-1 range."""
        try:
            from governance.pydantic_tools import TrustScoreResult
            from pydantic import ValidationError

            # Valid
            result = TrustScoreResult(
                success=True,
                agent_id="AGENT-001",
                trust_score=0.85,
                vote_weight=1.0
            )
            valid_works = result.trust_score == 0.85

            # Invalid range
            rejects_over_1 = False
            try:
                TrustScoreResult(
                    success=True,
                    agent_id="AGENT-001",
                    trust_score=1.5,
                    vote_weight=1.0
                )
            except ValidationError:
                rejects_over_1 = True

            return {
                "valid_works": valid_works,
                "rejects_over_1": rejects_over_1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # MCP Wrapper Tests
    # =============================================================================

    @keyword("Query Rules MCP Exists")
    def query_rules_mcp_exists(self):
        """query_rules_mcp function exists."""
        try:
            from governance.pydantic_tools import query_rules_mcp
            return {"exists": callable(query_rules_mcp)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Analyze Dependencies MCP Exists")
    def analyze_dependencies_mcp_exists(self):
        """analyze_dependencies_mcp function exists."""
        try:
            from governance.pydantic_tools import analyze_dependencies_mcp
            return {"exists": callable(analyze_dependencies_mcp)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Calculate Trust Score MCP Exists")
    def calculate_trust_score_mcp_exists(self):
        """calculate_trust_score_mcp function exists."""
        try:
            from governance.pydantic_tools import calculate_trust_score_mcp
            return {"exists": callable(calculate_trust_score_mcp)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Analyze Impact MCP Exists")
    def analyze_impact_mcp_exists(self):
        """analyze_impact_mcp function exists."""
        try:
            from governance.pydantic_tools import analyze_impact_mcp
            return {"exists": callable(analyze_impact_mcp)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Check MCP Exists")
    def health_check_mcp_exists(self):
        """health_check_mcp function exists."""
        try:
            from governance.pydantic_tools import health_check_mcp
            return {"exists": callable(health_check_mcp)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

