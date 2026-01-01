"""
Rule Impact Analysis Functions (GAP-FILE-006)
==============================================
Rule impact analysis for P9.4.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

from typing import Dict, List, Any


def get_rule_dependencies(rule_id: str) -> List[str]:
    """
    Get rules that this rule depends on.

    Args:
        rule_id: Rule ID to get dependencies for

    Returns:
        List of dependency rule IDs
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        deps = client.get_rule_dependencies(rule_id)
        return deps if deps else []
    finally:
        client.close()


def get_rule_dependents(rule_id: str) -> List[str]:
    """
    Get rules that depend on this rule.

    Args:
        rule_id: Rule ID to get dependents for

    Returns:
        List of dependent rule IDs
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        dependents = client.get_rules_depending_on(rule_id)
        return dependents if dependents else []
    finally:
        client.close()


def get_rule_conflicts() -> List[Dict[str, Any]]:
    """
    Get all conflicting rule pairs.

    Returns:
        List of conflict dicts with rule1_id, rule2_id, reason
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        conflicts = client.find_conflicts()
        return conflicts if conflicts else []
    finally:
        client.close()


def build_dependency_graph(rules: List[Dict]) -> Dict[str, Any]:
    """
    Build a complete dependency graph from all rules.

    Pure function: transforms rules list into graph structure.

    Args:
        rules: List of rule dicts

    Returns:
        Graph structure with nodes and edges for visualization
    """
    nodes = []
    edges = []

    # Build nodes from rules
    for rule in rules:
        rule_id = rule.get('id') or rule.get('rule_id')
        if rule_id:
            nodes.append({
                'id': rule_id,
                'label': rule.get('name') or rule.get('title') or rule_id,
                'status': rule.get('status', 'UNKNOWN'),
                'category': rule.get('category', 'unknown'),
                'priority': rule.get('priority', 'MEDIUM'),
            })

    # Build edges from dependencies
    for rule in rules:
        rule_id = rule.get('id') or rule.get('rule_id')
        if rule_id:
            deps = get_rule_dependencies(rule_id)
            for dep_id in deps:
                edges.append({
                    'source': rule_id,
                    'target': dep_id,
                    'type': 'depends_on',
                })

    # Add conflict edges
    conflicts = get_rule_conflicts()
    for conflict in conflicts:
        if isinstance(conflict, dict):
            edges.append({
                'source': conflict.get('rule1_id') or conflict.get('rule1'),
                'target': conflict.get('rule2_id') or conflict.get('rule2'),
                'type': 'conflicts_with',
                'reason': conflict.get('reason', ''),
            })

    return {
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'dependency_edges': len([e for e in edges if e['type'] == 'depends_on']),
            'conflict_edges': len([e for e in edges if e['type'] == 'conflicts_with']),
        }
    }


def calculate_rule_impact(rule_id: str, rules: List[Dict]) -> Dict[str, Any]:
    """
    Calculate the impact of changing or removing a rule.

    Pure function: analyzes graph to determine impact.

    Args:
        rule_id: Rule ID to analyze
        rules: All rules for context

    Returns:
        Impact analysis with affected rules, risk level, etc.
    """
    # Get direct dependents (rules that depend on this rule)
    direct_dependents = get_rule_dependents(rule_id)

    # Get transitive dependents (rules that depend on dependents)
    all_affected = set(direct_dependents)
    to_check = list(direct_dependents)

    while to_check:
        current = to_check.pop(0)
        deps = get_rule_dependents(current)
        for dep in deps:
            if dep not in all_affected:
                all_affected.add(dep)
                to_check.append(dep)

    # Get the rule's own dependencies
    dependencies = get_rule_dependencies(rule_id)

    # Calculate risk level based on impact
    total_affected = len(all_affected)
    if total_affected == 0:
        risk_level = 'LOW'
        risk_score = 0.1
    elif total_affected <= 2:
        risk_level = 'MEDIUM'
        risk_score = 0.4
    elif total_affected <= 5:
        risk_level = 'HIGH'
        risk_score = 0.7
    else:
        risk_level = 'CRITICAL'
        risk_score = 0.9

    # Check if any affected rules are CRITICAL priority
    affected_rules_data = [r for r in rules if (r.get('id') or r.get('rule_id')) in all_affected]
    critical_affected = [r for r in affected_rules_data if r.get('priority') == 'CRITICAL']
    if critical_affected:
        risk_level = 'CRITICAL'
        risk_score = 1.0

    return {
        'rule_id': rule_id,
        'dependencies': dependencies,
        'direct_dependents': direct_dependents,
        'all_affected': list(all_affected),
        'total_affected': total_affected,
        'risk_level': risk_level,
        'risk_score': risk_score,
        'critical_rules_affected': [r.get('id') or r.get('rule_id') for r in critical_affected],
        'recommendation': _get_impact_recommendation(risk_level, total_affected),
    }


def _get_impact_recommendation(risk_level: str, total_affected: int) -> str:
    """Get recommendation based on impact analysis."""
    if risk_level == 'CRITICAL':
        return "HALT: This change affects critical rules. Requires full governance review."
    elif risk_level == 'HIGH':
        return f"CAUTION: {total_affected} rules affected. Consider phased rollout."
    elif risk_level == 'MEDIUM':
        return f"PROCEED WITH CARE: {total_affected} rules will need updates."
    else:
        return "SAFE: Minimal impact. Standard change process applies."


def generate_mermaid_graph(graph: Dict[str, Any]) -> str:
    """
    Generate Mermaid diagram syntax from graph structure.

    Pure function: transforms graph to Mermaid string.

    Args:
        graph: Graph dict with nodes and edges

    Returns:
        Mermaid diagram string
    """
    lines = ["graph TD"]

    # Add nodes with styling
    for node in graph.get('nodes', []):
        node_id = node['id'].replace('-', '_')
        label = node.get('label', node['id'])
        status = node.get('status', 'UNKNOWN')

        # Style based on status
        if status == 'ACTIVE':
            style = f'{node_id}["{label}"]:::active'
        elif status == 'DEPRECATED':
            style = f'{node_id}["{label}"]:::deprecated'
        else:
            style = f'{node_id}["{label}"]:::draft'

        lines.append(f"    {style}")

    # Add edges
    for edge in graph.get('edges', []):
        source = edge['source'].replace('-', '_')
        target = edge['target'].replace('-', '_')
        edge_type = edge.get('type', 'depends_on')

        if edge_type == 'depends_on':
            lines.append(f"    {source} --> {target}")
        elif edge_type == 'conflicts_with':
            lines.append(f"    {source} -.- {target}")

    # Add style definitions
    lines.append("")
    lines.append("    classDef active fill:#4CAF50,stroke:#2E7D32,color:#fff")
    lines.append("    classDef draft fill:#9E9E9E,stroke:#616161,color:#fff")
    lines.append("    classDef deprecated fill:#F44336,stroke:#C62828,color:#fff")

    return "\n".join(lines)
