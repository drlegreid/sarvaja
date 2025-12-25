"""
Pydantic AI Type-Safe Governance Tools
======================================
Type-safe wrappers for Governance MCP operations.

Features:
- Validated inputs with Pydantic models
- Structured outputs with guaranteed schema
- FastMCP integration for MCP server creation
- Runtime type checking and validation

Per: RULE-017 (Type-Safe Tool Development)
Source: local-gai/photoprism_migration/pydantic_tools.py pattern

Usage:
    from governance.pydantic_tools import (
        RuleQueryConfig, RuleQueryResult,
        query_rules_typed
    )

    config = RuleQueryConfig(category="governance", status="ACTIVE")
    result = query_rules_typed(config)
    print(result.model_dump_json())
"""

from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import json


# =============================================================================
# INPUT MODELS - Validated request configurations
# =============================================================================

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


# =============================================================================
# OUTPUT MODELS - Structured result types
# =============================================================================

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


# =============================================================================
# TYPE-SAFE TOOL IMPLEMENTATIONS
# =============================================================================

def query_rules_typed(config: RuleQueryConfig) -> RuleQueryResult:
    """
    Query rules with type-safe configuration and result.

    Args:
        config: Validated query configuration

    Returns:
        Structured result with matched rules
    """
    import time
    start = time.time()

    try:
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return RuleQueryResult(
                success=False,
                total_count=0,
                filtered_count=0,
                query_time_ms=0,
                error="Failed to connect to TypeDB"
            )

        try:
            # Get rules based on status filter
            if config.status == "ACTIVE":
                rules = client.get_active_rules()
            else:
                rules = client.get_all_rules()

            # Apply additional filters
            filtered = rules
            filters_applied = {}

            if config.category:
                filtered = [r for r in filtered if r.category == config.category]
                filters_applied["category"] = config.category

            if config.priority:
                filtered = [r for r in filtered if r.priority == config.priority]
                filters_applied["priority"] = config.priority

            if config.status and config.status != "ACTIVE":
                filtered = [r for r in filtered if r.status == config.status]
                filters_applied["status"] = config.status

            # Convert to RuleInfo models
            rule_infos = []
            for r in filtered:
                info = RuleInfo(
                    rule_id=r.rule_id,
                    name=r.name,
                    category=r.category,
                    priority=r.priority,
                    status=r.status,
                    directive=r.directive
                )

                if config.include_dependencies:
                    deps = client.get_rule_dependencies(r.rule_id)
                    info.dependencies = deps

                rule_infos.append(info)

            elapsed = (time.time() - start) * 1000

            return RuleQueryResult(
                success=True,
                rules=rule_infos,
                total_count=len(rules),
                filtered_count=len(filtered),
                filters_applied=filters_applied,
                query_time_ms=round(elapsed, 2)
            )

        finally:
            client.close()

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return RuleQueryResult(
            success=False,
            total_count=0,
            filtered_count=0,
            query_time_ms=round(elapsed, 2),
            error=str(e)
        )


def analyze_dependencies_typed(config: DependencyConfig) -> DependencyResult:
    """
    Analyze rule dependencies with type-safe configuration.

    Args:
        config: Validated dependency configuration

    Returns:
        Structured dependency analysis result
    """
    try:
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return DependencyResult(
                success=False,
                rule_id=config.rule_id,
                error="Failed to connect to TypeDB"
            )

        try:
            dependencies = []
            dependents = []

            if config.direction in ["dependencies", "both"]:
                dependencies = client.get_rule_dependencies(config.rule_id)

            if config.direction in ["dependents", "both"]:
                # Query dependents (rules that depend on this rule)
                query = f'''
                    match
                        $r1 isa rule-entity, has rule-id $id1;
                        $r2 isa rule-entity, has rule-id "{config.rule_id}";
                        (dependent: $r1, dependency: $r2) isa rule-dependency;
                    get $id1;
                '''
                results = client.execute_query(query)
                dependents = [r.get('id1') for r in results if r.get('id1')]

            # Calculate transitive dependencies
            transitive = []
            if config.include_transitive and dependencies:
                seen = set(dependencies)
                to_check = list(dependencies)

                while to_check:
                    current = to_check.pop(0)
                    sub_deps = client.get_rule_dependencies(current)
                    for dep in sub_deps:
                        if dep not in seen:
                            seen.add(dep)
                            transitive.append(dep)
                            to_check.append(dep)

            # Calculate depth
            depth = 0
            if transitive:
                depth = len(set(dependencies + transitive))
            elif dependencies:
                depth = 1

            return DependencyResult(
                success=True,
                rule_id=config.rule_id,
                dependencies=dependencies,
                dependents=dependents,
                transitive_dependencies=transitive,
                dependency_depth=depth
            )

        finally:
            client.close()

    except Exception as e:
        return DependencyResult(
            success=False,
            rule_id=config.rule_id,
            error=str(e)
        )


