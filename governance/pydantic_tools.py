"""
Pydantic AI Type-Safe Governance Tools
======================================
Type-safe wrappers for Governance MCP operations.

**Refactored: 2024-12-28 per GAP-FILE-010**
Original: 807 lines -> Package with 8 modules (~550 lines total)

Modules extracted to governance/pydantic/:
- models/inputs.py: 6 input configuration models
- models/outputs.py: 7 output result models
- tools/rules.py: Rule query and dependency analysis
- tools/agents.py: Trust score calculation
- tools/proposals.py: Proposal creation
- tools/analysis.py: Impact analysis and health check
- mcp.py: MCP tool wrappers with JSON serialization

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

# Re-export everything from the package for backward compatibility
from governance.pydantic import (
    # Input models
    RuleQueryConfig,
    DependencyConfig,
    TrustScoreRequest,
    ProposalConfig,
    ImpactAnalysisConfig,
    DSMCycleConfig,
    # Output models
    RuleInfo,
    RuleQueryResult,
    DependencyResult,
    TrustScoreResult,
    ProposalResult,
    ImpactAnalysisResult,
    HealthCheckResult,
    # Type-safe tools
    query_rules_typed,
    analyze_dependencies_typed,
    calculate_trust_score_typed,
    create_proposal_typed,
    analyze_impact_typed,
    health_check_typed,
    # MCP wrappers
    query_rules_mcp,
    analyze_dependencies_mcp,
    calculate_trust_score_mcp,
    analyze_impact_mcp,
    health_check_mcp,
)

__all__ = [
    # Input models
    "RuleQueryConfig",
    "DependencyConfig",
    "TrustScoreRequest",
    "ProposalConfig",
    "ImpactAnalysisConfig",
    "DSMCycleConfig",
    # Output models
    "RuleInfo",
    "RuleQueryResult",
    "DependencyResult",
    "TrustScoreResult",
    "ProposalResult",
    "ImpactAnalysisResult",
    "HealthCheckResult",
    # Type-safe tools
    "query_rules_typed",
    "analyze_dependencies_typed",
    "calculate_trust_score_typed",
    "create_proposal_typed",
    "analyze_impact_typed",
    "health_check_typed",
    # MCP wrappers
    "query_rules_mcp",
    "analyze_dependencies_mcp",
    "calculate_trust_score_mcp",
    "analyze_impact_mcp",
    "health_check_mcp",
]


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
        print(f"  RuleQueryConfig validated: {config.model_dump()}")
    except Exception as e:
        print(f"  Validation failed: {e}")

    # Test DependencyConfig validation
    try:
        dep_config = DependencyConfig(
            rule_id="RULE-001",
            direction="both"
        )
        print(f"  DependencyConfig validated: {dep_config.model_dump()}")
    except Exception as e:
        print(f"  Validation failed: {e}")

    # Test invalid input
    try:
        bad_config = DependencyConfig(rule_id="invalid-id")
        print(f"  Should have failed validation")
    except ValueError as e:
        print(f"  Correctly rejected invalid input: {e}")

    # Test ProposalConfig cross-field validation
    try:
        bad_proposal = ProposalConfig(
            action="modify",
            hypothesis="This is a test hypothesis",
            evidence=["Evidence 1"]
            # Missing rule_id for modify action
        )
        print(f"  Should have failed validation")
    except ValueError as e:
        print(f"  Correctly rejected: {e}")

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
