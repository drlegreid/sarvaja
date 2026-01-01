"""
State Constants for Governance UI
==================================
Immutable color mappings, icons, and configuration.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py

Created: 2024-12-28
"""

from typing import Dict, List


# =============================================================================
# STATUS/PRIORITY COLORS
# =============================================================================

STATUS_COLORS: Dict[str, str] = {
    'ACTIVE': 'success',
    'DRAFT': 'grey',
    'DEPRECATED': 'warning',
    'PROPOSED': 'info',
}

PRIORITY_COLORS: Dict[str, str] = {
    'CRITICAL': 'error',
    'HIGH': 'warning',
    'MEDIUM': 'grey',
    'LOW': 'grey-lighten-1',
}

RISK_COLORS: Dict[str, str] = {
    'CRITICAL': 'error',
    'HIGH': 'warning',
    'MEDIUM': 'info',
    'LOW': 'success',
}


# =============================================================================
# CATEGORY ICONS
# =============================================================================

CATEGORY_ICONS: Dict[str, str] = {
    'governance': 'mdi-gavel',
    'technical': 'mdi-cog',
    'operational': 'mdi-clipboard-check',
    'strategic': 'mdi-strategy',
    'architecture': 'mdi-domain',
    'security': 'mdi-shield',
}


# =============================================================================
# NAVIGATION
# =============================================================================

NAVIGATION_ITEMS: List[Dict[str, str]] = [
    {'title': 'Chat', 'icon': 'mdi-chat', 'value': 'chat'},  # ORCH-006: Agent Chat UI
    {'title': 'Rules', 'icon': 'mdi-gavel', 'value': 'rules'},
    {'title': 'Agents', 'icon': 'mdi-robot', 'value': 'agents'},
    {'title': 'Tasks', 'icon': 'mdi-checkbox-marked', 'value': 'tasks'},
    {'title': 'Backlog', 'icon': 'mdi-inbox-arrow-down', 'value': 'backlog'},  # TODO-6
    {'title': 'Sessions', 'icon': 'mdi-timeline', 'value': 'sessions'},
    {'title': 'Executive', 'icon': 'mdi-chart-box', 'value': 'executive'},  # GAP-UI-044
    {'title': 'Decisions', 'icon': 'mdi-scale-balance', 'value': 'decisions'},
    {'title': 'Impact', 'icon': 'mdi-graph', 'value': 'impact'},
    {'title': 'Trust', 'icon': 'mdi-shield-check', 'value': 'trust'},
    {'title': 'Monitor', 'icon': 'mdi-pulse', 'value': 'monitor'},
    {'title': 'Search', 'icon': 'mdi-magnify', 'value': 'search'},
]


# =============================================================================
# TRUST DASHBOARD (P9.5)
# =============================================================================

TRUST_LEVEL_COLORS: Dict[str, str] = {
    'HIGH': 'success',
    'MEDIUM': 'warning',
    'LOW': 'error',
}

PROPOSAL_STATUS_COLORS: Dict[str, str] = {
    'pending': 'info',
    'approved': 'success',
    'rejected': 'error',
    'disputed': 'warning',
    'escalated': 'purple',
}


# =============================================================================
# MONITORING (P9.6)
# =============================================================================

EVENT_TYPE_COLORS: Dict[str, str] = {
    'rule_query': 'info',
    'rule_change': 'warning',
    'violation': 'error',
    'compliance_check': 'success',
    'trust_decrease': 'warning',
    'trust_increase': 'success',
}

EVENT_TYPE_ICONS: Dict[str, str] = {
    'rule_query': 'mdi-magnify',
    'rule_change': 'mdi-pencil',
    'violation': 'mdi-alert-circle',
    'compliance_check': 'mdi-check-circle',
    'trust_decrease': 'mdi-arrow-down-bold',
    'trust_increase': 'mdi-arrow-up-bold',
}

SEVERITY_COLORS: Dict[str, str] = {
    'INFO': 'info',
    'WARNING': 'warning',
    'CRITICAL': 'error',
}


# =============================================================================
# FORM OPTIONS
# =============================================================================

RULE_CATEGORIES: List[str] = ['governance', 'technical', 'operational']
RULE_PRIORITIES: List[str] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
RULE_STATUSES: List[str] = ['ACTIVE', 'DRAFT', 'DEPRECATED']


# =============================================================================
# JOURNEY (P9.7)
# =============================================================================

GAP_PRIORITY_COLORS: Dict[str, str] = {
    'high': 'error',
    'medium': 'warning',
    'low': 'info',
}


# =============================================================================
# BACKLOG (TODO-6)
# =============================================================================

TASK_STATUS_COLORS: Dict[str, str] = {
    'TODO': 'info',
    'IN_PROGRESS': 'warning',
    'DONE': 'success',
    'BLOCKED': 'error',
}


# =============================================================================
# EXECUTIVE (GAP-UI-044)
# =============================================================================

EXECUTIVE_STATUS_COLORS: Dict[str, str] = {
    'healthy': 'success',
    'warning': 'warning',
    'critical': 'error',
}

SECTION_STATUS_COLORS: Dict[str, str] = {
    'success': 'success',
    'warning': 'warning',
    'error': 'error',
}


# =============================================================================
# CHAT (ORCH-006)
# =============================================================================

CHAT_ROLE_COLORS: Dict[str, str] = {
    'user': 'primary',
    'agent': 'success',
    'system': 'grey',
    'error': 'error',
}

CHAT_STATUS_ICONS: Dict[str, str] = {
    'pending': 'mdi-clock-outline',
    'processing': 'mdi-loading',
    'complete': 'mdi-check',
    'error': 'mdi-alert-circle',
}


# =============================================================================
# TASK EXECUTION (ORCH-007)
# =============================================================================

EXECUTION_EVENT_TYPES: Dict[str, Dict[str, str]] = {
    'claimed': {'icon': 'mdi-hand-back-right', 'color': 'info'},
    'started': {'icon': 'mdi-play', 'color': 'primary'},
    'progress': {'icon': 'mdi-progress-clock', 'color': 'info'},
    'delegated': {'icon': 'mdi-account-switch', 'color': 'warning'},
    'completed': {'icon': 'mdi-check-circle', 'color': 'success'},
    'failed': {'icon': 'mdi-alert-circle', 'color': 'error'},
    'evidence': {'icon': 'mdi-file-document', 'color': 'secondary'},
}