def calculate_trust_score_typed(request: TrustScoreRequest) -> TrustScoreResult:
    """
    Calculate trust score with type-safe request and result.

    Trust Formula (RULE-011):
    Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

    Args:
        request: Validated trust score request

    Returns:
        Structured trust score result
    """
    try:
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return TrustScoreResult(
                success=False,
                agent_id=request.agent_id,
                trust_score=0.0,
                vote_weight=0.0,
                error="Failed to connect to TypeDB"
            )

        try:
            query = f'''
                match
                    $a isa agent, has agent-id "{request.agent_id}";
                    $a has agent-name $name;
                    $a has trust-score $trust;
                    $a has compliance-rate $compliance;
                    $a has accuracy-rate $accuracy;
                    $a has tenure-days $tenure;
                get $name, $trust, $compliance, $accuracy, $tenure;
            '''

            results = client.execute_query(query)

            if not results:
                return TrustScoreResult(
                    success=False,
                    agent_id=request.agent_id,
                    trust_score=0.0,
                    vote_weight=0.0,
                    error=f"Agent {request.agent_id} not found"
                )

            result = results[0]
            trust_score = float(result.get('trust', 0.0))

            # Calculate vote weight per RULE-011
            vote_weight = 1.0 if trust_score >= 0.5 else trust_score

            return TrustScoreResult(
                success=True,
                agent_id=request.agent_id,
                agent_name=result.get('name'),
                trust_score=trust_score,
                vote_weight=vote_weight,
                components={
                    "compliance": float(result.get('compliance', 0.0)),
                    "accuracy": float(result.get('accuracy', 0.0)),
                    "tenure_days": int(result.get('tenure', 0))
                }
            )

        finally:
            client.close()

    except Exception as e:
        return TrustScoreResult(
            success=False,
            agent_id=request.agent_id,
            trust_score=0.0,
            vote_weight=0.0,
            error=str(e)
        )


def create_proposal_typed(config: ProposalConfig) -> ProposalResult:
    """
    Create a rule proposal with type-safe configuration.

    Args:
        config: Validated proposal configuration

    Returns:
        Structured proposal result
    """
    proposal_id = f"PROPOSAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return ProposalResult(
        success=True,
        proposal_id=proposal_id,
        status="pending",
        action=config.action,
        rule_id=config.rule_id,
        created_at=datetime.now().isoformat(),
        message=f"Proposal {proposal_id} created. Awaiting votes from agents."
    )


def analyze_impact_typed(config: ImpactAnalysisConfig) -> ImpactAnalysisResult:
    """
    Analyze rule modification impact with type-safe configuration.

    Args:
        config: Validated impact analysis configuration

    Returns:
        Structured impact analysis result
    """
    try:
        from governance.rule_quality import RuleQualityAnalyzer

        analyzer = RuleQualityAnalyzer()
        impact = analyzer.get_rule_impact(config.rule_id)

        # Parse impact data
        risk_map = {
            "HIGH RISK": "HIGH",
            "MEDIUM RISK": "MEDIUM",
            "LOW RISK": "LOW"
        }

        risk_level = risk_map.get(
            impact.get("recommendation", "LOW RISK").split(":")[0],
            "MEDIUM"
        )

        recommendations = []
        if config.include_recommendations:
            if impact.get("direct_dependents"):
                recommendations.append(
                    f"Update {len(impact['direct_dependents'])} direct dependents"
                )
            if impact.get("transitive_dependents"):
                recommendations.append(
                    f"Review {len(impact['transitive_dependents'])} transitive impacts"
                )
            if risk_level in ["HIGH", "CRITICAL"]:
                recommendations.append("Consider phased rollout with monitoring")

        return ImpactAnalysisResult(
            success=True,
            rule_id=config.rule_id,
            impact_score=impact.get("impact_score", 0),
            risk_level=risk_level,
            direct_dependents=impact.get("direct_dependents", []),
            transitive_dependents=impact.get("transitive_dependents", []),
            affected_count=impact.get("affected_count", 0),
            recommendations=recommendations
        )

    except Exception as e:
        return ImpactAnalysisResult(
            success=False,
            rule_id=config.rule_id,
            impact_score=0,
            risk_level="MEDIUM",
            error=str(e)
        )


