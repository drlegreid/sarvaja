"""
Dashboard State Initialization.

Per DOC-SIZE-01-v1: Extracted from governance_dashboard.py (679 lines).
Initializes form fields, detail view states, and auxiliary UI state.
"""

from typing import Any

from agent.governance_ui.state.constants import (
    RULE_CATEGORIES,
    RULE_STATUSES,
    TASK_PHASES,
    TASK_STATUSES,
)


def init_form_and_detail_states(state: Any) -> None:
    """Initialize all form fields and detail view states.

    These are Trame state variables for forms, dialogs, and detail views
    that aren't covered by get_initial_state().
    """
    # Agent Task Backlog state (TODO-6)
    state.available_tasks = []
    state.claimed_tasks = []
    state.backlog_agent_id = ""

    # Form/filter states - Rules
    state.show_rule_detail = False
    state.show_rule_form = False
    state.rule_form_mode = "create"
    state.rules_status_filter = None
    state.rules_category_filter = None
    state.rules_search_query = ""
    state.rules_sort_column = "rule_id"
    state.rules_sort_asc = True

    # GAP-UI-027 fix: Filter options as state for proper VSelect binding
    state.status_options = RULE_STATUSES
    state.category_options = RULE_CATEGORIES
    state.task_status_options = TASK_STATUSES
    state.task_phase_options = TASK_PHASES

    # Form field states - Rules
    state.form_rule_id = ""
    state.form_rule_title = ""
    state.form_rule_directive = ""
    state.form_rule_category = "governance"
    state.form_rule_priority = "HIGH"

    # Form field states - Tasks
    state.show_task_form = False
    state.form_task_id = ""
    state.form_task_description = ""
    state.form_task_phase = "P10"
    state.form_task_agent = ""

    # Detail view states - Tasks
    state.selected_task = None
    state.show_task_detail = False
    state.edit_task_mode = False
    state.edit_task_description = ""
    state.edit_task_phase = "P10"
    state.edit_task_status = "TODO"
    state.edit_task_agent = ""

    # Detail view states - Sessions
    state.selected_session = None
    state.show_session_detail = False

    # Detail view states - Decisions
    state.selected_decision = None
    state.show_decision_detail = False

    # Executive Reports state (GAP-UI-044)
    state.executive_report = None
    state.executive_loading = False
    state.executive_period = "week"

    # Agent Chat state (ORCH-006)
    state.chat_messages = []
    state.chat_input = ""
    state.chat_loading = False
    state.chat_selected_agent = None
    state.chat_session_id = None
    state.chat_task_id = None

    # File Viewer state (GAP-DATA-003)
    state.show_file_viewer = False
    state.file_viewer_path = ""
    state.file_viewer_content = ""
    state.file_viewer_loading = False
    state.file_viewer_error = ""

    # Task Execution Viewer state (ORCH-007)
    state.task_execution_log = []
    state.task_execution_loading = False
    state.show_task_execution = False

    # Test Runner state (WORKFLOW-SHELL-01-v1)
    state.tests_loading = False
    state.tests_running = False
    state.tests_current_run = None
    state.tests_recent_runs = []


def init_dialog_states(state: Any) -> None:
    """Initialize dialog states (after layout build)."""
    state.has_error = False
    state.show_confirm = False
    state.confirm_message = ""
