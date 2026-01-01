"""
Pydantic Input Models
=====================
Validated request configurations for governance operations.

Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field, field_validator


class RuleQueryConfig(BaseModel):
    """Configuration for querying rules."""

    category: Optional[str] = Field(
        default=None,
        description="Filter by category (governance, architecture, testing, devops, etc.)"
    )
    status: Optional[Literal["ACTIVE", "DRAFT", "DEPRECATED"]] = Field(
        default=None,
        description="Filter by rule status"
    )
    priority: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = Field(
        default=None,
        description="Filter by priority level"
    )
    include_dependencies: bool = Field(
        default=False,
        description="Include dependency information for each rule"
    )


class DependencyConfig(BaseModel):
    """Configuration for dependency analysis."""

    rule_id: str = Field(
        description="Rule ID to analyze (e.g., 'RULE-001')"
    )
    include_transitive: bool = Field(
        default=True,
        description="Include transitive dependencies (uses TypeDB inference)"
    )
    direction: Literal["dependencies", "dependents", "both"] = Field(
        default="both",
        description="Direction of dependency search"
    )

    @field_validator('rule_id')
    @classmethod
    def validate_rule_id(cls, v: str) -> str:
        v = v.upper()  # Uppercase first, then validate
        if not v.startswith("RULE-"):
            raise ValueError("Rule ID must start with 'RULE-'")
        return v


class TrustScoreRequest(BaseModel):
    """Request for agent trust score calculation."""

    agent_id: str = Field(
        description="Agent ID (e.g., 'AGENT-001')"
    )

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        v = v.upper()  # Uppercase first, then validate
        if not v.startswith("AGENT-"):
            raise ValueError("Agent ID must start with 'AGENT-'")
        return v


class ProposalConfig(BaseModel):
    """Configuration for creating a rule proposal."""

    action: Literal["create", "modify", "deprecate"] = Field(
        description="Type of proposal action"
    )
    hypothesis: str = Field(
        min_length=10,
        description="Why this change is needed (hypothesis)"
    )
    evidence: List[str] = Field(
        min_length=1,
        description="List of evidence items supporting the proposal"
    )
    rule_id: Optional[str] = Field(
        default=None,
        description="Required for modify/deprecate actions"
    )
    directive: Optional[str] = Field(
        default=None,
        description="Required for create/modify actions"
    )

    @field_validator('rule_id')
    @classmethod
    def validate_rule_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("RULE-"):
            raise ValueError("Rule ID must start with 'RULE-'")
        return v.upper() if v else v

    def model_post_init(self, __context) -> None:
        """Validate cross-field constraints."""
        if self.action in ["modify", "deprecate"] and not self.rule_id:
            raise ValueError(f"rule_id required for {self.action} action")
        if self.action in ["create", "modify"] and not self.directive:
            raise ValueError(f"directive required for {self.action} action")


class ImpactAnalysisConfig(BaseModel):
    """Configuration for rule impact analysis."""

    rule_id: str = Field(
        description="Rule ID to analyze impact for"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include remediation recommendations"
    )

    @field_validator('rule_id')
    @classmethod
    def validate_rule_id(cls, v: str) -> str:
        v = v.upper()  # Uppercase first, then validate
        if not v.startswith("RULE-"):
            raise ValueError("Rule ID must start with 'RULE-'")
        return v


class DSMCycleConfig(BaseModel):
    """Configuration for DSM cycle operations."""

    batch_id: Optional[str] = Field(
        default=None,
        description="Optional batch identifier (e.g., 'P4.4', 'RD-001')"
    )
    auto_checkpoint: bool = Field(
        default=True,
        description="Automatically checkpoint on phase changes"
    )
