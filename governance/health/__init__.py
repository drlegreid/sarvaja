"""
Shared Health Check Module
==========================
Common health check functions used by both hooks and MCP servers.

Per RULE-021: MCP Healthcheck Protocol
Per GAP-MCP-002: MCP dependency management

Usage:
    from governance.health import check_all_services, check_typedb, check_chromadb
"""

from governance.health.checks import (
    check_port,
    check_typedb,
    check_chromadb,
    check_podman,
    check_governance_api,
    check_all_services,
    are_core_services_healthy,
    get_failed_services,
    ServiceStatus,
    CORE_SERVICES,
)

from governance.health.amnesia import (
    check_amnesia_indicators,
    AmnesiaResult,
)

__all__ = [
    "check_port",
    "check_typedb",
    "check_chromadb",
    "check_podman",
    "check_governance_api",
    "check_all_services",
    "are_core_services_healthy",
    "get_failed_services",
    "ServiceStatus",
    "CORE_SERVICES",
    "check_amnesia_indicators",
    "AmnesiaResult",
]
