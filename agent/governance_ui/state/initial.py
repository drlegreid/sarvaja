"""
Initial State Factory for Governance UI
========================================
Factory function returning fresh initial state.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Extracted from state.py
Per GAP-UI-047: Added reactive loader states with trace status
Per GAP-UI-048: Added trace bar states

Created: 2024-12-28
Updated: 2026-01-14 - Added loader states with trace metadata
Updated: 2026-01-14 - Added trace bar states
"""

from typing import Dict, Any

from ..loaders.loader_state import get_initial_loader_states
from ..trace_bar.trace_store import get_initial_trace_state


def get_initial_state() -> Dict[str, Any]:
    """
    Get initial UI state.

    Factory function: returns new dict each call (no shared state).

    Returns:
        Dict with all initial state values
    """
    return {
        # Theme
        'dark_mode': False,

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
        'show_session_detail': False,
        'show_decision_detail': False,

        # Decision form state (GAP-UI-033)
        'show_decision_form': False,
        'decision_form_mode': 'create',
        'form_decision_id': '',
        'form_decision_name': '',
        'form_decision_context': '',
        'form_decision_rationale': '',
        'form_decision_status': 'PENDING',

        # Session form state (GAP-UI-034)
        'show_session_form': False,
        'session_form_mode': 'create',
        'form_session_id': '',
        'form_session_description': '',
        'form_session_status': 'ACTIVE',
        'form_session_agent_id': '',

        # Evidence Attachment (P11.5)
        'show_evidence_attach': False,
        'evidence_attach_path': '',
        'evidence_attach_loading': False,

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
        'show_graph_view': True,

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
        'monitor_filter': None,
        'auto_refresh': False,
        'top_rules': [],
        'hourly_stats': {},

        # Journey Pattern Analyzer (P9.7)
        'recurring_questions': [],
        'journey_patterns': [],
        'knowledge_gaps': [],
        'question_history': [],

        # Agent Task Backlog (TODO-6, GAP-005)
        'available_tasks': [],
        'claimed_tasks': [],
        'selected_task': None,
        'show_task_detail': False,
        'current_agent_id': None,
        'backlog_agent_id': '',
        'backlog_auto_refresh': False,
        'backlog_refresh_interval': 5,  # seconds

        # Sessions filter state
        'sessions_search_query': '',

        # Tasks filter state (GAP-UI-EXP-004)
        'tasks_search_query': '',
        'tasks_status_filter': None,
        'tasks_phase_filter': None,
        # Filter dropdown options (must match items= in tasks/list.py)
        'task_status_options': ['TODO', 'IN_PROGRESS', 'DONE', 'BLOCKED'],
        'task_phase_options': ['P10', 'P11', 'P12', 'R&D', 'FH', 'KAN', 'ORCH', 'DOCVIEW'],

        # Tasks pagination state (EPIC-DR-005)
        'tasks_page': 1,
        'tasks_per_page': 20,
        'tasks_per_page_options': [10, 20, 50, 100],
        'tasks_pagination': {
            'total': 0,
            'offset': 0,
            'limit': 20,
            'has_more': False,
            'returned': 0,
        },

        # Executive Reports (GAP-UI-044)
        'executive_report': None,
        'executive_loading': False,
        'executive_period': 'week',

        # Agent Chat (ORCH-006)
        'chat_messages': [],
        'chat_input': '',
        'chat_loading': False,
        'chat_selected_agent': None,
        'chat_session_id': None,
        'chat_task_id': None,

        # File Viewer (GAP-DATA-003)
        'show_file_viewer': False,
        'file_viewer_path': '',
        'file_viewer_content': '',
        'file_viewer_loading': False,
        'file_viewer_error': '',

        # Task Execution Viewer (ORCH-007)
        'task_execution_log': [],
        'task_execution_loading': False,
        'show_task_execution': False,

        # Infrastructure Health (GAP-INFRA-004)
        'infra_services': {},
        'infra_stats': {},
        'infra_loading': False,
        'infra_last_action': '',

        # Workflow Compliance (RD-WORKFLOW Phase 4)
        'workflow_status': {'overall': 'UNKNOWN', 'passed': 0, 'failed': 0, 'warnings': 0},
        'workflow_checks': [],
        'workflow_violations': [],
        'workflow_recommendations': [],
        'workflow_loading': False,

        # Test Runner (WORKFLOW-SHELL-01-v1)
        'tests_loading': False,
        'tests_running': False,
        'tests_current_run': None,
        'tests_recent_runs': [],

        # Reactive Loader States (GAP-UI-047)
        # Per-component loading with trace status
        **get_initial_loader_states(),

        # Trace Bar States (GAP-UI-048)
        # Bottom bar with technical traces for developer visibility
        **get_initial_trace_state(),
    }
