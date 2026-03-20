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
        'dark_mode': True,

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
        'form_decision_options': [],          # Decision options list
        'form_decision_selected_option': '',  # Currently selected option

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

        # Session Detail: Tool Calls & Thoughts (GAP-SESSION-DETAIL-001)
        'session_tool_calls': [],
        'session_tool_calls_loading': False,
        'session_thinking_items': [],
        'session_thinking_items_loading': False,
        'session_timeline': [],  # Merged chronological view of tools+thoughts

        # Session Content Validation (RELIABILITY-PLAN-01-v1 P1)
        'session_validation_data': None,
        'session_validation_loading': False,

        # Session Evidence Rendered HTML (GAP-SESSION-DETAIL-002)
        'session_evidence_html': '',
        'session_evidence_loading': False,

        # Session Conversation Transcript (GAP-SESSION-TRANSCRIPT-001)
        'session_transcript': [],
        'session_transcript_loading': False,
        'session_transcript_page': 1,
        'session_transcript_total': 0,
        'session_transcript_has_more': False,
        'session_transcript_include_thinking': True,
        'session_transcript_include_user': True,
        'session_transcript_expanded_entry': None,

        # View state
        'show_rule_detail': False,
        'show_rule_form': False,
        'rule_form_mode': 'create',

        # Rule implementing tasks (UI-AUDIT-003)
        'rule_implementing_tasks': [],
        'rule_implementing_tasks_loading': False,

        # Rules table headers (pattern: sessions_headers)
        'rules_headers': [
            {"title": "Rule ID", "key": "id", "width": "180px", "sortable": True},
            {"title": "Name", "key": "name", "sortable": True},
            {"title": "Status", "key": "status", "width": "100px", "sortable": True},
            {"title": "Category", "key": "category", "width": "120px", "sortable": True},
            {"title": "Priority", "key": "priority", "width": "100px", "sortable": True},
            {"title": "Applicability", "key": "applicability", "width": "120px", "sortable": True},
            {"title": "Tasks", "key": "linked_tasks_count", "width": "80px", "sortable": True},
            {"title": "Sessions", "key": "linked_sessions_count", "width": "90px", "sortable": True},
            {"title": "Created", "key": "created_date", "width": "120px", "sortable": True},
        ],

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
        'form_rule_applicability': 'MANDATORY',

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
        'dependency_overview': None,  # Overview stats for dependency graph
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
        'show_agent_registration': False,
        'reg_agent_name': '',         # Registration form fields
        'reg_agent_id': '',
        'reg_agent_type': '',
        'reg_agent_model': '',
        'reg_agent_rules': [],
        'reg_agent_instructions': '',
        'reg_agent_loading': False,
        'agent_sessions': [],  # EPIC-A.4: Full session data for selected agent
        'trust_history': [],  # Trust score history for selected agent

        # Real-time Monitoring (P9.6)
        'monitor_feed': [],
        'monitor_alerts': [],
        'monitor_stats': {},
        'monitor_filter': None,
        'monitor_event_type_filter': '',
        'monitor_headers': [
            {"title": "Type", "key": "event_type", "width": "130px", "sortable": True},
            {"title": "Source", "key": "source", "sortable": True},
            {"title": "Severity", "key": "severity", "width": "100px", "sortable": True},
            {"title": "Timestamp", "key": "timestamp", "width": "160px", "sortable": True},
            {"title": "Rule", "key": "rule_id", "width": "140px", "sortable": True},
        ],
        'auto_refresh': False,
        'top_rules': [],
        'hourly_stats': {},
        'monitor_last_updated': '',

        # Journey Pattern Analyzer (P9.7)
        'recurring_questions': [],
        'journey_patterns': [],
        'knowledge_gaps': [],
        'question_history': [],

        # Task form state (GAP-TASK-CREATE-UI-001)
        'show_task_form': False,
        'form_task_id': '',
        'form_task_description': '',
        'form_task_body': '',
        'form_task_phase': 'P10',
        'form_task_agent': '',
        'form_task_priority': None,
        'form_task_type': None,

        # Task document management
        'show_attach_document_dialog': False,
        'attach_document_path': '',

        # Task edit mode (inline editing in detail view)
        'edit_task_mode': False,
        'edit_task_description': '',
        'edit_task_phase': 'P10',
        'edit_task_status': 'TODO',
        'edit_task_agent': '',
        'edit_task_body': '',

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

        # Sessions auto-refresh (P2-10c: UI-REFRESH-01-v1)
        'sessions_auto_refresh': False,
        'sessions_refresh_interval': 10,  # seconds

        # Sessions filter state (F.1: dynamic column filters)
        'sessions_search_query': '',
        'sessions_filter_status': None,
        'sessions_filter_agent': None,
        'sessions_agent_options': [],
        'sessions_exclude_test': True,  # BUG-3: Hide test sessions by default
        # Sessions view mode (F.4: pivot table)
        'sessions_view_mode': 'table',  # 'table' | 'pivot'
        'sessions_pivot_data': [],
        'sessions_pivot_group_by': 'agent_id',
        # Sessions timeline (F.3: histogram)
        'sessions_timeline_data': [],
        'sessions_timeline_labels': [],
        # Sessions date range filter (histogram click-to-filter)
        'sessions_date_from': None,
        'sessions_date_to': None,

        # Tasks table headers (pattern: sessions_headers)
        'tasks_headers': [
            {"title": "Task ID", "key": "task_id", "width": "150px", "sortable": True},
            {"title": "Description", "key": "description", "sortable": True},
            {"title": "Priority", "key": "priority", "width": "90px", "sortable": True},
            {"title": "Type", "key": "task_type", "width": "80px", "sortable": True},
            {"title": "Status", "key": "status", "width": "100px", "sortable": True},
            {"title": "Phase", "key": "phase", "width": "70px", "sortable": True},
            {"title": "Agent", "key": "agent_id", "width": "130px", "sortable": True},
            {"title": "Created", "key": "created_at", "width": "110px", "sortable": True},
            {"title": "Completed", "key": "completed_at", "width": "110px", "sortable": True},
            {"title": "Gap", "key": "gap_id", "width": "100px", "sortable": True},
            {"title": "Docs", "key": "doc_count", "width": "70px", "sortable": False},
        ],

        # Tasks filter state (GAP-UI-EXP-004)
        'tasks_search_query': '',
        'tasks_status_filter': None,
        'tasks_phase_filter': None,
        # Filter dropdown options (must match items= in tasks/list.py)
        'task_status_options': ['TODO', 'IN_PROGRESS', 'DONE', 'BLOCKED'],
        'task_phase_options': ['P10', 'P11', 'P12', 'R&D', 'FH', 'KAN', 'ORCH', 'DOCVIEW'],
        # Task taxonomy dropdowns (META-TAXON-01-v1)
        'task_type_options': ['bug', 'feature', 'chore', 'research', 'gap', 'epic', 'test'],
        'task_priority_options': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],

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

        # Workspaces state (Entity chain: Project→Workspace→Agent)
        'workspaces': [],
        'selected_workspace': None,
        'show_workspace_detail': False,
        'workspaces_loading': False,
        'workspaces_search': '',
        'workspaces_type_filter': None,
        'workspaces_status_filter': None,
        'workspace_types': [],
        'workspace_type_options': [],
        # Workspace CRUD form state
        'show_workspace_form': False,
        'form_workspace_name': '',
        'form_workspace_type': 'generic',
        'form_workspace_description': '',
        'form_workspace_project_id': '',
        'edit_workspace_mode': False,
        'edit_workspace_name': '',
        'edit_workspace_description': '',
        'edit_workspace_status': 'active',
        'show_workspace_delete_confirm': False,
        # GAP-WS-DETAIL-UI: Linked tasks
        'workspace_tasks': [],
        'workspace_tasks_loading': False,

        # Agent Capabilities state (rule→agent bindings)
        'agent_capabilities': [],
        'agent_capabilities_loading': False,
        'new_capability_rule_id': '',
        'new_capability_category': 'general',

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

        # Sessions table headers (pattern: projects_headers)
        'sessions_headers': [
            {"title": "Session ID", "key": "session_id", "width": "180px", "sortable": True},
            {"title": "Name", "key": "cc_external_name", "width": "140px", "sortable": True},
            {"title": "Source", "key": "source_type", "width": "70px", "sortable": True},
            {"title": "Project", "key": "cc_project_slug", "width": "120px", "sortable": True},
            {"title": "Start", "key": "start_time", "width": "130px", "sortable": True},
            {"title": "End", "key": "end_time", "width": "130px", "sortable": True},
            {"title": "Duration", "key": "duration", "width": "90px", "sortable": True},
            {"title": "Status", "key": "status", "width": "100px", "sortable": True},
            {"title": "Agent", "key": "agent_id", "width": "130px", "sortable": True},
            {"title": "Description", "key": "description"},
        ],
        'sessions_pivot_headers': [
            {"title": "Group", "key": "group", "sortable": True},
            {"title": "Count", "key": "count", "width": "80px", "sortable": True},
            {"title": "Completed", "key": "completed", "width": "100px", "sortable": True},
            {"title": "Active", "key": "active", "width": "80px", "sortable": True},
            {"title": "Avg Duration", "key": "avg_duration", "width": "120px", "sortable": True},
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
        'executive_expanded_sections': [],  # Accordion state for executive sections

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
        'show_task_execution': False,  # Chat dialog (chat/execution.py)
        'show_task_execution_inline': False,  # Task detail inline (tasks/execution.py)

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
        'audit_filter_date_from': None,
        'audit_filter_date_to': None,
        'audit_entity_types': ['task', 'session', 'rule', 'agent'],
        'audit_action_types': ['CREATE', 'UPDATE', 'CLAIM', 'COMPLETE', 'DELETE'],

        # Test Runner (WORKFLOW-SHELL-01-v1)
        'tests_loading': False,
        'tests_running': False,
        'tests_current_run': None,
        'tests_recent_runs': [],
        'tests_cvp_status': None,
        'tests_category_filter': '',  # '' = all, else filter by category
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
