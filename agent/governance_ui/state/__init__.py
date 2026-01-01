"""
State Management Package for Governance UI
==========================================
Re-exports all state components for backward compatibility.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Modularized from state.py (1547 -> ~30 lines, 98% reduction)

Module structure:
    - constants.py: All color/icon constants
    - initial.py: get_initial_state() factory
    - core.py: Core transforms and helpers
    - trust.py: Trust dashboard state (P9.5)
    - monitor.py: Monitoring state (P9.6)
    - journey.py: Journey analyzer state (P9.7)
    - backlog.py: Task backlog state (TODO-6)
    - executive.py: Executive reports state (GAP-UI-044)
    - chat.py: Agent chat state (ORCH-006)
    - file_viewer.py: File viewer state (GAP-DATA-003)
    - execution.py: Task execution state (ORCH-007)

Created: 2024-12-28
"""

# =============================================================================
# CONSTANTS
# =============================================================================
from .constants import (
    STATUS_COLORS,
    PRIORITY_COLORS,
    RISK_COLORS,
    CATEGORY_ICONS,
    NAVIGATION_ITEMS,
    TRUST_LEVEL_COLORS,
    PROPOSAL_STATUS_COLORS,
    EVENT_TYPE_COLORS,
    EVENT_TYPE_ICONS,
    SEVERITY_COLORS,
    RULE_CATEGORIES,
    RULE_PRIORITIES,
    RULE_STATUSES,
    GAP_PRIORITY_COLORS,
    TASK_STATUS_COLORS,
    EXECUTIVE_STATUS_COLORS,
    SECTION_STATUS_COLORS,
    CHAT_ROLE_COLORS,
    CHAT_STATUS_ICONS,
    EXECUTION_EVENT_TYPES,
)

# =============================================================================
# INITIAL STATE
# =============================================================================
from .initial import get_initial_state

# =============================================================================
# CORE TRANSFORMS & HELPERS
# =============================================================================
from .core import (
    # Transforms
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
    # Helpers
    get_status_color,
    get_priority_color,
    get_category_icon,
    get_risk_color,
    format_rule_card,
    format_impact_summary,
)

# =============================================================================
# TRUST DASHBOARD (P9.5)
# =============================================================================
from .trust import (
    with_agents,
    with_selected_agent,
    with_proposals,
    with_escalated_proposals,
    with_governance_stats,
    get_trust_level,
    get_trust_level_color,
    get_proposal_status_color,
    format_agent_card,
    format_proposal_card,
)

# =============================================================================
# MONITORING (P9.6)
# =============================================================================
from .monitor import (
    with_monitor_feed,
    with_monitor_alerts,
    with_monitor_stats,
    with_monitor_filter,
    with_auto_refresh,
    with_top_rules,
    with_hourly_stats,
    get_event_type_color,
    get_event_type_icon,
    get_severity_color,
    format_event_item,
    format_alert_item,
)

# =============================================================================
# JOURNEY (P9.7)
# =============================================================================
from .journey import (
    with_recurring_questions,
    with_journey_patterns,
    with_knowledge_gaps,
    with_question_history,
    get_gap_priority_color,
    format_recurring_question,
    format_knowledge_gap,
    format_journey_pattern,
)

# =============================================================================
# BACKLOG (TODO-6)
# =============================================================================
from .backlog import (
    with_available_tasks,
    with_claimed_tasks,
    with_selected_task,
    with_current_agent,
    get_task_status_color,
    format_backlog_task,
)

# =============================================================================
# EXECUTIVE (GAP-UI-044)
# =============================================================================
from .executive import (
    with_executive_report,
    with_executive_loading,
    with_executive_period,
    get_executive_status_color,
    get_section_status_color,
    format_executive_section,
    format_executive_report,
)

