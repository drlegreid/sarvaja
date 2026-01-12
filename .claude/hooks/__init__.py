"""
Claude Code Hooks - Health monitoring and session management.

Per EPIC-006, RULE-021, RULE-024: Provides non-blocking health checks,
entropy monitoring, and AMNESIA detection.

Directory Structure:
    hooks/
    ├── core/           # Base classes, state management, formatters
    ├── checkers/       # Health checks (services, entropy, amnesia)
    ├── recovery/       # Auto-recovery (containers - podman/docker)
    ├── healthcheck.py  # Main healthcheck entry point
    └── entropy_monitor.py  # Entropy tracking entry point

Usage:
    # From healthcheck.py
    from hooks.core import HookConfig, OutputFormatter
    from hooks.checkers import ServiceChecker, AmnesiaDetector
    from hooks.recovery import ContainerRecovery

    # Quick service check
    checker = ServiceChecker()
    result = checker.check_core()
"""

__version__ = "1.1.0"

# Re-export commonly used classes for convenience
from .core import (
    HookConfig,
    HookResult,
    OutputFormatter,
    HealthFormatter,
    EntropyFormatter,
    DEFAULT_CONFIG
)
from .checkers import ServiceChecker, EntropyChecker, AmnesiaDetector
from .recovery import ContainerRecovery, PodmanRecovery, DockerRecovery

__all__ = [
    "HookConfig",
    "HookResult",
    "OutputFormatter",
    "HealthFormatter",
    "EntropyFormatter",
    "DEFAULT_CONFIG",
    "ServiceChecker",
    "EntropyChecker",
    "AmnesiaDetector",
    "ContainerRecovery",  # Primary class
    "PodmanRecovery",     # Backward compat alias
    "DockerRecovery",     # Backward compat alias
]
