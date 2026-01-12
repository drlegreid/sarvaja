"""
Recovery module for Claude Code hooks.

Provides auto-recovery capabilities for containers (runtime-agnostic),
plus audit logging for transparency and debugability.

Platform: Linux (xubuntu) with Podman - migrated 2026-01-11
Note: Docker support stubbed for future implementation.
"""

from .containers import ContainerRecovery, PodmanRecovery, DockerRecovery
from .audit import RecoveryAuditLog, get_audit_log, log_recovery_attempt

__all__ = [
    "ContainerRecovery",  # Primary class (runtime-agnostic)
    "PodmanRecovery",     # Backward compatibility alias
    "DockerRecovery",     # Backward compatibility alias
    "RecoveryAuditLog",
    "get_audit_log",
    "log_recovery_attempt",
]
