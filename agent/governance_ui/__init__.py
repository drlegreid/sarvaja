"""
Governance UI Package
=====================
Pure data and state modules for Sim.ai Governance Dashboard.

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm

Package Structure:
    data_access.py  - Pure MCP data functions (no side effects)
    state.py        - Immutable state management (pure transforms)

Dashboard (view layer):
    agent/governance_dashboard.py - Trame UI (thin coordinator)

Usage:
    # Pure functions (this package)
    from agent.governance_ui import get_rules, get_initial_state, with_loading

    # Dashboard class
    from agent.governance_dashboard import GovernanceDashboard, create_governance_dashboard

    dashboard = create_governance_dashboard(port=8081)
    dashboard.run()
"""

# Data access (pure functions)
from .data_access import (
    call_mcp_tool,
    get_rules,
    get_rules_by_category,
    get_decisions,
    get_sessions,
    get_tasks,
    search_evidence,
    filter_rules_by_status,
    filter_rules_by_category,
    filter_rules_by_search,
    sort_rules,
    # Impact analysis (P9.4)
    get_rule_dependencies,
    get_rule_dependents,
    get_rule_conflicts,
    build_dependency_graph,
    calculate_rule_impact,
    generate_mermaid_graph,
    # Agent Trust Dashboard (P9.5 - RULE-011)
    get_agents,
    get_agent_trust_score,
    calculate_trust_score,
    get_agent_actions,
    get_proposals,
    get_proposal_votes,
    get_escalated_proposals,
    build_trust_leaderboard,
    calculate_consensus_score,
    get_governance_stats,
    # Real-time Monitoring (P9.6)
    get_rule_monitor,
    get_monitor_feed,
    get_monitor_alerts,
    get_monitor_stats,
    log_monitor_event,
    acknowledge_monitor_alert,
    get_top_monitored_rules,
    get_hourly_monitor_stats,
    # Journey Pattern Analyzer (P9.7)
    get_journey_analyzer,
    log_journey_question,
    get_recurring_questions,
    get_journey_patterns,
    get_knowledge_gaps,
    get_question_history,
)

# State management
from .state import (
    # Constants
    STATUS_COLORS,
    PRIORITY_COLORS,
    CATEGORY_ICONS,
    NAVIGATION_ITEMS,
    RULE_CATEGORIES,
    RULE_PRIORITIES,
    RULE_STATUSES,
    RISK_COLORS,
    TRUST_LEVEL_COLORS,
    PROPOSAL_STATUS_COLORS,
    EVENT_TYPE_COLORS,
    EVENT_TYPE_ICONS,
    SEVERITY_COLORS,
    # State factory
    get_initial_state,
    # Pure transforms
    with_loading,
    with_error,
    clear_error,
    with_status,
    with_active_view,
    with_selected_rule,
    with_rule_form,
    with_filters,
    with_sort,
    with_impact_analysis,
    with_graph_view,
    # Agent Trust (P9.5)
    with_agents,
    with_selected_agent,
    with_proposals,
    with_escalated_proposals,
    with_governance_stats,
    # UI helpers
    get_status_color,
    get_priority_color,
    get_category_icon,
    format_rule_card,
    get_risk_color,
    format_impact_summary,
    # Trust UI helpers (P9.5)
    get_trust_level,
    get_trust_level_color,
    get_proposal_status_color,
    format_agent_card,
    format_proposal_card,
    # Monitoring transforms (P9.6)
    with_monitor_feed,
    with_monitor_alerts,
    with_monitor_stats,
    with_monitor_filter,
    with_auto_refresh,
    with_top_rules,
    with_hourly_stats,
    # Monitoring UI helpers (P9.6)
    get_event_type_color,
    get_event_type_icon,
    get_severity_color,
    format_event_item,
    format_alert_item,
    # Journey Pattern Analyzer (P9.7)
    GAP_PRIORITY_COLORS,
    with_recurring_questions,
    with_journey_patterns,
    with_knowledge_gaps,
    with_question_history,
    get_gap_priority_color,
    format_recurring_question,
    format_knowledge_gap,
    format_journey_pattern,
)

__all__ = [
    # Data access
    'call_mcp_tool',
    'get_rules',
    'get_rules_by_category',
    'get_decisions',
    'get_sessions',
    'get_tasks',
    'search_evidence',
    'filter_rules_by_status',
    'filter_rules_by_category',
    'filter_rules_by_search',
    'sort_rules',
    # Impact analysis (P9.4)
    'get_rule_dependencies',
    'get_rule_dependents',
    'get_rule_conflicts',
    'build_dependency_graph',
    'calculate_rule_impact',
    'generate_mermaid_graph',
    # Agent Trust Dashboard (P9.5)
    'get_agents',
    'get_agent_trust_score',
    'calculate_trust_score',
    'get_agent_actions',
    'get_proposals',
    'get_proposal_votes',
    'get_escalated_proposals',
    'build_trust_leaderboard',
    'calculate_consensus_score',
    'get_governance_stats',
    # State
    'STATUS_COLORS',
    'PRIORITY_COLORS',
    'CATEGORY_ICONS',
    'NAVIGATION_ITEMS',
    'RULE_CATEGORIES',
    'RULE_PRIORITIES',
    'RULE_STATUSES',
    'RISK_COLORS',
    'TRUST_LEVEL_COLORS',
    'PROPOSAL_STATUS_COLORS',
    'get_initial_state',
    'with_loading',
    'with_error',
    'clear_error',
    'with_status',
    'with_active_view',
    'with_selected_rule',
    'with_rule_form',
    'with_filters',
    'with_sort',
    'with_impact_analysis',
    'with_graph_view',
    'with_agents',
    'with_selected_agent',
    'with_proposals',
    'with_escalated_proposals',
    'with_governance_stats',
    'get_status_color',
    'get_priority_color',
    'get_category_icon',
    'format_rule_card',
    'get_risk_color',
    'format_impact_summary',
    'get_trust_level',
    'get_trust_level_color',
    'get_proposal_status_color',
    'format_agent_card',
    'format_proposal_card',
    # Real-time Monitoring (P9.6)
    'get_rule_monitor',
    'get_monitor_feed',
    'get_monitor_alerts',
    'get_monitor_stats',
    'log_monitor_event',
    'acknowledge_monitor_alert',
    'get_top_monitored_rules',
    'get_hourly_monitor_stats',
    'EVENT_TYPE_COLORS',
    'EVENT_TYPE_ICONS',
    'SEVERITY_COLORS',
    'with_monitor_feed',
    'with_monitor_alerts',
    'with_monitor_stats',
    'with_monitor_filter',
    'with_auto_refresh',
    'with_top_rules',
    'with_hourly_stats',
    'get_event_type_color',
    'get_event_type_icon',
    'get_severity_color',
    'format_event_item',
    'format_alert_item',
    # Journey Pattern Analyzer (P9.7)
    'get_journey_analyzer',
    'log_journey_question',
    'get_recurring_questions',
    'get_journey_patterns',
    'get_knowledge_gaps',
    'get_question_history',
    'GAP_PRIORITY_COLORS',
    'with_recurring_questions',
    'with_journey_patterns',
    'with_knowledge_gaps',
    'with_question_history',
    'get_gap_priority_color',
    'format_recurring_question',
    'format_knowledge_gap',
    'format_journey_pattern',
]
