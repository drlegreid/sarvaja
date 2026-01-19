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

    Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-3-B:
    Since Claude Code does NOT expose context usage APIs, uses heuristics:
    - Tool call count (proxy for context accumulation)
    - Session duration (time-based accumulation)

    Thresholds:
    - 50 tool calls: First warning (MEDIUM) - consider saving
    - 100 tool calls: Strong suggestion (HIGH) - save now
    - 150 tool calls: Critical warning (CRITICAL) - stop and save
    - 60 minutes: Time-based reminder
    """

    MEDIUM_THRESHOLD = 50     # First gentle reminder
    HIGH_THRESHOLD = 100      # Strong save suggestion
    CRITICAL_THRESHOLD = 150  # STOP and save immediately
    TIME_THRESHOLD = 60       # Minutes before time-based reminder

    # Alias for backwards compatibility
    LOW_THRESHOLD = MEDIUM_THRESHOLD

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

        if tool_count >= self.CRITICAL_THRESHOLD:
            return HealthLevel.CRITICAL
        elif tool_count >= self.HIGH_THRESHOLD:
            return HealthLevel.HIGH
        elif tool_count >= self.MEDIUM_THRESHOLD:
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

        # CRITICAL threshold - STOP and save (every 25 calls)
        if tool_count >= self.CRITICAL_THRESHOLD and tool_count - last_warning_at >= 25:
            warning_level = "CRITICAL"
            message = (
                f"[CONTEXT ENTROPY CRITICAL] {tool_count} tool calls, {int(session_minutes)}m session.\n"
                f"SAVE CONTEXT NOW! Use chroma_save_session_context() before compaction."
            )
            state["last_warning_at"] = tool_count
            state["warnings_shown"] = warnings_shown + 1
            resolution_path = "CRITICAL: Save to ChromaDB immediately"

        # HIGH threshold - strong suggestion (but don't spam)
        elif tool_count >= self.HIGH_THRESHOLD and tool_count - last_warning_at >= 20:
            warning_level = "HIGH"
            message = (
                f"[CONTEXT ENTROPY HIGH] {tool_count} tool calls, {int(session_minutes)}m session.\n"
                f"Run /save before complex tasks to preserve context."
            )
            # Update warning tracking
            state["last_warning_at"] = tool_count
            state["warnings_shown"] = warnings_shown + 1

        # MEDIUM threshold - first gentle reminder
        elif tool_count >= self.MEDIUM_THRESHOLD and warnings_shown == 0:
            warning_level = "MEDIUM"
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


# =============================================================================
# CLI ENTRY POINT (for PostToolUse hooks)
# =============================================================================

def main():
    """
    CLI entry point for entropy monitoring.

    Usage:
        python entropy.py --increment    # Increment and check (PostToolUse)
        python entropy.py --status       # Get current status
        python entropy.py --reset        # Reset for new session

    Exit codes:
        0 - OK (no warning)
        1 - Warning issued (non-blocking)
        2 - Error
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Entropy monitoring for Claude Code")
    parser.add_argument("--increment", action="store_true", help="Increment tool count and check")
    parser.add_argument("--status", action="store_true", help="Get current entropy status")
    parser.add_argument("--reset", action="store_true", help="Reset entropy state")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress OK messages")

    args = parser.parse_args()

    try:
        checker = EntropyChecker()

        if args.increment:
            result = checker.increment_and_check()
            if result.is_warning:
                print(result.message)
                sys.exit(1)  # Non-blocking warning
            elif not args.quiet:
                status = checker.get_status()
                print(f"[ENTROPY {status['entropy'].upper()}] {status['tool_count']} calls")
            sys.exit(0)

        elif args.status:
            status = checker.get_status()
            print(f"Entropy: {status['entropy']}")
            print(f"Tool calls: {status['tool_count']}")
            print(f"Session: {status['minutes']} minutes")
            if status['last_save']:
                print(f"Last save: {status['last_save']}")
            sys.exit(0)

        elif args.reset:
            checker.reset()
            print("Entropy state reset for new session")
            sys.exit(0)

        else:
            # Default: just check without incrementing
            result = checker.check()
            if result.is_warning:
                print(result.message)
                sys.exit(1)
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
