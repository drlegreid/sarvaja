"""
State Management for Governance UI
===================================
Immutable state patterns and initial state definitions.

Per RULE-012: DSP Semantic Code Structure
Per FP Principles: Immutable state, pure transforms
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from copy import deepcopy


# =============================================================================
# STATE CONSTANTS (Immutable)
# =============================================================================

# Status color mapping
STATUS_COLORS: Dict[str, str] = {
    'ACTIVE': 'success',
    'DRAFT': 'grey',
    'DEPRECATED': 'warning',
    'PROPOSED': 'info',
}

# Priority color mapping
PRIORITY_COLORS: Dict[str, str] = {
    'CRITICAL': 'error',
    'HIGH': 'warning',
    'MEDIUM': 'grey',
    'LOW': 'grey-lighten-1',
}

# Category icon mapping
CATEGORY_ICONS: Dict[str, str] = {
    'governance': 'mdi-gavel',
    'technical': 'mdi-cog',
    'operational': 'mdi-clipboard-check',
    'strategic': 'mdi-strategy',
    'architecture': 'mdi-domain',
    'security': 'mdi-shield',
}

# Navigation items (immutable)
NAVIGATION_ITEMS: List[Dict[str, str]] = [
    {'title': 'Rules', 'icon': 'mdi-gavel', 'value': 'rules'},
    {'title': 'Impact', 'icon': 'mdi-graph', 'value': 'impact'},
    {'title': 'Trust', 'icon': 'mdi-shield-check', 'value': 'trust'},
    {'title': 'Monitor', 'icon': 'mdi-pulse', 'value': 'monitor'},
    {'title': 'Journey', 'icon': 'mdi-map-marker-path', 'value': 'journey'},
    {'title': 'Decisions', 'icon': 'mdi-scale-balance', 'value': 'decisions'},
    {'title': 'Sessions', 'icon': 'mdi-timeline', 'value': 'sessions'},
    {'title': 'Tasks', 'icon': 'mdi-checkbox-marked', 'value': 'tasks'},
    {'title': 'Search', 'icon': 'mdi-magnify', 'value': 'search'},
]

# Risk level colors
RISK_COLORS: Dict[str, str] = {
    'CRITICAL': 'error',
    'HIGH': 'warning',
    'MEDIUM': 'info',
    'LOW': 'success',
}

# Trust level colors (P9.5 - RULE-011)
TRUST_LEVEL_COLORS: Dict[str, str] = {
    'HIGH': 'success',
    'MEDIUM': 'warning',
    'LOW': 'error',
}

# Proposal status colors (P9.5 - RULE-011)
PROPOSAL_STATUS_COLORS: Dict[str, str] = {
    'pending': 'info',
    'approved': 'success',
    'rejected': 'error',
    'disputed': 'warning',
    'escalated': 'purple',
}

# Monitoring event type colors (P9.6)
EVENT_TYPE_COLORS: Dict[str, str] = {
    'rule_query': 'info',
    'rule_change': 'warning',
    'violation': 'error',
    'compliance_check': 'success',
    'trust_decrease': 'warning',
    'trust_increase': 'success',
}

# Monitoring event type icons (P9.6)
EVENT_TYPE_ICONS: Dict[str, str] = {
    'rule_query': 'mdi-magnify',
    'rule_change': 'mdi-pencil',
    'violation': 'mdi-alert-circle',
    'compliance_check': 'mdi-check-circle',
    'trust_decrease': 'mdi-arrow-down-bold',
    'trust_increase': 'mdi-arrow-up-bold',
}

# Monitoring severity colors (P9.6)
SEVERITY_COLORS: Dict[str, str] = {
    'INFO': 'info',
    'WARNING': 'warning',
    'CRITICAL': 'error',
}

# Form categories
RULE_CATEGORIES: List[str] = ['governance', 'technical', 'operational']

# Form priorities
RULE_PRIORITIES: List[str] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

# Form statuses
RULE_STATUSES: List[str] = ['ACTIVE', 'DRAFT', 'DEPRECATED']


# =============================================================================
# INITIAL STATE (Factory function - returns new dict each time)
# =============================================================================

def get_initial_state() -> Dict[str, Any]:
    """
    Get initial UI state.

    Factory function: returns new dict each call (no shared state).

    Returns:
        Dict with all initial state values
    """
    return {
        # Navigation
        'active_view': 'rules',

        # Data lists (populated by data_access)
        'rules': [],
        'decisions': [],
        'sessions': [],
        'tasks': [],

        # Selection state
        'selected_rule': None,
        'selected_session': None,
        'selected_decision': None,

        # View state
        'show_rule_detail': False,
        'show_rule_form': False,
        'rule_form_mode': 'create',

        # Filter state
        'rules_status_filter': None,
        'rules_category_filter': None,
        'rules_search_query': '',
        'rules_sort_column': 'rule_id',
        'rules_sort_asc': True,

        # Form field state
        'form_rule_id': '',
        'form_rule_title': '',
        'form_rule_directive': '',
        'form_rule_category': 'governance',
        'form_rule_priority': 'HIGH',

        # UI state
        'is_loading': False,
        'has_error': False,
        'error_message': '',
        'status_message': '',

        # Dialogs
        'show_confirm': False,
        'confirm_message': '',
        'confirm_action': None,

        # Search
        'search_query': '',
        'search_results': [],

        # Impact Analyzer (P9.4)
        'impact_selected_rule': None,
        'impact_analysis': None,
        'dependency_graph': None,
        'mermaid_diagram': '',
        'show_graph_view': True,  # True = graph, False = list

        # Agent Trust Dashboard (P9.5 - RULE-011)
        'agents': [],
        'selected_agent': None,
        'trust_leaderboard': [],
        'proposals': [],
        'escalated_proposals': [],
        'governance_stats': {},
        'show_agent_detail': False,

        # Real-time Monitoring (P9.6)
        'monitor_feed': [],
        'monitor_alerts': [],
        'monitor_stats': {},
        'monitor_filter': None,  # Filter by event type
        'auto_refresh': False,
        'top_rules': [],
        'hourly_stats': {},

        # Journey Pattern Analyzer (P9.7)
        'recurring_questions': [],
        'journey_patterns': [],
        'knowledge_gaps': [],
        'question_history': [],
    }


# =============================================================================
# PURE STATE TRANSFORMS (Functional patterns)
# =============================================================================

def with_loading(state: Dict[str, Any], loading: bool = True) -> Dict[str, Any]:
    """Return new state with loading flag set."""
    return {**state, 'is_loading': loading}


def with_error(state: Dict[str, Any], error: str) -> Dict[str, Any]:
    """Return new state with error set."""
    return {**state, 'has_error': True, 'error_message': error}


def clear_error(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return new state with error cleared."""
    return {**state, 'has_error': False, 'error_message': ''}


