"""
Checkers module for Claude Code hooks.

Provides service health checking, entropy monitoring, amnesia detection,
intent continuity tracking, and zombie process detection.

Platform: Linux (xubuntu) with Podman - migrated 2026-01-09
"""

from .services import ServiceChecker, check_port, check_podman_running, check_container
from .services import check_podman_running as check_docker_running  # backward compat alias
from .entropy import EntropyChecker
from .amnesia import AmnesiaDetector
from .intent_checker import check_intent_continuity, get_intent_status, format_intent_for_healthcheck
from .zombies import check_zombie_processes, cleanup_zombie_pids

__all__ = [
    "ServiceChecker",
    "check_port",
    "check_podman_running",
    "check_docker_running",  # backward compat alias
    "check_container",
    "EntropyChecker",
    "AmnesiaDetector",
    # RD-INTENT Phase 3
    "check_intent_continuity",
    "get_intent_status",
    "format_intent_for_healthcheck",
    # GAP-ZOMBIE-001
    "check_zombie_processes",
    "cleanup_zombie_pids",
]
