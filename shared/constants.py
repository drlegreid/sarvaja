"""
Shared Application Constants for Sarvaja Governance Platform.

Per EPIC-DRY-001: Enforce DRY principle with shared constants.
Per DECISION-008: Project renamed from sim.ai to Sarvaja (2026-01-14).
Per GAP-TEST-PROFILES: Environment variables for container networking.

Single source of truth for:
- Application identity (name, title, version)
- Default ports and hosts (configurable via env vars for containers)
- Default timeouts

Usage:
    from shared.constants import APP_TITLE, DEFAULT_PORTS

    # In dashboard
    v3.VAppBarTitle(APP_TITLE)

    # In tests
    page.wait_for_selector(f"text={APP_TITLE}", timeout=DEFAULT_TIMEOUTS["page_load"])

Container Usage:
    # Inside container, services use container names:
    # TYPEDB_HOST=typedb CHROMADB_HOST=chromadb python3 -m pytest
"""
import os

# =============================================================================
# Application Identity
# =============================================================================

APP_NAME = "Sarvaja"
"""Short application name (Sanskrit: All-Knowing)."""

APP_TITLE = "Sarvaja Governance Dashboard"
"""Full application title shown in UI header."""

APP_VERSION = "1.3.1"
"""Current application version."""

PROJECT_REPO = "https://github.com/drlegreid/platform-gai"
"""GitHub repository URL."""


# =============================================================================
# Default Ports (configurable via environment variables for containers)
# =============================================================================

DEFAULT_PORTS = {
    "dashboard": int(os.getenv("DASHBOARD_PORT", "8081")),
    "api": int(os.getenv("API_PORT", "8082")),
    "typedb": int(os.getenv("TYPEDB_PORT", "1729")),
    "chromadb": int(os.getenv("CHROMADB_PORT", "8001")),  # Container internal: 8000
    "litellm": int(os.getenv("LITELLM_PORT", "4000")),
    "ollama": int(os.getenv("OLLAMA_PORT", "11434")),
}
"""Default ports for platform services. Override via env vars for container networking."""


# =============================================================================
# Default Hosts (configurable via environment variables for containers)
# =============================================================================

DEFAULT_HOSTS = {
    "dashboard": os.getenv("DASHBOARD_HOST", "localhost"),
    "api": os.getenv("API_HOST", "localhost"),
    "typedb": os.getenv("TYPEDB_HOST", "localhost"),
    "chromadb": os.getenv("CHROMADB_HOST", "localhost"),
    "litellm": os.getenv("LITELLM_HOST", "localhost"),
    "ollama": os.getenv("OLLAMA_HOST", "localhost"),
}
"""Default hosts for platform services. Override via env vars for container networking."""


# =============================================================================
# Default Timeouts (milliseconds)
# =============================================================================

DEFAULT_TIMEOUTS = {
    "page_load": 10000,      # 10 seconds for page load
    "element_wait": 5000,    # 5 seconds for element visibility
    "api_request": 30000,    # 30 seconds for API requests
    "typedb_query": 60000,   # 60 seconds for TypeDB queries
    "test_step": 15000,      # 15 seconds per test step
}
"""Default timeouts in milliseconds."""


# =============================================================================
# API Endpoints
# =============================================================================

API_BASE_URL = f"http://{DEFAULT_HOSTS['api']}:{DEFAULT_PORTS['api']}"
"""Base URL for API requests."""

DASHBOARD_URL = f"http://{DEFAULT_HOSTS['dashboard']}:{DEFAULT_PORTS['dashboard']}"
"""Base URL for dashboard."""


# =============================================================================
# Database Names
# =============================================================================

TYPEDB_DATABASE = "sim-ai-governance"
"""TypeDB database name."""

CHROMADB_COLLECTION = "claude_memories"
"""ChromaDB collection name for claude-mem."""
