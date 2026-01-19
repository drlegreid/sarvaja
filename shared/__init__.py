"""
Shared constants and utilities for Sarvaja Governance Platform.

Per EPIC-DRY-001: Enforce DRY principle with shared constants.

Modules:
- constants: Application constants (APP_TITLE, VERSION, PORTS)
- urls: API endpoint patterns
- locators: UI element selectors (for tests)

Usage:
    from shared.constants import APP_TITLE, DEFAULT_PORTS
    from shared.urls import API_ENDPOINTS
"""

from shared.constants import (
    APP_TITLE,
    APP_NAME,
    APP_VERSION,
    DEFAULT_PORTS,
    DEFAULT_TIMEOUTS,
)

__all__ = [
    "APP_TITLE",
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_PORTS",
    "DEFAULT_TIMEOUTS",
]
