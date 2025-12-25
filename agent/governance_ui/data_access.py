"""
Data Access Layer for Governance UI
====================================
Pure functions for MCP tool integration.

Per RULE-012: DSP Semantic Code Structure
Per FP Principles: Pure functions, no side effects
"""

import json
from typing import Dict, List, Any, Callable, Optional

# Import MCP tools
from governance.mcp_server import (
    governance_list_sessions,
    governance_get_session,
    governance_list_decisions,
    governance_get_decision,
    governance_list_tasks,
    governance_get_task_deps,
    governance_evidence_search,
    governance_query_rules,
)


# =============================================================================
# MCP TOOL REGISTRY (Immutable)
# =============================================================================

MCP_TOOLS: Dict[str, Callable] = {
    'governance_list_sessions': governance_list_sessions,
    'governance_get_session': governance_get_session,
    'governance_list_decisions': governance_list_decisions,
    'governance_get_decision': governance_get_decision,
    'governance_list_tasks': governance_list_tasks,
    'governance_get_task_deps': governance_get_task_deps,
    'governance_evidence_search': governance_evidence_search,
    'governance_query_rules': governance_query_rules,
}


# =============================================================================
# PURE FUNCTIONS (No side effects)
# =============================================================================

def call_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Call an MCP tool and parse JSON response.

    Pure function: same input -> same output, no side effects.

    Args:
        tool_name: Name of MCP tool
        **kwargs: Tool arguments

    Returns:
        Parsed JSON dict or error dict
    """
    tool_func = MCP_TOOLS.get(tool_name)
    if not tool_func:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        result = tool_func(**kwargs)
        return json.loads(result)
    except Exception as e:
        return {"error": str(e)}


def get_rules() -> List[Dict[str, Any]]:
    """
    Get all governance rules.

    Returns:
        List of rule dicts with rule_id, title, status, category
    """
    result = call_mcp_tool('governance_query_rules')

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('rules', []) if isinstance(result, dict) else []


def get_rules_by_category() -> Dict[str, List[Dict]]:
    """
    Group rules by category.

    Pure function: computes grouping from rules list.

    Returns:
        Dict of category -> rules list
    """
    rules = get_rules()
    grouped: Dict[str, List[Dict]] = {}

    for rule in rules:
        category = rule.get('category', 'unknown')
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(rule)

    return grouped


def get_decisions() -> List[Dict[str, Any]]:
    """
    Get all strategic decisions.

    Returns:
        List of decision dicts
    """
    result = call_mcp_tool('governance_list_decisions')

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('decisions', []) if isinstance(result, dict) else []


def get_sessions(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent sessions.

    Args:
        limit: Max number of sessions

    Returns:
        List of session dicts
    """
    result = call_mcp_tool('governance_list_sessions', limit=limit)

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('sessions', []) if isinstance(result, dict) else []


def get_tasks() -> List[Dict[str, Any]]:
    """
    Get R&D tasks.

    Returns:
        List of task dicts
    """
    result = call_mcp_tool('governance_list_tasks')

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('tasks', []) if isinstance(result, dict) else []


def search_evidence(query: str) -> List[Dict[str, Any]]:
    """
    Search evidence documents.

    Args:
        query: Search query

    Returns:
        List of matching evidence
    """
    result = call_mcp_tool('governance_evidence_search', query=query)

    if isinstance(result, list):
        return result
    if isinstance(result, dict) and 'error' in result:
        return []

    return result.get('results', []) if isinstance(result, dict) else []


# =============================================================================
# FILTER & TRANSFORM FUNCTIONS (Pure, composable)
# =============================================================================

def filter_rules_by_status(rules: List[Dict], status: Optional[str]) -> List[Dict]:
    """Filter rules by status (pure function)."""
    if not status:
        return rules
    return [r for r in rules if r.get('status') == status]


def filter_rules_by_category(rules: List[Dict], category: Optional[str]) -> List[Dict]:
    """Filter rules by category (pure function)."""
    if not category:
        return rules
    return [r for r in rules if r.get('category') == category]


