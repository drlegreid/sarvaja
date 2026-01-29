"""
Governance Dashboard UI (P9.2)
Created: 2024-12-25
Updated: 2024-12-28 (GAP-FILE-005: Controllers extracted to modules)

Trame-based dashboard for viewing governance artifacts:
- Rules (22 rules from TypeDB)
- Decisions (strategic decisions)
- Sessions (evidence files)
- Tasks (R&D backlog)

Per RULE-019: UI/UX Design Standards
Per DECISION-003: TypeDB-First Strategy
Per RULE-012: DSP Semantic Code Structure (300 line limit per file)

Structure (per DSP):
    governance_ui/data_access.py  - Pure MCP data functions
    governance_ui/state/          - Immutable state, transforms (GAP-FILE-004)
    governance_ui/controllers/    - Trame controller modules (GAP-FILE-005)
    governance_ui/views/          - Extracted view modules (12 modules)
    governance_dashboard.py       - Trame view layer (this file)

Dependencies:
    pip install trame trame-vuetify trame-client
"""

import sys
import os
from pathlib import Path

from shared.constants import APP_TITLE

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent

# API base URL (default to localhost:8082)
API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# IMPORTS FROM governance_ui PACKAGE (DSP: Pure functions)
# =============================================================================
from agent.governance_ui import (
    # Data access (pure functions)
    get_rules,
    get_decisions,
    get_sessions,
    get_tasks,
    NAVIGATION_ITEMS,
    RULE_CATEGORIES,
    RULE_STATUSES,
    get_initial_state,
    # Pure transforms
    TASK_STATUSES,  # GAP-UI-EXP-004
    TASK_PHASES,  # GAP-UI-EXP-004
    )

# View modules (extracted per GAP-FILE-001)
from agent.governance_ui.views import (
    build_rules_view,
    build_tasks_view,
    build_sessions_view,
    build_agents_view,
    build_decisions_view,
    build_executive_view,
    build_chat_view,
    build_backlog_view,
    build_monitor_view,
    build_trust_view,
    build_search_view,
    build_impact_view,
    build_infra_view,  # GAP-INFRA-004: Infrastructure health dashboard
    build_workflow_view,  # RD-WORKFLOW Phase 4: Workflow compliance dashboard
    build_audit_view,  # RD-DEBUG-AUDIT Phase 4: Audit trail dashboard
    build_tests_view,  # WORKFLOW-SHELL-01-v1: Self-assessment test runner
    build_metrics_view,  # SESSION-METRICS-01-v1: Session analytics dashboard
    build_trace_bar,  # GAP-UI-048: Bottom trace bar
    build_all_dialogs,  # GAP-UI-038: Shared dialogs
)

# Controller modules (extracted per GAP-FILE-005)
from agent.governance_ui.controllers import register_all_controllers

# Project paths
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DOCS_DIR = PROJECT_ROOT / "docs"


