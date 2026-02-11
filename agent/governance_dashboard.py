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
    get_initial_state,
)
from agent.governance_ui.dashboard_data_loader import load_initial_data
from agent.governance_ui.dashboard_state_init import (
    init_form_and_detail_states,
    init_dialog_states,
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
    build_projects_view,  # GOV-PROJECT-01-v1: Project hierarchy navigation
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

    def _inject_html_script(self, script_src: str) -> None:
        """Inject a <script src> into Trame's HTML template before </body>.

        Neither html.Script() nor v-effect work in this Trame/Vue 3 build:
        - html.Script: Vue 3 strips <script> from component templates
        - v-effect: not a registered directive (only Vuetify directives exist)

        This patches the trame-client index.html directly at startup.
        """
        import trame_client
        www_dir = Path(trame_client.__file__).parent / "module" / "vue3-www"
        index_html = www_dir / "index.html"
        if not index_html.exists():
            return
        content = index_html.read_text()
        tag = f'<script src="{script_src}"></script>'
        if tag in content:
            return  # Already injected
        content = content.replace("</body>", f"  {tag}\n  </body>")
        index_html.write_text(content)

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

            # Serve static JS files (window isolator, etc.)
            static_dir = str(Path(__file__).parent / "governance_ui" / "static")
            self._server.serve["govstatic"] = static_dir

            # Inject window_isolator.js into Trame's HTML template
            # (html.Script doesn't work: Vue 3 strips <script> from templates)
            # (v-effect doesn't work: not a registered directive in this build)
            self._inject_html_script("/govstatic/window_isolator.js")

            # Initialize state (from package pure function)
            for key, value in get_initial_state().items():
                setattr(self._state, key, value)

            # Load initial data via REST API with MCP fallback
            # Per GAP-UI-PAGING-001: Use pagination to prevent DOM explosion
            load_initial_data(
                self._state, API_BASE_URL,
                get_rules, get_decisions, get_sessions, get_tasks,
            )

            # Initialize form fields, detail views, and filter options
            init_form_and_detail_states(self._state)

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

                # Inject list styles (UI-LIST-01: alternating rows, full-height containers)
                from agent.governance_ui.components.list_styles import inject_list_styles
                inject_list_styles()

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
                        "{{ rules.length }} Rules",
                        size="small",
                        color="white",
                        variant="outlined",
                        click="active_view = 'rules'",
                        style="cursor: pointer;",
                        __properties=["data-testid"],
                        **{"data-testid": "toolbar-rules-chip"}
                    )
                    v3.VChip(
                        "{{ decisions.length }} Decisions",
                        size="small",
                        color="white",
                        variant="outlined",
                        click="active_view = 'decisions'",
                        style="cursor: pointer;",
                        classes="ml-1",
                        __properties=["data-testid"],
                        **{"data-testid": "toolbar-decisions-chip"}
                    )
                    v3.VChip(
                        "{{ '#' + ((infra_stats && infra_stats.frankel_hash) || '').substring(0, 8) }}",
                        v_if="infra_stats && infra_stats.frankel_hash",
                        size="small",
                        variant="outlined",
                        prepend_icon=(
                            "infra_stats.status === 'healthy' ? 'mdi-shield-check' : "
                            "infra_stats.status === 'degraded' ? 'mdi-shield-alert' : "
                            "'mdi-shield-off'",
                        ),
                        click="active_view = 'infra'",
                        style="cursor: pointer;",
                        classes="ml-1",
                        color=(
                            "infra_stats.status === 'healthy' ? '#4caf50' : "
                            "infra_stats.status === 'degraded' ? '#ff9800' : "
                            "'#f44336'",
                        ),
                        title=(
                            "'Health: ' + (infra_stats.status || 'unknown') + "
                            "' | Last: ' + (infra_stats.last_check || 'Never')",
                        ),
                        __properties=["data-testid"],
                        **{"data-testid": "toolbar-health-chip"}
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
                        build_projects_view()

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

            # Initialize dialog states (after layout build)
            init_dialog_states(self._state)

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
