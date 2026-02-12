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
from .metrics import get_metrics_initial_state


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

        # Entity Navigation Context (UI-NAV-01-v1)
        # Tracks where user came from for back navigation
        'nav_source_view': None,       # 'sessions', 'rules', etc.
        'nav_source_id': None,         # session_id, rule_id, etc.
        'nav_source_label': None,      # Human-readable label for back button

        # Decision Log state (UI-AUDIT-2026-01-19: repurposed decisions)
        'decision_session_filter': None,  # Filter by session
        'decision_session_options': [],   # Populated from sessions list

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
        'evidence_search': '',  # B.4: Evidence search filter

        # Session Tasks (GAP-DATA-INTEGRITY-001 Phase 3)
        'session_tasks': [],
        'session_tasks_loading': False,

        # View state
        'show_rule_detail': False,
        'show_rule_form': False,
        'rule_form_mode': 'create',

        # Rule implementing tasks (UI-AUDIT-003)
        'rule_implementing_tasks': [],
        'rule_implementing_tasks_loading': False,

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
        'agent_sessions': [],  # EPIC-A.4: Full session data for selected agent

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

        # Task form state (GAP-TASK-CREATE-UI-001)
        'show_task_form': False,
        'form_task_id': '',
        'form_task_description': '',
        'form_task_phase': 'P10',
        'form_task_agent': '',

        # Unified Tasks View (UI-AUDIT-2026-01-19: merged backlog)
        'available_tasks': [],
        'claimed_tasks': [],
        'selected_task': None,
        'show_task_detail': False,
        'current_agent_id': None,
        'tasks_agent_id': '',  # Agent ID for claim/complete (was backlog_agent_id)
        'tasks_filter_type': 'all',  # all/available/mine/completed
        'tasks_auto_refresh': False,  # was backlog_auto_refresh
        'tasks_refresh_interval': 5,  # seconds
        # Backward compat aliases (remove in future)
        'backlog_agent_id': '',
        'backlog_auto_refresh': False,
        'backlog_refresh_interval': 5,
        'backlog_page': 1,
        'backlog_per_page': 10,
        'backlog_per_page_options': [10, 25, 50],

        # Sessions filter state (F.1: dynamic column filters)
        'sessions_search_query': '',
        'sessions_filter_status': None,
        'sessions_filter_agent': None,
        'sessions_agent_options': [],
        # Sessions view mode (F.4: pivot table)
        'sessions_view_mode': 'table',  # 'table' | 'pivot'
        'sessions_pivot_data': [],
        'sessions_pivot_group_by': 'agent_id',
        # Sessions timeline (F.3: histogram)
        'sessions_timeline_data': [],
        'sessions_timeline_labels': [],

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

        # Projects state (GOV-PROJECT-01-v1)
        'projects': [],
        'selected_project': None,
        'project_sessions': [],
        'projects_headers': [
            {"title": "Project ID", "key": "project_id", "width": "180px", "sortable": True},
            {"title": "Name", "key": "name", "sortable": True},
            {"title": "Path", "key": "path", "width": "250px", "sortable": True},
            {"title": "Plans", "key": "plan_count", "width": "80px", "sortable": True},
            {"title": "Sessions", "key": "session_count", "width": "100px", "sortable": True},
        ],

        # Sessions pagination state (GAP-UI-036)
        'sessions_page': 1,
        'sessions_per_page': 20,
        'sessions_per_page_options': [10, 20, 50, 100],
        'sessions_pagination': {
            'total': 0,
            'offset': 0,
            'limit': 20,
            'has_more': False,
            'returned': 0,
        },
        # Sessions metrics summary (GAP-SESSION-STATS-001)
        'sessions_metrics_duration': '0h',
        'sessions_metrics_avg_tasks': 0,

        # Executive Reports (GAP-UI-044)
        'executive_report': None,
        'executive_loading': False,
        'executive_period': 'week',
        'executive_session_id': None,  # UI-AUDIT-007: Selected session for report

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
        'file_viewer_html': '',
        'file_viewer_loading': False,
        'file_viewer_error': '',

        # Task Execution Viewer (ORCH-007)
        'task_execution_log': [],
        'task_execution_loading': False,
        'show_task_execution': False,

        # Infrastructure Health (GAP-INFRA-004, UI-AUDIT-008)
        'infra_services': {},
        'infra_stats': {
            'frankel_hash': '--------',
            'last_check': 'Never',
            'memory_pct': 0,
            'python_procs': 0,
            'mcp_servers': {},
            'status': 'unknown',
        },
        'infra_loading': False,
        'infra_last_action': '',
        'infra_log_lines': [],
        'infra_log_container': 'dashboard',
        'infra_log_level': '',
        # MCP detail dialog (C.2)
        'show_mcp_detail': False,
        'mcp_selected_server': None,
        # Python process drill-down (C.4)
        'infra_python_procs': [],
        'show_python_procs': False,

        # Workflow Compliance (RD-WORKFLOW Phase 4)
        'workflow_status': {'overall': 'UNKNOWN', 'passed': 0, 'failed': 0, 'warnings': 0},
        'workflow_checks': [],
        'workflow_violations': [],
        'workflow_recommendations': [],
        'workflow_loading': False,
        # LangGraph Proposal Workflow (GOV-BICAM-01-v1)
        'workflow_info': None,
        'proposal_history': [],
        'proposal_action': 'create',
        'proposal_hypothesis': '',
        'proposal_evidence': '',
        'proposal_rule_id': '',
        'proposal_directive': '',
        'proposal_dry_run': True,
        'proposal_submitting': False,
        'proposal_result': None,

        # Audit Trail (RD-DEBUG-AUDIT Phase 4)
        'audit_summary': {'total_entries': 0, 'by_action_type': {}, 'by_entity_type': {}, 'by_actor': {}, 'retention_days': 7},
        'audit_entries': [],
        'audit_loading': False,
        'audit_filter_entity_type': None,
        'audit_filter_action_type': None,
        'audit_filter_entity_id': '',
        'audit_filter_correlation_id': '',
        'audit_entity_types': ['task', 'session', 'rule', 'agent'],
        'audit_action_types': ['CREATE', 'UPDATE', 'CLAIM', 'COMPLETE', 'DELETE'],

        # Test Runner (WORKFLOW-SHELL-01-v1)
        'tests_loading': False,
        'tests_running': False,
        'tests_current_run': None,
        'tests_recent_runs': [],
        'robot_summary': None,

        # Reactive Loader States (GAP-UI-047)
        # Per-component loading with trace status
        **get_initial_loader_states(),

        # Trace Bar States (GAP-UI-048)
        # Bottom bar with technical traces for developer visibility
        **get_initial_trace_state(),

        # Session Metrics States (SESSION-METRICS-01-v1)
        **get_metrics_initial_state(),
    }
