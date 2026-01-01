"""
Data Access Layer for Governance UI
====================================
Re-exports from data_access/ package for backward compatibility.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Modularized 1170→~35 lines (97% reduction)

Original monolith extracted to:
- data_access/core.py - MCP registry, core data access
- data_access/backlog.py - Agent task backlog (TODO-6)
- data_access/filters.py - Filter & transform pure functions
- data_access/impact.py - Rule impact analysis (P9.4)
- data_access/trust.py - Agent trust dashboard (P9.5, RULE-011)
- data_access/monitoring.py - Real-time monitoring (P9.6)
- data_access/journey.py - Journey pattern analyzer (P9.7)
- data_access/executive.py - Executive reports (GAP-UI-044)

Created: 2024-12-28
"""

# Re-export everything from the package
from agent.governance_ui.data_access import *  # noqa: F401, F403

# Explicit re-exports for IDE support
from agent.governance_ui.data_access import (
    # Core
    MCP_TOOLS,
    call_mcp_tool,
    get_rules,
    get_rules_by_category,
    get_decisions,
    get_sessions,
    get_tasks,
    search_evidence,
    # Backlog
    get_api_base_url,
    get_available_tasks,
    claim_task,
    complete_task,
    get_agent_tasks,
    # Session evidence (P11.5)
    link_evidence_to_session,
    get_session_evidence,
    # Filters
    filter_rules_by_status,
    filter_rules_by_category,
    filter_rules_by_search,
    sort_rules,
    # Impact
    get_rule_dependencies,
    get_rule_dependents,
    get_rule_conflicts,
    build_dependency_graph,
    calculate_rule_impact,
    generate_mermaid_graph,
    # Trust
    TRUST_WEIGHTS,
    MAX_TENURE_DAYS,
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
    # Monitoring
    get_rule_monitor,
    get_monitor_feed,
    get_monitor_alerts,
    get_monitor_stats,
    log_monitor_event,
    acknowledge_monitor_alert,
    get_top_monitored_rules,
    get_hourly_monitor_stats,
    # Journey
    get_journey_analyzer,
    log_journey_question,
    get_recurring_questions,
    get_journey_patterns,
    get_knowledge_gaps,
    get_question_history,
    # Executive
    get_executive_report,
)
