"""
Pydantic Output Models
======================
Structured result types for governance operations.

Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field


class RuleInfo(BaseModel):
    """Information about a single rule."""

    rule_id: str
    name: str
    category: str
    priority: str
    status: str
    directive: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)


class RuleQueryResult(BaseModel):
    """Result of a rule query operation."""

    success: bool
    rules: List[RuleInfo] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    filtered_count: int = Field(ge=0)
    filters_applied: Dict[str, str] = Field(default_factory=dict)
    query_time_ms: float = Field(ge=0)
    error: Optional[str] = None


class DependencyResult(BaseModel):
    """Result of dependency analysis."""

    success: bool
    rule_id: str
    dependencies: List[str] = Field(
        default_factory=list,
        description="Rules this rule depends on"
    )
    dependents: List[str] = Field(
        default_factory=list,
        description="Rules that depend on this rule"
    )
    transitive_dependencies: List[str] = Field(
        default_factory=list,
        description="All transitive dependencies (inferred)"
    )
    dependency_depth: int = Field(
        ge=0,
        description="Maximum depth of dependency chain"
    )
    error: Optional[str] = None


class TrustScoreResult(BaseModel):
    """Result of trust score calculation."""

    success: bool
    agent_id: str
    agent_name: Optional[str] = None
    trust_score: float = Field(ge=0.0, le=1.0)
    vote_weight: float = Field(ge=0.0, le=1.0)
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="Trust score components (compliance, accuracy, tenure)"
    )
    error: Optional[str] = None


class ProposalResult(BaseModel):
    """Result of creating a proposal."""

    success: bool
    proposal_id: Optional[str] = None
    status: Literal["pending", "approved", "rejected", "disputed", "error"] = "pending"
    action: str
    rule_id: Optional[str] = None
    created_at: Optional[str] = None
    message: str
    error: Optional[str] = None


class ImpactAnalysisResult(BaseModel):
    """Result of impact analysis."""

    success: bool
    rule_id: str
    impact_score: float = Field(
        ge=0, le=100,
        description="Impact score 0-100"
    )
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    direct_dependents: List[str] = Field(default_factory=list)
    transitive_dependents: List[str] = Field(default_factory=list)
    affected_count: int = Field(ge=0)
    recommendations: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class HealthCheckResult(BaseModel):
    """Result of system health check."""

    healthy: bool
    typedb_connected: bool
    chromadb_connected: bool = False
    rules_count: int = Field(ge=0)
    active_rules_count: int = Field(ge=0)
    agents_count: int = Field(ge=0)
    last_check: str
    issues: List[str] = Field(default_factory=list)