# =============================================================================
# CHAT (ORCH-006)
# =============================================================================
from .chat import (
    with_chat_messages,
    with_chat_message,
    with_chat_loading,
    with_chat_input,
    with_chat_agent,
    with_chat_session,
    with_chat_task,
    get_chat_role_color,
    get_chat_status_icon,
    format_chat_message,
    create_user_message,
    create_agent_message,
    create_system_message,
)

# =============================================================================
# FILE VIEWER (GAP-DATA-003)
# =============================================================================
from .file_viewer import (
    with_file_viewer,
    with_file_viewer_loading,
    with_file_viewer_content,
    with_file_viewer_error,
    close_file_viewer,
)

# =============================================================================
# TASK EXECUTION (ORCH-007)
# =============================================================================
from .execution import (
    with_task_execution_log,
    with_task_execution_loading,
    with_task_execution_event,
    clear_task_execution,
    get_execution_event_style,
    format_execution_event,
)

# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    # Constants
    'STATUS_COLORS', 'PRIORITY_COLORS', 'RISK_COLORS', 'CATEGORY_ICONS',
    'NAVIGATION_ITEMS', 'TRUST_LEVEL_COLORS', 'PROPOSAL_STATUS_COLORS',
    'EVENT_TYPE_COLORS', 'EVENT_TYPE_ICONS', 'SEVERITY_COLORS',
    'RULE_CATEGORIES', 'RULE_PRIORITIES', 'RULE_STATUSES',
    'GAP_PRIORITY_COLORS', 'TASK_STATUS_COLORS',
    'EXECUTIVE_STATUS_COLORS', 'SECTION_STATUS_COLORS',
    'CHAT_ROLE_COLORS', 'CHAT_STATUS_ICONS', 'EXECUTION_EVENT_TYPES',
    # Initial state
    'get_initial_state',
    # Core
    'with_loading', 'with_error', 'clear_error', 'with_status',
    'with_active_view', 'with_selected_rule', 'with_rule_form',
    'with_filters', 'with_sort', 'with_impact_analysis', 'with_graph_view',
    'get_status_color', 'get_priority_color', 'get_category_icon',
    'get_risk_color', 'format_rule_card', 'format_impact_summary',
    # Trust
    'with_agents', 'with_selected_agent', 'with_proposals',
    'with_escalated_proposals', 'with_governance_stats',
    'get_trust_level', 'get_trust_level_color', 'get_proposal_status_color',
    'format_agent_card', 'format_proposal_card',
    # Monitor
    'with_monitor_feed', 'with_monitor_alerts', 'with_monitor_stats',
    'with_monitor_filter', 'with_auto_refresh', 'with_top_rules',
    'with_hourly_stats', 'get_event_type_color', 'get_event_type_icon',
    'get_severity_color', 'format_event_item', 'format_alert_item',
    # Journey
    'with_recurring_questions', 'with_journey_patterns',
    'with_knowledge_gaps', 'with_question_history',
    'get_gap_priority_color', 'format_recurring_question',
    'format_knowledge_gap', 'format_journey_pattern',
    # Backlog
    'with_available_tasks', 'with_claimed_tasks', 'with_selected_task',
    'with_current_agent', 'get_task_status_color', 'format_backlog_task',
    # Executive
    'with_executive_report', 'with_executive_loading', 'with_executive_period',
    'get_executive_status_color', 'get_section_status_color',
    'format_executive_section', 'format_executive_report',
    # Chat
    'with_chat_messages', 'with_chat_message', 'with_chat_loading',
    'with_chat_input', 'with_chat_agent', 'with_chat_session', 'with_chat_task',
    'get_chat_role_color', 'get_chat_status_icon', 'format_chat_message',
    'create_user_message', 'create_agent_message', 'create_system_message',
    # File viewer
    'with_file_viewer', 'with_file_viewer_loading', 'with_file_viewer_content',
    'with_file_viewer_error', 'close_file_viewer',
    # Execution
    'with_task_execution_log', 'with_task_execution_loading',
    'with_task_execution_event', 'clear_task_execution',
    'get_execution_event_style', 'format_execution_event',
]
