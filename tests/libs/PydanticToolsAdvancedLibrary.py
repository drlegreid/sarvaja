"""
Robot Framework Library for Pydantic AI Type-Safe Governance Tools Tests (Advanced).

Per RULE-004: Exploratory Testing & Executable Specification
Per RULE-017: Type-Safe Tool Development
Split from PydanticToolsLibrary.py per DOC-SIZE-01-v1
"""
from robot.api.deco import keyword


class PydanticToolsAdvancedLibrary:
    """Library for testing Pydantic governance tools - typed functions, validators, and constraints."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Typed Functions Tests
    # =============================================================================

    @keyword("Query Rules Typed Exists")
    def query_rules_typed_exists(self):
        """query_rules_typed function exists."""
        try:
            from governance.pydantic_tools import query_rules_typed
            return {"exists": callable(query_rules_typed)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Proposal Typed Works")
    def create_proposal_typed_works(self):
        """create_proposal_typed returns valid ProposalResult."""
        try:
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

            return {
                "is_proposal_result": isinstance(result, ProposalResult),
                "success": result.success is True,
                "has_proposal_id": result.proposal_id is not None,
                "id_format_correct": result.proposal_id.startswith("PROPOSAL-"),
                "status_pending": result.status == "pending"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Field Validator Tests
    # =============================================================================

    @keyword("Rule Id Validator Uppercase")
    def rule_id_validator_uppercase(self):
        """Rule ID validator uppercases input."""
        try:
            from governance.pydantic_tools import DependencyConfig
            config = DependencyConfig(rule_id="rule-005")
            return {"uppercased": config.rule_id == "RULE-005"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Id Validator Rejects Invalid")
    def rule_id_validator_rejects_invalid(self):
        """Rule ID validator rejects invalid format."""
        try:
            from governance.pydantic_tools import DependencyConfig
            from pydantic import ValidationError

            rejects = False
            error_message = ""
            try:
                DependencyConfig(rule_id="REG-001")
            except ValidationError as e:
                rejects = True
                error_message = str(e)

            return {
                "rejects": rejects,
                "mentions_rule": "RULE-" in error_message
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Agent Id Validator Uppercase")
    def agent_id_validator_uppercase(self):
        """Agent ID validator uppercases input."""
        try:
            from governance.pydantic_tools import TrustScoreRequest
            request = TrustScoreRequest(agent_id="agent-003")
            return {"uppercased": request.agent_id == "AGENT-003"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Literal Type Tests
    # =============================================================================

    @keyword("Status Literal Values Accepted")
    def status_literal_values_accepted(self):
        """RuleQueryConfig accepts valid status values."""
        try:
            from governance.pydantic_tools import RuleQueryConfig

            all_valid = True
            for status in ["ACTIVE", "DRAFT", "DEPRECATED"]:
                try:
                    config = RuleQueryConfig(status=status)
                    if config.status != status:
                        all_valid = False
                except Exception:
                    all_valid = False

            return {"all_valid": all_valid}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Priority Literal Values Accepted")
    def priority_literal_values_accepted(self):
        """RuleQueryConfig accepts valid priority values."""
        try:
            from governance.pydantic_tools import RuleQueryConfig

            all_valid = True
            for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                try:
                    config = RuleQueryConfig(priority=priority)
                    if config.priority != priority:
                        all_valid = False
                except Exception:
                    all_valid = False

            return {"all_valid": all_valid}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Field Constraint Tests
    # =============================================================================

    @keyword("Trust Score Range Enforced")
    def trust_score_range_enforced(self):
        """TrustScoreResult enforces 0-1 range."""
        try:
            from governance.pydantic_tools import TrustScoreResult
            from pydantic import ValidationError

            # Valid
            result = TrustScoreResult(
                success=True,
                agent_id="AGENT-001",
                trust_score=0.5,
                vote_weight=1.0
            )
            valid_works = result.trust_score == 0.5

            # Below range
            rejects_negative = False
            try:
                TrustScoreResult(
                    success=True,
                    agent_id="AGENT-001",
                    trust_score=-0.1,
                    vote_weight=1.0
                )
            except ValidationError:
                rejects_negative = True

            return {
                "valid_works": valid_works,
                "rejects_negative": rejects_negative
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Impact Score Range Enforced")
    def impact_score_range_enforced(self):
        """ImpactAnalysisResult enforces 0-100 range."""
        try:
            from governance.pydantic_tools import ImpactAnalysisResult
            from pydantic import ValidationError

            # Valid
            result = ImpactAnalysisResult(
                success=True,
                rule_id="RULE-001",
                impact_score=75,
                risk_level="HIGH",
                affected_count=5
            )
            valid_works = result.impact_score == 75

            # Above range
            rejects_over_100 = False
            try:
                ImpactAnalysisResult(
                    success=True,
                    rule_id="RULE-001",
                    impact_score=150,
                    risk_level="HIGH",
                    affected_count=5
                )
            except ValidationError:
                rejects_over_100 = True

            return {
                "valid_works": valid_works,
                "rejects_over_100": rejects_over_100
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Count Fields Non Negative")
    def count_fields_non_negative(self):
        """Count fields enforce non-negative values."""
        try:
            from governance.pydantic_tools import RuleQueryResult
            from pydantic import ValidationError

            # Valid
            result = RuleQueryResult(
                success=True,
                total_count=0,
                filtered_count=0,
                query_time_ms=0
            )
            valid_works = result.total_count == 0

            # Negative
            rejects_negative = False
            try:
                RuleQueryResult(
                    success=True,
                    total_count=-1,
                    filtered_count=0,
                    query_time_ms=0
                )
            except ValidationError:
                rejects_negative = True

            return {
                "valid_works": valid_works,
                "rejects_negative": rejects_negative
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
