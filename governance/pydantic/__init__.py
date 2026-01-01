"""
Pydantic AI Type-Safe Governance Package
========================================
Type-safe wrappers for Governance MCP operations.

**Refactored: 2024-12-28 per GAP-FILE-010**
Original: 807 lines -> Package with 8 modules (~550 lines total)

Features:
- Validated inputs with Pydantic models
- Structured outputs with guaranteed schema
- FastMCP integration for MCP server creation
- Runtime type checking and validation

Per: RULE-017 (Type-Safe Tool Development)

Usage:
    from governance.pydantic import (
        RuleQueryConfig, RuleQueryResult,
        query_rules_typed
    )

    config = RuleQueryConfig(category="governance", status="ACTIVE")
    result = query_rules_typed(config)
    print(result.model_dump_json())
"""

# Input models
from .models import (
    RuleQueryConfig,
    DependencyConfig,
    TrustScoreRequest,
    ProposalConfig,
    ImpactAnalysisConfig,
    DSMCycleConfig,
)

# Output models
from .models import (
    RuleInfo,
    RuleQueryResult,
    DependencyResult,
    TrustScoreResult,
    ProposalResult,
    ImpactAnalysisResult,
    HealthCheckResult,
)

# Type-safe tools
from .tools import (
    query_rules_typed,
    analyze_dependencies_typed,
    calculate_trust_score_typed,
    create_proposal_typed,
    analyze_impact_typed,
    health_check_typed,
)

# MCP wrappers
from .mcp import (
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
