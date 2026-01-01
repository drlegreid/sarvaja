"""
Rule Query Tools
================
Type-safe rule query and dependency analysis operations.

Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

import time
from ..models import (
    RuleQueryConfig,
    DependencyConfig,
    RuleInfo,
    RuleQueryResult,
    DependencyResult,
)


def query_rules_typed(config: RuleQueryConfig) -> RuleQueryResult:
    """
    Query rules with type-safe configuration and result.

    Args:
        config: Validated query configuration

    Returns:
        Structured result with matched rules
    """
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
