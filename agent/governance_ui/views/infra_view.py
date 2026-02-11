"""
Infrastructure View for Governance Dashboard.

Per GAP-INFRA-004: Docker/Podman health dashboard.
Per DOC-SIZE-01-v1: Split into infra/ subpackage (710 -> 5 files).

Re-exports all public functions for backward compatibility.
"""

from .infra import (  # noqa: F401
    build_infra_view,
    build_infra_header,
    build_services_grid,
    build_system_stats,
    build_mcp_status_panel,
    build_mcp_detail_dialog,
    build_dsp_alert,
    build_python_procs_panel,
    build_logs_panel,
    build_recovery_panel,
)
from .infra.services import build_service_card  # noqa: F401
