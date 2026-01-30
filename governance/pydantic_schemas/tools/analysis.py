"""
Analysis Tools
==============
Type-safe impact analysis and health check operations.

Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

import logging
from datetime import datetime
from typing import Literal

logger = logging.getLogger(__name__)

from ..models import ImpactAnalysisConfig, ImpactAnalysisResult, HealthCheckResult


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

        risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = risk_map.get(
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
            query = 'match $a isa agent; select $a; count;'
            try:
                result = client.execute_query(query)
                agents_count = int(result[0].get('count', 0)) if result else 0
            except Exception as e:
                logger.debug(f"Failed to count agents: {e}")

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