class GovernanceDashboard:
    """
    Governance Dashboard for sim-ai platform.

    Thin view layer (per DSP FP + Digital Twin paradigm).
    All data access and state management delegated to governance_ui package.

    Provides UI views for:
    - Rules browser (grouped by category)
    - Decisions viewer
    - Sessions timeline
    - Tasks tracker
    - Evidence search
    """

    def __init__(self, port: int = 8081):
        """
        Initialize Governance Dashboard.

        Args:
            port: Port for Trame server (default 8081)
        """
        self.port = port
        self._server = None
        self._state = None

    # =========================================================================
    # TRAME SERVER
    # =========================================================================

    def build_ui(self):
        """
        Build complete Trame UI layout.

        Per UI-FIRST-SPRINT-WORKFLOW.md: All components have data-testid for POM testing.
        Per RULE-004: Page Object Model (POM) pattern.

        GAPs addressed:
        - GAP-UI-001: data-testid attributes
        - GAP-UI-002: CRUD forms
        - GAP-UI-003: Detail drill-down
        - GAP-UI-006: rule_id column
        - GAP-UI-007: Clickable rows
        - GAP-FILE-001: View extraction (refactored 2024-12-28)
        """
        try:
            from trame.app import get_server
            from trame.ui.vuetify3 import VAppLayout
            from trame.widgets import vuetify3 as v3, html

            self._server = get_server(client_type="vue3", name="governance-dashboard")
            self._state = self._server.state

            # Initialize state (from package pure function)
            for key, value in get_initial_state().items():
                setattr(self._state, key, value)

            # Load initial data (from package pure functions)
            self._state.rules = get_rules()
            self._state.decisions = get_decisions()
            self._state.sessions = get_sessions(limit=100)
            # Load tasks with pagination to prevent DOM explosion (GAP-UI-PAGING-001)
            try:
                import httpx
                page_size = 20  # Must match tasks_per_page default in state/initial.py
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(f"{API_BASE_URL}/api/tasks", params={"limit": page_size, "offset": 0})
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and "items" in data:
                            self._state.tasks = data["items"]
                            self._state.tasks_pagination = data.get("pagination", {})
                        else:
                            self._state.tasks = data[:page_size] if len(data) > page_size else data
                            self._state.tasks_pagination = {"total": len(data), "offset": 0, "limit": page_size, "has_more": len(data) > page_size, "returned": min(len(data), page_size)}
                    else:
                        self._state.tasks = get_tasks()
            except Exception:
                self._state.tasks = get_tasks()

            # Agent Task Backlog state (TODO-6)
            self._state.available_tasks = []
            self._state.claimed_tasks = []
            self._state.backlog_agent_id = ""

            # Controller for handling UI events
            ctrl = self._server.controller

            # =================================================================
            # REGISTER ALL CONTROLLERS (GAP-FILE-005)
            # Controllers extracted to governance_ui/controllers/ modules
            # =================================================================
            loaders = register_all_controllers(self._state, ctrl, API_BASE_URL)

            # Store loaders for view change handler
            load_trust_data = loaders['load_trust_data']
            load_monitor_data = loaders['load_monitor_data']
            load_backlog_data = loaders['load_backlog_data']
            load_executive_report_data = loaders['load_executive_report_data']
            load_infra_status = loaders['load_infra_status']
            load_workflow_status = loaders['load_workflow_status']
            load_tests_data = loaders['load_tests_data']
            load_sessions_list = loaders['load_sessions_list']
            load_metrics_data = loaders['load_metrics_data']

            # Initialize additional state for forms and filters
            self._state.show_rule_detail = False
            self._state.show_rule_form = False
            self._state.rule_form_mode = "create"
            self._state.rules_status_filter = None
            self._state.rules_category_filter = None
            self._state.rules_search_query = ""
            self._state.rules_sort_column = "rule_id"
            self._state.rules_sort_asc = True

            # GAP-UI-027 fix: Filter options as state for proper VSelect binding
            self._state.status_options = RULE_STATUSES  # ['ACTIVE', 'DRAFT', 'DEPRECATED']
            self._state.category_options = RULE_CATEGORIES  # ['governance', 'technical', 'operational']
            # GAP-UI-EXP-004: Task filter options
            self._state.task_status_options = TASK_STATUSES  # ['TODO', 'IN_PROGRESS', 'DONE', 'BLOCKED']
            self._state.task_phase_options = TASK_PHASES  # ['P10', 'P11', 'P12', 'R&D', ...]

            # Form field states - Rules
            self._state.form_rule_id = ""
            self._state.form_rule_title = ""
            self._state.form_rule_directive = ""
            self._state.form_rule_category = "governance"
            self._state.form_rule_priority = "HIGH"

            # Form field states - Tasks
            self._state.show_task_form = False
            self._state.form_task_id = ""
            self._state.form_task_description = ""
            self._state.form_task_phase = "P10"
            self._state.form_task_agent = ""

            # Detail view states - Tasks
            self._state.selected_task = None
            self._state.show_task_detail = False
            self._state.edit_task_mode = False
            self._state.edit_task_description = ""
            self._state.edit_task_phase = "P10"
            self._state.edit_task_status = "TODO"
            self._state.edit_task_agent = ""

            # Detail view states - Sessions
            self._state.selected_session = None
            self._state.show_session_detail = False

            # Detail view states - Decisions
            self._state.selected_decision = None
            self._state.show_decision_detail = False

            # Executive Reports state (GAP-UI-044)
            self._state.executive_report = None
            self._state.executive_loading = False
            self._state.executive_period = "week"

            # Agent Chat state (ORCH-006)
            self._state.chat_messages = []
            self._state.chat_input = ""
            self._state.chat_loading = False
            self._state.chat_selected_agent = None
            self._state.chat_session_id = None
            self._state.chat_task_id = None

            # File Viewer state (GAP-DATA-003)
            self._state.show_file_viewer = False
            self._state.file_viewer_path = ""
            self._state.file_viewer_content = ""
            self._state.file_viewer_loading = False
            self._state.file_viewer_error = ""

            # Task Execution Viewer state (ORCH-007)
            self._state.task_execution_log = []
            self._state.task_execution_loading = False
            self._state.show_task_execution = False

            # Test Runner state (WORKFLOW-SHELL-01-v1)
            self._state.tests_loading = False
            self._state.tests_running = False
            self._state.tests_current_run = None
            self._state.tests_recent_runs = []

            # =================================================================
            # STATE CHANGE HANDLER - Auto-load data on view change (P11.1 fix)
            # Fixes GAP-UI-035: UI views don't auto-load data on open
            # =================================================================
            @self._state.change("active_view")
            def on_view_change(active_view, **kwargs):
                """Auto-load data when view changes."""
                if active_view == 'trust':
                    load_trust_data()
                elif active_view == 'monitor':
                    load_monitor_data()
                elif active_view == 'agents':
                    # Load agents data via trust data loader
                    load_trust_data()
                elif active_view == 'impact':
                    # Ensure rules are loaded for impact analysis
                    if not self._state.rules or len(self._state.rules) == 0:
                        self._state.rules = get_rules()
                elif active_view == 'backlog':
                    # Load available tasks for agent backlog (TODO-6)
                    load_backlog_data()
                elif active_view == 'executive':
                    # Auto-load sessions list for dropdown (UI-AUDIT-007 fix)
                    load_sessions_list()
                    # Auto-load executive report on view change (GAP-UI-044)
                    load_executive_report_data()
                elif active_view == 'infra':
                    # Auto-load infrastructure status (GAP-UI-EXP-006 fix)
                    load_infra_status()
                elif active_view == 'workflow':
                    # Auto-load workflow compliance status (GAP-UI-EXP-011 fix)
                    load_workflow_status()
                elif active_view == 'tests':
                    # Auto-load test results (WORKFLOW-SHELL-01-v1)
                    load_tests_data()
                elif active_view == 'metrics':
                    # Auto-load session metrics (SESSION-METRICS-01-v1)
                    load_metrics_data()

            with VAppLayout(
                self._server,
                full_height=True,
                theme=("dark_mode ? 'dark' : 'light'",)
            ) as layout:
                # Inject mermaid.js for diagram rendering (RULE-039)
                from agent.governance_ui.components.mermaid import inject_mermaid_script
                inject_mermaid_script()

                # Inject window state isolator (GAP-UI-AUDIT-002: Option C)
                from agent.governance_ui.components.window_state import inject_window_state_isolator
                inject_window_state_isolator()

                # App bar with data-testid
                with v3.VAppBar(
                    color="deep-purple",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "app-bar"}
                ):
                    v3.VAppBarTitle(APP_TITLE)
                    v3.VSpacer()
                    v3.VChip(
                        "{{ rules.length }} Rules | {{ decisions.length }} Decisions",
                        size="small",
                        color="white",
                        variant="outlined",
                    )
                    v3.VBtn(
                        icon="mdi-refresh",
                        variant="text",
                        click="trigger('refresh_data')",
                        title="Refresh data from API",
                        __properties=["data-testid"],
                        **{"data-testid": "refresh-btn"}
                    )
                    # Dark mode toggle (GAP-UI-DARK-THEME)
                    v3.VSwitch(
                        v_model="dark_mode",
                        prepend_icon="mdi-theme-light-dark",
                        hide_details=True,
                        density="compact",
                        color="white",
                        __properties=["data-testid"],
                        **{"data-testid": "dark-mode-toggle"}
                    )

                # Navigation drawer with data-testid
                with v3.VNavigationDrawer(
                    permanent=True,
                    rail=True,
                    __properties=["data-testid"],
                    **{"data-testid": "nav-drawer"}
                ):
                    with v3.VList(nav=True, density="compact"):
                        for item in NAVIGATION_ITEMS:
                            v3.VListItem(
                                title=item['title'],
                                prepend_icon=item['icon'],
                                value=item['value'],
                                active=(f"active_view === '{item['value']}'",),
                                click=f"active_view = '{item['value']}'",
                                __properties=["data-testid"],
                                **{"data-testid": f"nav-{item['value']}"}
                            )

                # Main content
                with v3.VMain():
                    with v3.VContainer(fluid=True, classes="fill-height pa-4"):
                        # =============================================================
                        # VIEWS (extracted per GAP-FILE-001, per RULE-012)
                        # Each view manages its own v_if visibility based on active_view
                        # =============================================================
                        build_rules_view()
                        build_tasks_view()
                        build_sessions_view()
                        build_decisions_view()
                        build_agents_view()
                        build_executive_view()
                        build_chat_view()
                        build_backlog_view()
                        build_monitor_view()
                        build_trust_view()
                        build_search_view()
                        build_impact_view()
                        build_infra_view()
                        build_workflow_view()
                        build_audit_view()
                        build_tests_view()
                        build_metrics_view()

                    # =============================================================
                    # SHARED DIALOGS (GAP-UI-038)
                    # =============================================================
                    build_all_dialogs()

                # =================================================================
                # LOADING SPINNER - GAP-UI-005
                # =================================================================
                with v3.VOverlay(
                    v_model="is_loading",
                    persistent=True,
                    classes="align-center justify-center",
                    __properties=["data-testid"],
                    **{"data-testid": "loading-overlay"}
                ):
                    v3.VProgressCircular(
                        indeterminate=True,
                        size=64,
                        __properties=["data-testid"],
                        **{"data-testid": "loading-spinner"}
                    )

                # =================================================================
                # ERROR BANNER - GAP-UI-005
                # =================================================================
                v3.VSnackbar(
                    v_model="has_error",
                    color="error",
                    timeout=5000,
                    __properties=["data-testid"],
                    **{"data-testid": "error-banner"}
                )

                # =================================================================
                # CONFIRM DIALOG
                # =================================================================
                with v3.VDialog(
                    v_model="show_confirm",
                    max_width=400,
                    __properties=["data-testid"],
                    **{"data-testid": "confirm-dialog"}
                ):
                    with v3.VCard():
                        v3.VCardTitle("Confirm Action")
                        v3.VCardText("{{ confirm_message }}")
                        with v3.VCardActions():
                            v3.VSpacer()
                            v3.VBtn(
                                "No",
                                variant="text",
                                click="show_confirm = false",
                                __properties=["data-testid"],
                                **{"data-testid": "confirm-no"}
                            )
                            v3.VBtn(
                                "Yes",
                                color="primary",
                                click="confirm_action(); show_confirm = false",
                                __properties=["data-testid"],
                                **{"data-testid": "confirm-yes"}
                            )

                # FILE VIEWER DIALOG: Now provided by build_all_dialogs() from views/dialogs.py
                # Per GAP-UI-038: Fullscreen modal for document viewing

                # =================================================================
                # TRACE BAR - GAP-UI-048
                # Bottom bar with technical traces for developer visibility
                # =================================================================
                build_trace_bar()

            # Initialize additional state for dialogs
            self._state.has_error = False
            self._state.show_confirm = False
            self._state.confirm_message = ""

            return self._server

        except ImportError:
            print("Trame not installed. Run: pip install trame trame-vuetify trame-client")
            return None

    def run(self, port: int = None):
        """
        Run Trame dashboard server.

        Args:
            port: Override port
        """
        if port:
            self.port = port

        server = self.build_ui()
        if server:
            print(f"Starting Governance Dashboard on port {self.port}")
            server.start(port=self.port, open_browser=True)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_governance_dashboard(port: int = 8081) -> GovernanceDashboard:
    """
    Factory function to create Governance Dashboard.

    Args:
        port: UI port

    Returns:
        GovernanceDashboard instance
    """
    return GovernanceDashboard(port=port)


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run Governance Dashboard standalone."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--port", type=int, default=8081, help="UI port")
    parser.add_argument("--server", action="store_true", help="Run in server mode (no browser)")
    args = parser.parse_args()

    # In Docker or when --server flag is passed, don't open browser
    server_mode = args.server or os.environ.get("TRAME_DEFAULT_HOST") == "0.0.0.0"

    dashboard = create_governance_dashboard(port=args.port)
    server = dashboard.build_ui()
    if server:
        print(f"Starting Governance Dashboard on port {args.port}")
        # timeout=0 keeps server running indefinitely (no idle exit)
        server.start(port=args.port, open_browser=not server_mode, timeout=0)


if __name__ == "__main__":
    main()
