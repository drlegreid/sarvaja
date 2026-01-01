"""
Data Access Package (GAP-FILE-006)
==================================
Package exports for governance UI data access functions.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Modularized from data_access.py (1170→~60 lines per module)

Created: 2024-12-28

Modules:
- core.py: MCP registry, core data access (rules, decisions, sessions, tasks)
- backlog.py: Agent task backlog functions (TODO-6)
- filters.py: Filter & transform pure functions
- impact.py: Rule impact analysis (P9.4)
- trust.py: Agent trust dashboard (P9.5, RULE-011)
- monitoring.py: Real-time monitoring (P9.6)
- journey.py: Journey pattern analyzer (P9.7)
- executive.py: Executive reports (GAP-UI-044, RULE-029)
"""

# Core data access
from .core import (
    MCP_TOOLS,
    call_mcp_tool,
    get_rules,
    get_rules_by_category,
    get_decisions,
    get_sessions,
    get_tasks,
    search_evidence,
)

# Agent task backlog (TODO-6)
from .backlog import (
    get_api_base_url,
    get_available_tasks,
    claim_task,
    complete_task,
    get_agent_tasks,
    # Session evidence (P11.5)
    link_evidence_to_session,
    get_session_evidence,
)

# Filter & transform functions
from .filters import (
    filter_rules_by_status,
    filter_rules_by_category,
    filter_rules_by_search,
    sort_rules,
)

# Rule impact analysis (P9.4)
from .impact import (
    get_rule_dependencies,
    get_rule_dependents,
    get_rule_conflicts,
    build_dependency_graph,
    calculate_rule_impact,
    generate_mermaid_graph,
)

# Agent trust dashboard (P9.5)
from .trust import (
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
)

# Real-time monitoring (P9.6)
from .monitoring import (
    get_rule_monitor,
    get_monitor_feed,
    get_monitor_alerts,
    get_monitor_stats,
    log_monitor_event,
    acknowledge_monitor_alert,
    get_top_monitored_rules,
    get_hourly_monitor_stats,
)

# Journey pattern analyzer (P9.7)
from .journey import (
    get_journey_analyzer,
    log_journey_question,
    get_recurring_questions,
    get_journey_patterns,
    get_knowledge_gaps,
    get_question_history,
)

# Executive reports (GAP-UI-044)
from .executive import (
    get_executive_report,
)

__all__ = [
    # Core
    'MCP_TOOLS',
    'call_mcp_tool',
    'get_rules',
    'get_rules_by_category',
    'get_decisions',
    'get_sessions',
    'get_tasks',
    'search_evidence',
    # Backlog
    'get_api_base_url',
    'get_available_tasks',
    'claim_task',
    'complete_task',
    'get_agent_tasks',
    # Session evidence (P11.5)
    'link_evidence_to_session',
    'get_session_evidence',
    # Filters
    'filter_rules_by_status',
    'filter_rules_by_category',
    'filter_rules_by_search',
    'sort_rules',
    # Impact
    'get_rule_dependencies',
    'get_rule_dependents',
    'get_rule_conflicts',
    'build_dependency_graph',
    'calculate_rule_impact',
    'generate_mermaid_graph',
    # Trust
    'TRUST_WEIGHTS',
    'MAX_TENURE_DAYS',
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
    # Monitoring
    'get_rule_monitor',
    'get_monitor_feed',
    'get_monitor_alerts',
    'get_monitor_stats',
    'log_monitor_event',
    'acknowledge_monitor_alert',
    'get_top_monitored_rules',
    'get_hourly_monitor_stats',
    # Journey
    'get_journey_analyzer',
    'log_journey_question',
    'get_recurring_questions',
    'get_journey_patterns',
    'get_knowledge_gaps',
    'get_question_history',
    # Executive
    'get_executive_report',
]