def filter_rules_by_search(rules: List[Dict], query: str) -> List[Dict]:
    """Filter rules by text search (pure function)."""
    if not query:
        return rules
    query_lower = query.lower()
    return [
        r for r in rules
        if query_lower in (r.get('title', '') or '').lower()
        or query_lower in (r.get('rule_id', '') or r.get('id', '')).lower()
        or query_lower in (r.get('directive', '') or '').lower()
    ]


def sort_rules(rules: List[Dict], column: str, ascending: bool = True) -> List[Dict]:
    """Sort rules by column (pure function, returns new list)."""
    return sorted(
        rules,
        key=lambda r: r.get(column, ''),
        reverse=not ascending
    )


# =============================================================================
# RULE IMPACT ANALYSIS FUNCTIONS (P9.4)
# =============================================================================

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


# =============================================================================
# AGENT TRUST DASHBOARD FUNCTIONS (P9.5 - RULE-011)
# =============================================================================

# Trust score weights per RULE-011
TRUST_WEIGHTS = {
    'compliance': 0.4,
    'accuracy': 0.3,
    'consistency': 0.2,
    'tenure': 0.1,
}

# Max tenure days for normalization
MAX_TENURE_DAYS = 365


def get_agents() -> List[Dict[str, Any]]:
    """
    Get all registered agents.

    Returns:
        List of agent dicts with trust metrics
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        agents = client.list_agents()
        return agents if agents else []
    finally:
        client.close()


def get_agent_trust_score(agent_id: str) -> Optional[float]:
    """
    Get trust score for a specific agent.

    Args:
        agent_id: Agent ID

    Returns:
        Trust score (0.0-1.0) or None if not found
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return None
        trust = client.get_agent_trust(agent_id)
        return trust
    finally:
        client.close()


def calculate_trust_score(
    compliance_rate: float,
    accuracy_rate: float,
    consistency_rate: float,
    tenure_days: int
) -> float:
    """
    Calculate trust score using RULE-011 formula.

    Formula: Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

    Pure function: same inputs -> same output.

    Args:
        compliance_rate: 0.0-1.0 compliance percentage
        accuracy_rate: 0.0-1.0 accuracy percentage
        consistency_rate: 0.0-1.0 consistency percentage
        tenure_days: Days agent has been active

    Returns:
        Trust score 0.0-1.0
    """
    # Normalize tenure to 0-1 scale (365 days = 1.0)
    normalized_tenure = min(tenure_days / MAX_TENURE_DAYS, 1.0)

    # Calculate weighted sum
    trust = (
        (compliance_rate * TRUST_WEIGHTS['compliance']) +
        (accuracy_rate * TRUST_WEIGHTS['accuracy']) +
        (consistency_rate * TRUST_WEIGHTS['consistency']) +
        (normalized_tenure * TRUST_WEIGHTS['tenure'])
    )

    # Clamp to 0.0-1.0
    return max(0.0, min(1.0, trust))


def get_agent_actions(agent_id: str) -> List[Dict[str, Any]]:
    """
    Get action history for an agent.

    Args:
        agent_id: Agent ID

    Returns:
        List of action dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        actions = client.get_agent_actions(agent_id)
        return actions if actions else []
    finally:
        client.close()


def get_proposals(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get governance proposals.

    Args:
        status: Optional filter by status (pending, approved, rejected, disputed)

    Returns:
        List of proposal dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        proposals = client.list_proposals(status=status)
        return proposals if proposals else []
    finally:
        client.close()


def get_proposal_votes(proposal_id: str) -> List[Dict[str, Any]]:
    """
    Get votes for a proposal.

    Args:
        proposal_id: Proposal ID

    Returns:
        List of vote dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        votes = client.get_proposal_votes(proposal_id)
        return votes if votes else []
    finally:
        client.close()


def get_escalated_proposals() -> List[Dict[str, Any]]:
    """
    Get proposals that require human escalation.

    Returns:
        List of escalated proposal dicts
    """
    from governance.mcp_tools.common import get_typedb_client

    client = get_typedb_client()
    try:
        if not client.connect():
            return []
        escalated = client.get_escalated_proposals()
        return escalated if escalated else []
    finally:
        client.close()