def with_status(state: Dict[str, Any], message: str) -> Dict[str, Any]:
    """Return new state with status message."""
    return {**state, 'status_message': message}


def with_active_view(state: Dict[str, Any], view: str) -> Dict[str, Any]:
    """Return new state with active view changed."""
    return {**state, 'active_view': view}


def with_selected_rule(state: Dict[str, Any], rule: Optional[Dict]) -> Dict[str, Any]:
    """Return new state with selected rule."""
    return {
        **state,
        'selected_rule': rule,
        'show_rule_detail': rule is not None,
    }


def with_rule_form(state: Dict[str, Any], mode: str = 'create', show: bool = True) -> Dict[str, Any]:
    """Return new state for rule form."""
    return {
        **state,
        'show_rule_form': show,
        'rule_form_mode': mode,
    }


def with_filters(
    state: Dict[str, Any],
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: str = ''
) -> Dict[str, Any]:
    """Return new state with filters applied."""
    return {
        **state,
        'rules_status_filter': status,
        'rules_category_filter': category,
        'rules_search_query': search,
    }


def with_sort(state: Dict[str, Any], column: str, ascending: bool = True) -> Dict[str, Any]:
    """Return new state with sort applied."""
    return {
        **state,
        'rules_sort_column': column,
        'rules_sort_asc': ascending,
    }


def with_impact_analysis(
    state: Dict[str, Any],
    rule_id: Optional[str] = None,
    analysis: Optional[Dict] = None,
    graph: Optional[Dict] = None,
    mermaid: str = ''
) -> Dict[str, Any]:
    """Return new state with impact analysis results."""
    return {
        **state,
        'impact_selected_rule': rule_id,
        'impact_analysis': analysis,
        'dependency_graph': graph,
        'mermaid_diagram': mermaid,
    }