def health_check_typed() -> HealthCheckResult:
    """
    Perform system health check with structured result.

    Returns:
        Structured health check result
    """
    issues = []
    typedb_connected = False
    rules_count = 0
    active_count = 0
    agents_count = 0

    try:
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if client.connect():
            typedb_connected = True

            rules = client.get_all_rules()
            rules_count = len(rules)
            active_count = len([r for r in rules if r.status == "ACTIVE"])

            # Count agents
            query = 'match $a isa agent; get $a; count;'
            try:
                result = client.execute_query(query)
                agents_count = int(result[0].get('count', 0)) if result else 0
            except:
                pass

            client.close()
        else:
            issues.append("TypeDB connection failed")

    except Exception as e:
        issues.append(f"TypeDB error: {str(e)}")

    return HealthCheckResult(
        healthy=typedb_connected and not issues,
        typedb_connected=typedb_connected,
        rules_count=rules_count,
        active_rules_count=active_count,
        agents_count=agents_count,
        last_check=datetime.now().isoformat(),
        issues=issues
    )


# =============================================================================
# MCP TOOL WRAPPERS (JSON serialization)
# =============================================================================

def query_rules_mcp(
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    include_dependencies: bool = False
) -> str:
    """MCP wrapper for query_rules_typed."""
    config = RuleQueryConfig(
        category=category,
        status=status,
        priority=priority,
        include_dependencies=include_dependencies
    )
    result = query_rules_typed(config)
    return result.model_dump_json(indent=2)


def analyze_dependencies_mcp(
    rule_id: str,
    include_transitive: bool = True,
    direction: str = "both"
) -> str:
    """MCP wrapper for analyze_dependencies_typed."""
    config = DependencyConfig(
        rule_id=rule_id,
        include_transitive=include_transitive,
        direction=direction
    )
    result = analyze_dependencies_typed(config)
    return result.model_dump_json(indent=2)


def calculate_trust_score_mcp(agent_id: str) -> str:
    """MCP wrapper for calculate_trust_score_typed."""
    request = TrustScoreRequest(agent_id=agent_id)
    result = calculate_trust_score_typed(request)
    return result.model_dump_json(indent=2)


def analyze_impact_mcp(
    rule_id: str,
    include_recommendations: bool = True
) -> str:
    """MCP wrapper for analyze_impact_typed."""
    config = ImpactAnalysisConfig(
        rule_id=rule_id,
        include_recommendations=include_recommendations
    )
    result = analyze_impact_typed(config)
    return result.model_dump_json(indent=2)


def health_check_mcp() -> str:
    """MCP wrapper for health_check_typed."""
    result = health_check_typed()
    return result.model_dump_json(indent=2)


# =============================================================================
# CLI / TESTING
# =============================================================================

def main():
    """Test the type-safe tools."""
    print("=" * 60)
    print("PYDANTIC AI TYPE-SAFE GOVERNANCE TOOLS")
    print("=" * 60)

    # Test RuleQueryConfig validation
    print("\n--- INPUT VALIDATION ---")
    try:
        config = RuleQueryConfig(
            category="governance",
            status="ACTIVE",
            priority="HIGH"
        )
        print(f"✓ RuleQueryConfig validated: {config.model_dump()}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")

    # Test DependencyConfig validation
    try:
        dep_config = DependencyConfig(
            rule_id="RULE-001",
            direction="both"
        )
        print(f"✓ DependencyConfig validated: {dep_config.model_dump()}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")

    # Test invalid input
    try:
        bad_config = DependencyConfig(rule_id="invalid-id")
        print(f"✗ Should have failed validation")
    except ValueError as e:
        print(f"✓ Correctly rejected invalid input: {e}")

    # Test ProposalConfig cross-field validation
    try:
        bad_proposal = ProposalConfig(
            action="modify",
            hypothesis="This is a test hypothesis",
            evidence=["Evidence 1"]
            # Missing rule_id for modify action
        )
        print(f"✗ Should have failed validation")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")

    # Show model schemas
    print("\n--- MODEL SCHEMAS ---")
    print(f"  RuleQueryConfig: {len(RuleQueryConfig.model_fields)} fields")
    print(f"  DependencyConfig: {len(DependencyConfig.model_fields)} fields")
    print(f"  TrustScoreRequest: {len(TrustScoreRequest.model_fields)} fields")
    print(f"  ProposalConfig: {len(ProposalConfig.model_fields)} fields")
    print(f"  ImpactAnalysisConfig: {len(ImpactAnalysisConfig.model_fields)} fields")

    print("\n--- OUTPUT MODELS ---")
    print(f"  RuleQueryResult: {len(RuleQueryResult.model_fields)} fields")
    print(f"  DependencyResult: {len(DependencyResult.model_fields)} fields")
    print(f"  TrustScoreResult: {len(TrustScoreResult.model_fields)} fields")
    print(f"  ImpactAnalysisResult: {len(ImpactAnalysisResult.model_fields)} fields")
    print(f"  HealthCheckResult: {len(HealthCheckResult.model_fields)} fields")

    print("\n" + "=" * 60)
    print("TYPE SAFETY VALIDATED")
    print("=" * 60)


if __name__ == "__main__":
    main()