def build_trust_leaderboard(agents: List[Dict]) -> List[Dict[str, Any]]:
    """
    Build trust leaderboard from agents list.

    Pure function: sorts and ranks agents by trust score.

    Args:
        agents: List of agent dicts

    Returns:
        Sorted and ranked leaderboard
    """
    # Sort by trust score descending
    sorted_agents = sorted(
        agents,
        key=lambda a: a.get('trust_score', 0.0),
        reverse=True
    )

    # Add rank and trust level
    leaderboard = []
    for i, agent in enumerate(sorted_agents, start=1):
        trust_score = agent.get('trust_score', 0.0)
        leaderboard.append({
            **agent,
            'rank': i,
            'trust_level': _get_trust_level(trust_score),
        })

    return leaderboard


def _get_trust_level(score: float) -> str:
    """Get trust level category from score."""
    if score >= 0.8:
        return 'HIGH'
    elif score >= 0.5:
        return 'MEDIUM'
    else:
        return 'LOW'


def calculate_consensus_score(votes: List[Dict]) -> float:
    """
    Calculate consensus score from weighted votes.

    Pure function: computes consensus from vote list.

    Args:
        votes: List of vote dicts with vote_value and vote_weight

    Returns:
        Consensus score 0.0-1.0 (1.0 = unanimous)
    """
    if not votes:
        return 0.0

    total_weight = 0.0
    approve_weight = 0.0
    reject_weight = 0.0

    for vote in votes:
        weight = vote.get('vote_weight', 1.0)
        value = vote.get('vote_value', 'abstain')
        total_weight += weight

        if value == 'approve':
            approve_weight += weight
        elif value == 'reject':
            reject_weight += weight

    if total_weight == 0:
        return 0.0

    # Consensus = majority weight / total weight
    majority_weight = max(approve_weight, reject_weight)
    return majority_weight / total_weight


def get_governance_stats(
    agents: List[Dict],
    proposals: List[Dict]
) -> Dict[str, Any]:
    """
    Calculate governance statistics.

    Pure function: aggregates metrics from agents and proposals.

    Args:
        agents: List of agent dicts
        proposals: List of proposal dicts

    Returns:
        Stats dict with governance metrics
    """
    # Calculate averages
    trust_scores = [a.get('trust_score', 0.0) for a in agents]
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0

    # Count proposals by status
    pending = len([p for p in proposals if p.get('proposal_status') == 'pending'])
    approved = len([p for p in proposals if p.get('proposal_status') == 'approved'])
    rejected = len([p for p in proposals if p.get('proposal_status') == 'rejected'])

    total_resolved = approved + rejected
    approval_rate = approved / total_resolved if total_resolved > 0 else 0.0

    return {
        'total_agents': len(agents),
        'avg_trust_score': avg_trust,
        'high_trust_agents': len([a for a in agents if a.get('trust_score', 0) >= 0.8]),
        'low_trust_agents': len([a for a in agents if a.get('trust_score', 0) < 0.5]),
        'total_proposals': len(proposals),
        'pending_proposals': pending,
        'approved_proposals': approved,
        'rejected_proposals': rejected,
        'approval_rate': approval_rate,
    }


# =============================================================================
# REAL-TIME MONITORING FUNCTIONS (P9.6)
# =============================================================================

# Singleton monitor instance
_monitor_instance = None


def get_rule_monitor():
    """
    Get or create singleton RuleMonitor instance.

    Returns:
        RuleMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        from agent.rule_monitor import create_rule_monitor
        _monitor_instance = create_rule_monitor()
    return _monitor_instance


def get_monitor_feed(limit: int = 50, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get monitoring event feed.

    Args:
        limit: Maximum events to return
        event_type: Optional filter by event type

    Returns:
        List of events (newest first)
    """
    monitor = get_rule_monitor()
    return monitor.get_feed(limit=limit, event_type=event_type)


