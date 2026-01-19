"""
Unit tests conftest - pytest configuration for unit tests.

Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-2-C:
Provides fixtures and configuration for MCP pre-flight unit tests.
"""

import sys
from pathlib import Path

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
