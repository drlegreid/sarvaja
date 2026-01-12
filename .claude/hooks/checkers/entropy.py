"""
Entropy monitoring for Claude Code sessions.

Per EPIC-006, RULE-024: Track session entropy to suggest context saves.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.base import HookConfig, HookResult, HealthLevel, DEFAULT_CONFIG
from ..core.state import EntropyState


class EntropyChecker:
    """
    Monitors session entropy (context accumulation) and suggests saves.

    Since Claude Code does NOT expose context usage APIs, uses heuristics:
    - Tool call count (proxy for context accumulation)
    - Session duration (time-based accumulation)

    Thresholds:
    - 50 tool calls: First warning (LOW)
    - 100 tool calls: Strong suggestion (HIGH)
    - 60 minutes: Time-based reminder
    """

    LOW_THRESHOLD = 50      # First gentle reminder
    HIGH_THRESHOLD = 100    # Strong save suggestion
    TIME_THRESHOLD = 60     # Minutes before time-based reminder

    def __init__(self, config: Optional[HookConfig] = None):
        """
        Initialize entropy checker.

        Args:
            config: Hook configuration (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.state_manager = EntropyState(self.config.entropy_file)

    def load_state(self) -> Dict[str, Any]:
        """Load current entropy state."""
        state = self.state_manager.load()
        if not state:
            state = self.state_manager.get_default_state()
        return state

    def get_session_minutes(self, state: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate session duration in minutes.

        Args:
            state: State dict (loads current if None)

        Returns:
            Session duration in minutes
        """
        if state is None:
            state = self.load_state()

        try:
            start_str = state.get("session_start", "")
            if start_str:
                start = datetime.fromisoformat(start_str)
                return (datetime.now() - start).total_seconds() / 60
        except Exception:
            pass
        return 0

    def get_entropy_level(self, state: Optional[Dict[str, Any]] = None) -> HealthLevel:
        """
        Determine current entropy level.

        Args:
            state: State dict (loads current if None)

        Returns:
            HealthLevel enum value
        """
        if state is None:
            state = self.load_state()

        tool_count = state.get("tool_count", 0)

        if tool_count >= self.HIGH_THRESHOLD:
            return HealthLevel.HIGH
        elif tool_count >= self.LOW_THRESHOLD:
            return HealthLevel.MEDIUM
        else:
            return HealthLevel.LOW

    def check(self) -> HookResult:
        """
        Check entropy and determine if a warning should be shown.

        Returns:
            HookResult with warning status and suggested action
        """
        state = self.load_state()
        tool_count = state.get("tool_count", 0)
        session_minutes = self.get_session_minutes(state)
        warnings_shown = state.get("warnings_shown", 0)
        last_warning_at = state.get("last_warning_at", 0)

        # Determine warning level
        warning_level = None
        message = None
        resolution_path = "Run /save to preserve context"

        # HIGH threshold - strong suggestion (but don't spam)
        if tool_count >= self.HIGH_THRESHOLD and tool_count - last_warning_at >= 20:
            warning_level = "HIGH"
            message = (
                f"[CONTEXT ENTROPY HIGH] {tool_count} tool calls, {int(session_minutes)}m session.\n"
                f"Run /save before complex tasks to preserve context."
            )
            # Update warning tracking
            state["last_warning_at"] = tool_count
            state["warnings_shown"] = warnings_shown + 1

        # LOW threshold - first gentle reminder
        elif tool_count >= self.LOW_THRESHOLD and warnings_shown == 0:
            warning_level = "LOW"
            message = (
                f"[CONTEXT CHECKPOINT] {tool_count} tool calls.\n"
                f"Consider /save at natural breakpoints."
            )
            state["warnings_shown"] = 1
            state["last_warning_at"] = tool_count

        # Time-based reminder (60 minutes)
        elif session_minutes >= self.TIME_THRESHOLD and warnings_shown < 2:
            warning_level = "TIME"
            message = (
                f"[SESSION DURATION] {int(session_minutes)} minutes active.\n"
                f"Consider /save if approaching milestone."
            )
            state["warnings_shown"] = 2

        # Save updated state if warning shown
        if warning_level:
            self.state_manager.save(
                state,
                add_history=True,
                history_entry={
                    "timestamp": datetime.now().isoformat(),
                    "event": f"WARNING_{warning_level}",
                    "tool_count": tool_count,
                    "session_hash": state.get("session_hash", "0000")
                }
            )
            return HookResult.warning(
                message,
                resolution_path=resolution_path,
                warning_level=warning_level,
                tool_count=tool_count,
                session_minutes=int(session_minutes)
            )

        return HookResult.ok(
            "Entropy within normal range",
            tool_count=tool_count,
            session_minutes=int(session_minutes),
            level=self.get_entropy_level(state).value
        )

    def increment_and_check(self) -> HookResult:
        """
        Increment tool count and check for warnings.

        This is the main entry point for PostToolUse hooks.

        Returns:
            HookResult with any warnings
        """
        state = self.load_state()
        state["tool_count"] = state.get("tool_count", 0) + 1
        state["check_count"] = state.get("check_count", 0) + 1

        # Save incremented state
        self.state_manager._state = state
        self.state_manager.save(state)

        # Now check for warnings
        return self.check()

    def reset(self) -> Dict[str, Any]:
        """
        Reset entropy state for a new session.

        Returns:
            New state dictionary
        """
        return self.state_manager.reset_session()

    def mark_saved(self) -> None:
        """Mark that a context save was performed."""
        self.state_manager.mark_saved()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current entropy status summary.

        Returns:
            Dictionary with entropy metrics
        """
        state = self.load_state()
        return {
            "entropy": self.get_entropy_level(state).value,
            "tool_count": state.get("tool_count", 0),
            "minutes": int(self.get_session_minutes(state)),
            "last_save": state.get("last_save"),
            "session_hash": state.get("session_hash", "0000")
        }
