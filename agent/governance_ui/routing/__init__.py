"""
Routing package for Sarvaja Governance Dashboard.

Per FEAT-008: Named URI routing for dashboard navigation and shareability.
Provides hash-based URL routing with bidirectional state sync.

Usage:
    from agent.governance_ui.routing import parse_hash, build_hash, RouteState, RouteRegistry
"""

from .models import RouteState, RouteConfig
from .parser import parse_hash
from .builder import build_hash
from .registry import RouteRegistry

__all__ = [
    "RouteState",
    "RouteConfig",
    "parse_hash",
    "build_hash",
    "RouteRegistry",
]
