"""
Unit tests conftest - pytest configuration for unit tests.

Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-2-C:
Provides fixtures and configuration for MCP pre-flight unit tests.
"""

import sys
from pathlib import Path

import pytest

# Add project root and hooks to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
HOOKS_PATH = PROJECT_ROOT / ".claude" / "hooks"

# Check if hooks modules are available
HOOKS_AVAILABLE = False
try:
    if HOOKS_PATH.exists():
        sys.path.insert(0, str(PROJECT_ROOT / ".claude"))
        from hooks.core.base import HookResult  # noqa: F401
        HOOKS_AVAILABLE = True
except ImportError:
    HOOKS_AVAILABLE = False


@pytest.fixture(autouse=True)
def _clear_session_parse_cache():
    """Clear module-level caches between tests.

    Prevents cache bleed when multiple tests call get_session_detail()
    with mocked JSONL paths (mtime=0.0 for all mocks).
    Also clears the timeline cache from sessions_pagination to prevent
    cross-test pollution (BUG-TEST-ROT-01).
    """
    try:
        from governance.services.cc_session_cache import _session_cache
        _session_cache.clear()
    except ImportError:
        pass
    try:
        from agent.governance_ui.controllers.sessions_pagination import _timeline_cache
        _timeline_cache.clear()
    except ImportError:
        pass
