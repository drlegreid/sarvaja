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
Per DOC-SIZE-01-v1: Layout in governance_dashboard_layout.py.

Structure (per DSP):
    governance_ui/data_access.py  - Pure MCP data functions
    governance_ui/state/          - Immutable state, transforms (GAP-FILE-004)
    governance_ui/controllers/    - Trame controller modules (GAP-FILE-005)
    governance_ui/views/          - Extracted view modules (12 modules)
    governance_dashboard.py       - Trame view layer (this file)

Dependencies:
    pip install trame trame-vuetify trame-client
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

            # Serve static JS files
            static_dir = str(Path(__file__).parent / "governance_ui" / "static")
            self._server.serve["govstatic"] = static_dir
            self._inject_html_script("/govstatic/window_isolator.js")

            # Initialize state
            for key, value in get_initial_state().items():
                setattr(self._state, key, value)

            # Load initial data via REST API with MCP fallback
            load_initial_data(
                self._state, API_BASE_URL,
                get_rules, get_decisions, get_sessions, get_tasks,
            )

            init_form_and_detail_states(self._state)

            ctrl = self._server.controller

            # Register controllers (GAP-FILE-005)
            loaders = register_all_controllers(self._state, ctrl, API_BASE_URL)

            load_trust_data = loaders['load_trust_data']
            load_monitor_data = loaders['load_monitor_data']
            load_backlog_data = loaders['load_backlog_data']
            load_executive_report_data = loaders['load_executive_report_data']
            load_infra_status = loaders['load_infra_status']
            load_workflow_status = loaders['load_workflow_status']
            load_tests_data = loaders['load_tests_data']
            load_sessions_list = loaders['load_sessions_list']
            load_metrics_data = loaders['load_metrics_data']

            # Auto-load data on view change (P11.1 fix / GAP-UI-035)
            @self._state.change("active_view")
            def on_view_change(active_view, **kwargs):
                """Auto-load data when view changes."""
                if active_view == 'trust':
                    load_trust_data()
                elif active_view == 'monitor':
                    load_monitor_data()
                elif active_view == 'agents':
                    load_trust_data()
                elif active_view == 'impact':
                    if not self._state.rules or len(self._state.rules) == 0:
                        self._state.rules = get_rules()
                elif active_view == 'backlog':
                    load_backlog_data()
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