def with_graph_view(state: Dict[str, Any], show_graph: bool = True) -> Dict[str, Any]:
    """Return new state with graph view toggle."""
    return {**state, 'show_graph_view': show_graph}


# =============================================================================
# UI HELPERS (Pure functions)
# =============================================================================

def get_status_color(status: str) -> str:
    """Get color for status (pure function)."""
    return STATUS_COLORS.get(status, 'grey')


def get_priority_color(priority: str) -> str:
    """Get color for priority (pure function)."""
    return PRIORITY_COLORS.get(priority, 'grey')


def get_category_icon(category: str) -> str:
    """Get icon for category (pure function)."""
    return CATEGORY_ICONS.get(category, 'mdi-file')


def format_rule_card(rule: Dict[str, Any]) -> Dict[str, str]:
    """
    Format rule data for card display.

    Pure function: same input -> same output.

    Args:
        rule: Rule dict

    Returns:
        Formatted card data
    """
    status = rule.get('status', 'unknown')
    rule_id = rule.get('rule_id') or rule.get('id', 'Unknown')
    return {
        'title': rule_id,
        'subtitle': rule.get('title') or rule.get('name', ''),
        'color': get_status_color(status),
        'icon': get_category_icon(rule.get('category', 'governance')),
    }


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level (pure function)."""
    return RISK_COLORS.get(risk_level, 'grey')


def format_impact_summary(impact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format impact analysis for display.

    Pure function: same input -> same output.

    Args:
        impact: Impact analysis dict

    Returns:
        Formatted summary for UI
    """
    return {
        'rule_id': impact.get('rule_id', 'Unknown'),
        'risk_level': impact.get('risk_level', 'LOW'),
        'risk_color': get_risk_color(impact.get('risk_level', 'LOW')),
        'total_affected': impact.get('total_affected', 0),
        'direct_dependents': len(impact.get('direct_dependents', [])),
        'dependencies': len(impact.get('dependencies', [])),
        'recommendation': impact.get('recommendation', ''),
        'critical_affected': impact.get('critical_rules_affected', []),
    }


# =============================================================================
# TRUST DASHBOARD STATE TRANSFORMS (P9.5 - RULE-011)
# =============================================================================

def with_agents(state: Dict[str, Any], agents: List[Dict]) -> Dict[str, Any]:
    """Return new state with agents and leaderboard."""
    from agent.governance_ui.data_access import build_trust_leaderboard
    return {
        **state,
        'agents': agents,
        'trust_leaderboard': build_trust_leaderboard(agents),
    }


def with_selected_agent(state: Dict[str, Any], agent: Optional[Dict]) -> Dict[str, Any]:
    """Return new state with selected agent."""
    return {
        **state,
        'selected_agent': agent,
        'show_agent_detail': agent is not None,
    }


def with_proposals(state: Dict[str, Any], proposals: List[Dict]) -> Dict[str, Any]:
    """Return new state with proposals."""
    return {**state, 'proposals': proposals}


def with_escalated_proposals(state: Dict[str, Any], escalated: List[Dict]) -> Dict[str, Any]:
    """Return new state with escalated proposals."""
    return {**state, 'escalated_proposals': escalated}


def with_governance_stats(state: Dict[str, Any], stats: Dict) -> Dict[str, Any]:
    """Return new state with governance stats."""
    return {**state, 'governance_stats': stats}


# =============================================================================
# TRUST DASHBOARD UI HELPERS (P9.5 - RULE-011)
# =============================================================================

def get_trust_level(score: float) -> str:
    """Get trust level category from score (pure function)."""
    if score >= 0.8:
        return 'HIGH'
    elif score >= 0.5:
        return 'MEDIUM'
    else:
        return 'LOW'


def get_trust_level_color(level: str) -> str:
    """Get color for trust level (pure function)."""
    return TRUST_LEVEL_COLORS.get(level, 'grey')


def get_proposal_status_color(status: str) -> str:
    """Get color for proposal status (pure function)."""
    return PROPOSAL_STATUS_COLORS.get(status, 'grey')


