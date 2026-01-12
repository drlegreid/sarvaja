"""
Recovery audit logging for Claude Code hooks.

Per user request: Transparency, resiliency, debugability.
Provides:
- Audit trail of recovery attempts
- Callback mechanism for local LLM agent notification
- Structured logs for debugging
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class RecoveryAuditLog:
    """
    Audit logger for recovery operations.

    Stores recovery attempts with:
    - Timestamp
    - Action attempted
    - Result (success/failure)
    - Error details if failed
    - Resolution hints
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit logs (default: ~/.claude/recovery_logs/)
        """
        self.log_dir = log_dir or Path.home() / ".claude" / "recovery_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    @property
    def current_log_file(self) -> Path:
        """Get path to current day's log file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"recovery-{date_str}.jsonl"

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for recovery failures.

        Args:
            callback: Function to call on failure with audit entry dict
        """
        self._callbacks.append(callback)

    def log_attempt(
        self,
        action: str,
        success: bool,
        services: List[str],
        error: Optional[str] = None,
        resolution_hint: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Log a recovery attempt.

        Args:
            action: What was attempted (e.g., "start_containers", "reset_containers")
            success: Whether the action succeeded
            services: Services involved
            error: Error message if failed
            resolution_hint: Suggested fix for the error
            duration_ms: How long the operation took

        Returns:
            The audit entry that was logged
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "success": success,
            "services": services,
            "error": error,
            "resolution_hint": resolution_hint,
            "duration_ms": duration_ms,
            "log_file": str(self.current_log_file)
        }

        # Write to audit log
        with open(self.current_log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Trigger callbacks on failure
        if not success and self._callbacks:
            for callback in self._callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass  # Don't let callback failures break recovery

        return entry

    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent failed recovery attempts.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of failed recovery entries, newest first
        """
        failures = []

        # Read from current day's log first
        if self.current_log_file.exists():
            with open(self.current_log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if not entry.get("success", True):
                            failures.append(entry)
                    except json.JSONDecodeError:
                        pass

        # Sort by timestamp descending and limit
        failures.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return failures[:limit]

    def format_for_llm(self, entry: Dict[str, Any]) -> str:
        """
        Format an audit entry for LLM agent notification.

        Args:
            entry: Audit entry dict

        Returns:
            Human-readable string for LLM context
        """
        lines = [
            f"## Recovery Failure Alert",
            f"",
            f"**Time:** {entry.get('timestamp', 'unknown')}",
            f"**Action:** {entry.get('action', 'unknown')}",
            f"**Services:** {', '.join(entry.get('services', []))}",
            f"**Error:** {entry.get('error', 'No error details')}",
            f"",
            f"### Resolution Hint",
            f"{entry.get('resolution_hint', 'No resolution hint available')}",
            f"",
            f"### Audit Log Location",
            f"`{entry.get('log_file', 'unknown')}`",
            f"",
            f"### Recommended Actions",
            f"1. Check container logs: `podman logs <container>`",
            f"2. Check system journal: `journalctl --user -u podman.socket`",
            f"3. Review audit log: `tail -20 {entry.get('log_file', '')}`",
        ]
        return "\n".join(lines)


# Default singleton instance
_default_audit_log: Optional[RecoveryAuditLog] = None


def get_audit_log() -> RecoveryAuditLog:
    """Get the default audit log instance."""
    global _default_audit_log
    if _default_audit_log is None:
        _default_audit_log = RecoveryAuditLog()
    return _default_audit_log


def log_recovery_attempt(
    action: str,
    success: bool,
    services: List[str],
    error: Optional[str] = None,
    resolution_hint: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to log a recovery attempt.

    Uses the default audit log instance.
    """
    return get_audit_log().log_attempt(
        action=action,
        success=success,
        services=services,
        error=error,
        resolution_hint=resolution_hint,
        duration_ms=duration_ms
    )
