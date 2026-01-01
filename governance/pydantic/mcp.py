"""
Pydantic MCP Wrappers
=====================
MCP tool wrappers with JSON serialization.

Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

from typing import Optional

from .models import (
    RuleQueryConfig,
    DependencyConfig,
    TrustScoreRequest,
    ImpactAnalysisConfig,
)
from .tools import (
    query_rules_typed,
    analyze_dependencies_typed,
    calculate_trust_score_typed,
    analyze_impact_typed,
    health_check_typed,
)


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