def format_agent_card(agent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format agent data for card display.

    Pure function: same input -> same output.

    Args:
        agent: Agent dict

    Returns:
        Formatted card data
    """
    trust_score = agent.get('trust_score', 0.0)
    trust_level = get_trust_level(trust_score)
    return {
        'agent_id': agent.get('agent_id', 'Unknown'),
        'name': agent.get('name', agent.get('agent_name', 'Unknown')),
        'agent_type': agent.get('agent_type', 'unknown'),
        'trust_score': trust_score,
        'trust_level': trust_level,
        'trust_color': get_trust_level_color(trust_level),
        'compliance_rate': agent.get('compliance_rate', 0.0),
        'accuracy_rate': agent.get('accuracy_rate', 0.0),
        'tenure_days': agent.get('tenure_days', 0),
    }


def format_proposal_card(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format proposal data for card display.

    Pure function: same input -> same output.

    Args:
        proposal: Proposal dict

    Returns:
        Formatted card data
    """
    status = proposal.get('proposal_status', 'pending')
    return {
        'proposal_id': proposal.get('proposal_id', 'Unknown'),
        'proposal_type': proposal.get('proposal_type', 'unknown'),
        'status': status,
        'status_color': get_proposal_status_color(status),
        'proposer_id': proposal.get('proposer_id', 'Unknown'),
        'affected_rule': proposal.get('affected_rule', ''),
        'evidence': proposal.get('evidence', ''),
    }


# =============================================================================
# REAL-TIME MONITORING STATE TRANSFORMS (P9.6)
# =============================================================================

def with_monitor_feed(state: Dict[str, Any], feed: List[Dict]) -> Dict[str, Any]:
    """Return new state with monitor feed."""
    return {**state, 'monitor_feed': feed}


def with_monitor_alerts(state: Dict[str, Any], alerts: List[Dict]) -> Dict[str, Any]:
    """Return new state with monitor alerts."""
    return {**state, 'monitor_alerts': alerts}


def with_monitor_stats(state: Dict[str, Any], stats: Dict) -> Dict[str, Any]:
    """Return new state with monitor stats."""
    return {**state, 'monitor_stats': stats}


def with_monitor_filter(state: Dict[str, Any], event_type: Optional[str]) -> Dict[str, Any]:
    """Return new state with monitor filter."""
    return {**state, 'monitor_filter': event_type}


def with_auto_refresh(state: Dict[str, Any], enabled: bool) -> Dict[str, Any]:
    """Return new state with auto-refresh toggle."""
    return {**state, 'auto_refresh': enabled}


def with_top_rules(state: Dict[str, Any], top_rules: List[Dict]) -> Dict[str, Any]:
    """Return new state with top monitored rules."""
    return {**state, 'top_rules': top_rules}


def with_hourly_stats(state: Dict[str, Any], hourly: Dict) -> Dict[str, Any]:
    """Return new state with hourly stats."""
    return {**state, 'hourly_stats': hourly}


# =============================================================================
# REAL-TIME MONITORING UI HELPERS (P9.6)
# =============================================================================

def get_event_type_color(event_type: str) -> str:
    """Get color for event type (pure function)."""
    return EVENT_TYPE_COLORS.get(event_type, 'grey')


def get_event_type_icon(event_type: str) -> str:
    """Get icon for event type (pure function)."""
    return EVENT_TYPE_ICONS.get(event_type, 'mdi-information')


def get_severity_color(severity: str) -> str:
    """Get color for severity (pure function)."""
    return SEVERITY_COLORS.get(severity, 'info')


def format_event_item(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format event data for display.

    Pure function: same input -> same output.

    Args:
        event: Event dict from monitor

    Returns:
        Formatted event for UI
    """
    event_type = event.get('event_type', 'unknown')
    severity = event.get('severity', 'INFO')

    return {
        'event_id': event.get('event_id', 'Unknown'),
        'event_type': event_type,
        'source': event.get('source', 'Unknown'),
        'timestamp': event.get('timestamp', ''),
        'severity': severity,
        'icon': get_event_type_icon(event_type),
        'color': get_severity_color(severity),
        'rule_id': event.get('details', {}).get('rule_id', ''),
        'details': event.get('details', {}),
    }


def format_alert_item(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format alert data for display.

    Pure function: same input -> same output.

    Args:
        alert: Alert dict from monitor

    Returns:
        Formatted alert for UI
    """
    severity = alert.get('severity', 'INFO')
    acknowledged = alert.get('acknowledged', False)

    return {
        'alert_id': alert.get('alert_id', 'Unknown'),
        'message': alert.get('message', ''),
        'rule_id': alert.get('rule_id', ''),
        'severity': severity,
        'color': get_severity_color(severity),
        'acknowledged': acknowledged,
        'ack_color': 'grey' if acknowledged else 'error',
        'timestamp': alert.get('timestamp', ''),
    }


# =============================================================================
# JOURNEY PATTERN ANALYZER STATE (P9.7)
# =============================================================================

# Priority colors for knowledge gaps
GAP_PRIORITY_COLORS: Dict[str, str] = {
    'high': 'error',
    'medium': 'warning',
    'low': 'info',
}


def with_recurring_questions(
    state: Dict[str, Any],
    questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add recurring questions to state.

    Args:
        state: Current state
        questions: List of recurring questions

    Returns:
        New state with recurring_questions
    """
    return {**state, 'recurring_questions': questions}


def with_journey_patterns(
    state: Dict[str, Any],
    patterns: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add journey patterns to state.

    Args:
        state: Current state
        patterns: List of detected patterns

    Returns:
        New state with journey_patterns
    """
    return {**state, 'journey_patterns': patterns}


def with_knowledge_gaps(
    state: Dict[str, Any],
    gaps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add knowledge gaps to state.

    Args:
        state: Current state
        gaps: List of knowledge gaps

    Returns:
        New state with knowledge_gaps
    """
    return {**state, 'knowledge_gaps': gaps}


def with_question_history(
    state: Dict[str, Any],
    history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Pure transform: add question history to state.

    Args:
        state: Current state
        history: Question history list

    Returns:
        New state with question_history
    """
    return {**state, 'question_history': history}


def get_gap_priority_color(priority: str) -> str:
    """
    Get color for knowledge gap priority.

    Args:
        priority: Priority level (high, medium, low)

    Returns:
        Vuetify color string
    """
    return GAP_PRIORITY_COLORS.get(priority.lower(), 'grey')


def format_recurring_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format recurring question for display.

    Pure function: same input -> same output.

    Args:
        question: Recurring question dict

    Returns:
        Formatted question for UI
    """
    count = question.get('count', 0)

    # Determine urgency color based on count
    if count >= 5:
        urgency_color = 'error'
        urgency = 'critical'
    elif count >= 3:
        urgency_color = 'warning'
        urgency = 'high'
    else:
        urgency_color = 'info'
        urgency = 'moderate'

    return {
        'question': question.get('question', ''),
        'count': count,
        'urgency': urgency,
        'urgency_color': urgency_color,
        'sources': question.get('sources', []),
        'first_asked': question.get('first_asked', ''),
        'last_asked': question.get('last_asked', ''),
    }


def format_knowledge_gap(gap: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format knowledge gap for display.

    Pure function: same input -> same output.

    Args:
        gap: Knowledge gap dict

    Returns:
        Formatted gap for UI
    """
    priority = gap.get('priority', 'medium')

    return {
        'topic': gap.get('topic', 'Unknown'),
        'question_pattern': gap.get('question_pattern', ''),
        'count': gap.get('count', 0),
        'priority': priority,
        'priority_color': get_gap_priority_color(priority),
        'sources': gap.get('sources', []),
    }


def format_journey_pattern(pattern: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format journey pattern for display.

    Pure function: same input -> same output.

    Args:
        pattern: Pattern dict from analyzer

    Returns:
        Formatted pattern for UI
    """
    return {
        'topic': pattern.get('topic', 'Unknown'),
        'question_count': pattern.get('question_count', 0),
        'questions': pattern.get('questions', [])[:3],  # Show max 3
        'suggestion': pattern.get('suggestion', ''),
        'ui_recommendation': pattern.get('ui_recommendation', {}),
        'component': pattern.get('ui_recommendation', {}).get('component', 'InfoWidget'),
        'location': pattern.get('ui_recommendation', {}).get('location', 'sidebar'),
    }
