"""
Core module for Claude Code hooks.

Provides base classes, configuration, and shared utilities.
"""

from .base import (
    HookConfig,
    HookResult,
    ServiceInfo,
    HealthLevel,
    ServiceStatus,
    DEFAULT_CONFIG
)
from .state import (
    StateManager,
    HealthcheckState,
    EntropyState,
    compute_frankel_hash,
    compute_component_hash,
    compute_session_hash
)
from .formatters import OutputFormatter, HealthFormatter, EntropyFormatter

__all__ = [
    # Base classes
    "HookConfig",
    "HookResult",
    "ServiceInfo",
    "HealthLevel",
    "ServiceStatus",
    "DEFAULT_CONFIG",
    # State management
    "StateManager",
    "HealthcheckState",
    "EntropyState",
    "compute_frankel_hash",
    "compute_component_hash",
    "compute_session_hash",
    # Formatters
    "OutputFormatter",
    "HealthFormatter",
    "EntropyFormatter",
]
