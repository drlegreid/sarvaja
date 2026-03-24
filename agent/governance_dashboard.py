"""
Governance Dashboard UI — Trame view layer.

Per DOC-SIZE-01-v1: Layout in governance_dashboard_layout.py.
Controllers in governance_ui/controllers/, views in governance_ui/views/.
"""

import logging
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

# Layout builder (extracted per DOC-SIZE-01-v1)
from agent.governance_dashboard_layout import build_dashboard_layout  # noqa: F401

# Controller modules (extracted per GAP-FILE-005)
from agent.governance_ui.controllers import register_all_controllers
from agent.governance_ui.controllers.routing import register_routing_controller

# Project paths
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DOCS_DIR = PROJECT_ROOT / "docs"

logger = logging.getLogger(__name__)


class GovernanceDashboard:
    """
    Governance Dashboard for sim-ai platform.

    Thin view layer (per DSP FP + Digital Twin paradigm).
    All data access and state management delegated to governance_ui package.
    """

    def __init__(self, port: int = 8081):
        self.port = port
        self._server = None
        self._state = None

    def _inject_html_script(self, script_src: str) -> None:
        """Inject a <script src> into Trame's HTML template before </body>."""
        import trame_client
        www_dir = Path(trame_client.__file__).parent / "module" / "vue3-www"
        index_html = www_dir / "index.html"
        if not index_html.exists():
            return
        content = index_html.read_text()
        tag = f'<script src="{script_src}"></script>'
        if tag in content:
            return
        content = content.replace("</body>", f"  {tag}\n  </body>")
        index_html.write_text(content)

    def build_ui(self):
        """Build complete Trame UI layout."""
        try:
            from trame.app import get_server

            self._server = get_server(client_type="vue3", name="governance-dashboard")
            self._state = self._server.state

            static_dir = str(Path(__file__).parent / "governance_ui" / "static")
            self._server.serve["govstatic"] = static_dir
            self._inject_html_script("/govstatic/window_isolator.js")
            self._inject_html_script("/govstatic/route_sync.js")

            for key, value in get_initial_state().items():
                setattr(self._state, key, value)

            load_initial_data(
                self._state, API_BASE_URL,
                get_rules, get_decisions, get_sessions, get_tasks,
            )

            init_form_and_detail_states(self._state)

            ctrl = self._server.controller

            # Register controllers (GAP-FILE-005)
            loaders = register_all_controllers(self._state, ctrl, API_BASE_URL)

            # Register routing controller (FEAT-008: Named URI routing)
            # Per SRVJ-FEAT-015: api_base_url enables deep link entity loading
            route_bridge = register_routing_controller(
                self._state, ctrl, api_base_url=API_BASE_URL,
            )

            load_trust_data = loaders['load_trust_data']
            load_monitor_data = loaders['load_monitor_data']
            load_backlog_data = loaders['load_backlog_data']
            load_executive_report_data = loaders['load_executive_report_data']
            load_infra_status = loaders['load_infra_status']
            load_workflow_status = loaders['load_workflow_status']
            load_tests_data = loaders['load_tests_data']
            load_sessions_list = loaders['load_sessions_list']
            load_metrics_data = loaders['load_metrics_data']
            load_audit_trail = loaders['load_audit_trail']
            load_rules = loaders.get('load_rules')
            load_tasks_page = loaders.get('load_tasks_page')
            load_workspaces = loaders.get('load_workspaces')

            # Auto-load data on view change (P11.1 fix / GAP-UI-035)
            @self._state.change("active_view")
            def on_view_change(active_view, **kwargs):
                """Auto-load data when view changes.

                Per BUG-012: Skip reset when cross-nav guard set.
                Per FEAT-008: Handle _pending_entity_id from browser back/forward.
                """
                is_cross_nav = getattr(self._state, 'cross_nav_in_progress', False)
                pending_id = getattr(self._state, '_pending_entity_id', None)

                if is_cross_nav:
                    # BUG-012: Skip all side effects — navigate_to_* already
                    # set state; additional changes cause Trame flush races.
                    self._state.cross_nav_in_progress = False
                    # SRVJ-FEAT-016: Push route hash so URL updates after
                    # cross-nav (navigate_to_session/task). Without this,
                    # browser back/forward has nothing to go back to.
                    self._state.route_hash = route_bridge.state_to_hash(
                        self._state,
                    )
                    return
                elif pending_id:
                    # FEAT-008: Browser back/forward with pending entity ID
                    self._state._pending_entity_id = None
                    self._state.has_error = False
                    self._state.error_message = ''
                    _load_pending_entity(active_view, pending_id)
                else:
                    # Normal tab switch — reset detail flags (BUG-UI-STALE-DETAIL-001)
                    self._state.show_session_detail = False
                    self._state.show_task_detail = False
                    self._state.show_rule_detail = False
                    self._state.show_decision_detail = False
                    self._state.show_session_form = False
                    self._state.show_rule_form = False
                    self._state.show_decision_form = False
                    # GAP-OVERLAY-SCRIM: Also reset workspace state on tab switch
                    self._state.show_workspace_detail = False
                    self._state.show_workspace_form = False
                    self._state.has_error = False
                    self._state.error_message = ''
                    # BUG-017b: Clear selected entity to prevent stale detail on return
                    self._state.selected_task = None
                    self._state.selected_session = None
                    # BUG-017c: Clear nav_source to prevent stale "Back to" button
                    self._state.nav_source_view = None
                    self._state.nav_source_id = None
                    self._state.nav_source_label = None
                    # BUG-017: Force Trame reactivity after clearing detail flags
                    for _f in ("show_session_detail", "show_task_detail",
                               "show_rule_detail", "show_decision_detail"):
                        self._state.dirty(_f)

                # Load data + push route (normal tab switch / pending entity)
                _load_view_data(active_view)
                self._state.route_hash = route_bridge.state_to_hash(self._state)

            # SRVJ-FEAT-015: Push route hash when detail view opens/closes.
            # on_view_change only fires on active_view change, but detail
            # opens (task row click) don't change active_view.
            @self._state.change(
                "show_task_detail", "show_session_detail",
                "show_rule_detail", "show_decision_detail",
            )
            def on_detail_flag_change(**kwargs):
                # Skip during route-originated changes: hash_to_state sets
                # _pending_entity_id AND detail flags in one batch. If we
                # push hash now, selected_* is still None → wrong hash
                # overwrites the URL and causes a cascade via hashchange.
                if getattr(self._state, '_pending_entity_id', None):
                    return
                self._state.route_hash = route_bridge.state_to_hash(
                    self._state,
                )

            def _load_pending_entity(view: str, entity_id: str):
                """FEAT-008: Load entity from API for browser back/forward."""
                from agent.governance_ui.controllers.tasks_navigation import (
                    _load_session_from_api, _load_task_from_api,
                )
                if view == 'sessions':
                    data = _load_session_from_api(API_BASE_URL, entity_id)
                    if data:
                        self._state.selected_session = data
                        self._state.show_session_detail = True
                elif view == 'tasks':
                    data = _load_task_from_api(API_BASE_URL, entity_id)
                    if data:
                        self._state.selected_task = data
                        self._state.show_task_detail = True

            def _load_view_data(active_view: str):
                """Load data lists for the active view."""
                if active_view == 'trust':
                    load_trust_data()
                elif active_view == 'monitor':
                    load_monitor_data()
                elif active_view == 'agents':
                    load_trust_data()
                elif active_view == 'impact':
                    if not self._state.rules or len(self._state.rules) == 0:
                        self._state.rules = get_rules()
                elif active_view == 'sessions':
                    load_sessions_list()
                elif active_view == 'tasks':
                    if load_tasks_page:
                        load_tasks_page()
                elif active_view == 'executive':
                    load_sessions_list()
                    load_executive_report_data()
                elif active_view == 'infra':
                    load_infra_status()
                elif active_view == 'workflow':
                    load_workflow_status()
                elif active_view == 'tests':
                    load_tests_data()
                elif active_view == 'metrics':
                    load_metrics_data()
                elif active_view == 'audit':
                    load_audit_trail()
                elif active_view == 'rules':
                    if load_rules:
                        load_rules()
                elif active_view == 'workspaces':
                    if load_workspaces:
                        load_workspaces()

            # Build layout (extracted per DOC-SIZE-01-v1)
            build_dashboard_layout(self._server, NAVIGATION_ITEMS)

            init_dialog_states(self._state)

            return self._server

        except ImportError:
            logger.error("Trame not installed. Run: pip install trame trame-vuetify trame-client")
            return None

    def run(self, port: int = None):
        """Run Trame dashboard server."""
        if port:
            self.port = port
        server = self.build_ui()
        if server:
            logger.info("Starting Governance Dashboard on port %s", self.port)
            server.start(port=self.port, open_browser=True)


def create_governance_dashboard(port: int = 8081) -> GovernanceDashboard:
    """Factory function to create Governance Dashboard."""
    return GovernanceDashboard(port=port)


def main():
    """Run Governance Dashboard standalone."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--port", type=int, default=8081, help="UI port")
    parser.add_argument("--server", action="store_true", help="Run in server mode (no browser)")
    args = parser.parse_args()

    server_mode = args.server or os.environ.get("TRAME_DEFAULT_HOST") == "0.0.0.0"

    dashboard = create_governance_dashboard(port=args.port)
    server = dashboard.build_ui()
    if server:
        print(f"Starting Governance Dashboard on port {args.port}")
        server.start(port=args.port, open_browser=not server_mode, timeout=0)


if __name__ == "__main__":
    main()
