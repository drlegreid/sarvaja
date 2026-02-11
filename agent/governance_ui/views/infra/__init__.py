"""
Infrastructure Health Dashboard View Package.

Per GAP-INFRA-004: Docker/Podman health dashboard.
Per DOC-SIZE-01-v1: Split from infra_view.py (710 lines).

Created: 2026-02-11
"""

from trame.widgets import vuetify3 as v3

from .services import build_infra_header, build_services_grid
from .stats import build_system_stats
from .mcp import build_mcp_status_panel, build_mcp_detail_dialog
from .panels import (
    build_dsp_alert,
    build_python_procs_panel,
    build_logs_panel,
    build_recovery_panel,
)


def build_infra_view() -> None:
    """Build the Infrastructure Health Dashboard view.

    Main entry point for the infra view module.
    Per GAP-INFRA-004: Docker/Podman health dashboard.
    """
    with v3.VCard(
        v_if="active_view === 'infra'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "infra-dashboard"}
    ):
        build_infra_header()

        with v3.VCardText():
            build_dsp_alert()
            build_services_grid()
            build_system_stats()
            build_mcp_status_panel()
            build_python_procs_panel()
            build_logs_panel()
            build_recovery_panel()

    # MCP detail dialog (C.2) - must be outside VCard
    build_mcp_detail_dialog()


__all__ = [
    "build_infra_view",
    "build_infra_header",
    "build_services_grid",
    "build_system_stats",
    "build_mcp_status_panel",
    "build_mcp_detail_dialog",
    "build_dsp_alert",
    "build_python_procs_panel",
    "build_logs_panel",
    "build_recovery_panel",
]
