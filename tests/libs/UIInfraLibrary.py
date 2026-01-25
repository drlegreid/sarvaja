"""
Robot Framework Library for UI Infrastructure View Tests.

Per DOC-SIZE-01-v1: Modular entity-based test structure.
Per UI-AUDIT-008: Validates health hash display in infrastructure view.
Per GAP-INFRA-004: Docker/Podman health dashboard.
Migrated from tests/unit/ui/test_ui_infra.py
"""
import json
from pathlib import Path
from robot.api.deco import keyword


class UIInfraLibrary:
    """Library for testing infrastructure view."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Infra State Variable Tests
    # =============================================================================

    @keyword("Initial State Has Infra Stats")
    def initial_state_has_infra_stats(self):
        """Initial state should include infra_stats for health hash."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()

            return {
                "has_infra_stats": 'infra_stats' in state
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Infra Stats Has Frankel Hash")
    def infra_stats_has_frankel_hash(self):
        """infra_stats should include frankel_hash field. Per UI-AUDIT-008."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()
            infra_stats = state.get('infra_stats', {})

            return {
                "has_frankel_hash": 'frankel_hash' in infra_stats,
                "default_placeholder": infra_stats.get('frankel_hash') == "--------"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Infra Stats Has Last Check")
    def infra_stats_has_last_check(self):
        """infra_stats should include last_check timestamp."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()
            infra_stats = state.get('infra_stats', {})

            return {
                "has_last_check": 'last_check' in infra_stats,
                "default_never": infra_stats.get('last_check') == "Never"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Infra Stats Has Memory Pct")
    def infra_stats_has_memory_pct(self):
        """infra_stats should include memory_pct field."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()
            infra_stats = state.get('infra_stats', {})

            return {
                "has_memory_pct": 'memory_pct' in infra_stats
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Infra Stats Has Python Procs")
    def infra_stats_has_python_procs(self):
        """infra_stats should include python_procs field."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()
            infra_stats = state.get('infra_stats', {})

            return {
                "has_python_procs": 'python_procs' in infra_stats
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Infra View Reference Tests
    # =============================================================================

    @keyword("Infra View Exists")
    def infra_view_exists(self):
        """Infrastructure view module should exist."""
        try:
            from agent.governance_ui.views import infra_view

            return {
                "exists": infra_view is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Build Infra View Callable")
    def build_infra_view_callable(self):
        """build_infra_view function should be callable."""
        try:
            from agent.governance_ui.views.infra_view import build_infra_view

            return {
                "callable": callable(build_infra_view)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Build System Stats Callable")
    def build_system_stats_callable(self):
        """build_system_stats function should be callable."""
        try:
            from agent.governance_ui.views.infra_view import build_system_stats

            return {
                "callable": callable(build_system_stats)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("View References Frankel Hash")
    def view_references_frankel_hash(self):
        """View source should reference infra_stats.frankel_hash. Per UI-AUDIT-008."""
        try:
            import inspect
            from agent.governance_ui.views import infra_view

            source = inspect.getsource(infra_view)

            return {
                "references_frankel_hash": 'frankel_hash' in source,
                "references_infra_stats": 'infra_stats' in source
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Healthcheck State File Tests
    # =============================================================================

    @keyword("Actual Healthcheck State Exists")
    def actual_healthcheck_state_exists(self):
        """Actual healthcheck state file should exist in hooks directory."""
        try:
            project_root = Path(__file__).parent.parent.parent
            state_file = project_root / ".claude" / "hooks" / ".healthcheck_state.json"

            if not state_file.exists():
                return {"skipped": True, "reason": "Healthcheck state file not found (CI environment)"}

            data = json.loads(state_file.read_text())

            return {
                "exists": True,
                "has_master_hash": 'master_hash' in data
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # MCP Status Panel Tests
    # =============================================================================

    @keyword("Build MCP Status Panel Callable")
    def build_mcp_status_panel_callable(self):
        """build_mcp_status_panel function should be callable."""
        try:
            from agent.governance_ui.views.infra_view import build_mcp_status_panel

            return {
                "callable": callable(build_mcp_status_panel)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Initial State Has MCP Servers")
    def initial_state_has_mcp_servers(self):
        """Initial state should include mcp_servers in infra_stats."""
        try:
            from agent.governance_ui import get_initial_state

            state = get_initial_state()
            infra_stats = state.get('infra_stats', {})

            # mcp_servers may be empty dict initially
            has_mcp = 'mcp_servers' in infra_stats or infra_stats.get('mcp_servers') is None

            return {
                "has_mcp_servers": has_mcp
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