def get_monitor_alerts(acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Get active monitoring alerts.

    Args:
        acknowledged: Optional filter by acknowledged status

    Returns:
        List of alerts
    """
    monitor = get_rule_monitor()
    return monitor.get_alerts(acknowledged=acknowledged)


def get_monitor_stats() -> Dict[str, Any]:
    """
    Get monitoring statistics.

    Returns:
        Stats dict with event counts, alerts, etc.
    """
    monitor = get_rule_monitor()
    return monitor.get_statistics()


def log_monitor_event(
    event_type: str,
    source: str,
    details: Dict[str, Any],
    severity: str = "INFO"
) -> Dict[str, Any]:
    """
    Log a governance event.

    Args:
        event_type: Type of event (rule_query, violation, rule_change, etc.)
        source: Event source (agent ID, user, etc.)
        details: Event details
        severity: Event severity (INFO, WARNING, CRITICAL)

    Returns:
        Event record
    """
    monitor = get_rule_monitor()
    return monitor.log_event(event_type, source, details, severity)


def acknowledge_monitor_alert(alert_id: str) -> Dict[str, Any]:
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge

    Returns:
        Result dict
    """
    monitor = get_rule_monitor()
    return monitor.acknowledge_alert(alert_id)


def get_top_monitored_rules(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most frequently accessed rules.

    Args:
        limit: Number of rules to return

    Returns:
        List of rules with access counts
    """
    monitor = get_rule_monitor()
    return monitor.get_top_rules(limit=limit)


def get_hourly_monitor_stats() -> Dict[str, Any]:
    """
    Get hourly monitoring statistics.

    Returns:
        Hourly stats dict
    """
    monitor = get_rule_monitor()
    return monitor.get_hourly_stats()


# =============================================================================
# JOURNEY PATTERN ANALYZER FUNCTIONS (P9.7)
# =============================================================================

# Singleton journey analyzer instance
_journey_analyzer_instance = None


def get_journey_analyzer():
    """
    Get or create singleton JourneyAnalyzer instance.

    Returns:
        JourneyAnalyzer instance
    """
    global _journey_analyzer_instance
    if _journey_analyzer_instance is None:
        from agent.journey_analyzer import create_journey_analyzer
        _journey_analyzer_instance = create_journey_analyzer()
    return _journey_analyzer_instance


def log_journey_question(
    question: str,
    source: str,
    category: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    answered: bool = True
) -> Dict[str, Any]:
    """
    Log a governance question for pattern analysis.

    Args:
        question: Question text
        source: Source of question (user, agent, etc.)
        category: Optional category tag
        context: Optional context dictionary
        answered: Whether the question was answered

    Returns:
        Question record with ID and recurrence info
    """
    analyzer = get_journey_analyzer()
    return analyzer.log_question(question, source, category, context, answered)


def get_recurring_questions(
    min_count: int = 2,
    days: Optional[int] = None,
    semantic_match: bool = False
) -> List[Dict[str, Any]]:
    """
    Get questions that recur frequently.

    Args:
        min_count: Minimum occurrences to be considered recurring
        days: Time window in days
        semantic_match: Whether to use semantic matching

    Returns:
        List of recurring questions with counts
    """
    analyzer = get_journey_analyzer()
    return analyzer.get_recurring_questions(min_count, days, semantic_match)


def get_journey_patterns() -> List[Dict[str, Any]]:
    """
    Detect patterns in question history.

    Returns:
        List of detected patterns with topics and suggestions
    """
    analyzer = get_journey_analyzer()
    return analyzer.detect_patterns()


def get_knowledge_gaps() -> List[Dict[str, Any]]:
    """
    Identify knowledge gaps from unanswered questions.

    Returns:
        List of knowledge gaps with frequency and topics
    """
    analyzer = get_journey_analyzer()
    return analyzer.get_knowledge_gaps()


def get_question_history(
    limit: int = 50,
    source: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get question history with optional filters.

    Args:
        limit: Maximum questions to return
        source: Filter by source
        category: Filter by category

    Returns:
        List of questions (newest first)
    """
    analyzer = get_journey_analyzer()
    return analyzer.get_question_history(limit, source, category)
