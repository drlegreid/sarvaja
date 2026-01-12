"""
Output formatters for Claude Code hooks.

Per EPIC-006: Provides consistent JSON output for context injection.
"""

import json
from typing import Any, Dict, List, Optional

from .base import HookResult, ServiceInfo, HealthLevel


class OutputFormatter:
    """
    Formats hook output for Claude Code context injection.

    All output MUST be valid JSON to avoid blocking Claude Code.
    """

    @staticmethod
    def to_json(context: str, hook_event: str = "SessionStart") -> str:
        """
        Format context string as JSON for Claude Code.

        Args:
            context: The context string to inject
            hook_event: The hook event name (SessionStart, PostToolUse, etc.)

        Returns:
            JSON string for stdout
        """
        output = {
            "hookSpecificOutput": {
                "hookEventName": hook_event,
                "additionalContext": context
            }
        }
        return json.dumps(output)

    @staticmethod
    def empty() -> str:
        """Return empty JSON (no context injection)."""
        return json.dumps({})

    @staticmethod
    def print_json(context: str, hook_event: str = "SessionStart") -> None:
        """Print formatted JSON to stdout."""
        print(OutputFormatter.to_json(context, hook_event))

    @staticmethod
    def print_empty() -> None:
        """Print empty JSON to stdout."""
        print(OutputFormatter.empty())


class HealthFormatter:
    """
    Formats healthcheck output with detailed service status.
    """

    @staticmethod
    def format_detailed(
        services: Dict[str, Dict[str, Any]],
        master_hash: str,
        core_services: List[str],
        recovery_actions: Optional[List[str]] = None,
        amnesia: Optional[Dict[str, Any]] = None,
        component_hashes: Optional[Dict[str, str]] = None,
        entropy: Optional[Dict[str, Any]] = None,
        resolution_path: Optional[str] = None
    ) -> str:
        """
        Format detailed healthcheck output.

        Args:
            services: Service status dictionary
            master_hash: Master state hash
            core_services: List of required service names
            recovery_actions: Actions taken for recovery
            amnesia: AMNESIA detection results
            component_hashes: Per-component hashes
            entropy: Session entropy state
            resolution_path: Instructions to fix issues
        """
        lines = [f"=== MCP DEPENDENCY CHAIN [Hash: {master_hash}] ===", ""]

        required_ok = all(services.get(s, {}).get("ok", False) for s in core_services)

        # Required services
        lines.append("Required Services (CORE MCPs):")
        for name in core_services:
            data = services.get(name, {})
            status = data.get("status", "UNKNOWN")
            port = data.get("port", "")
            port_str = f" (:{port})" if port else ""
            icon = "✓" if data.get("ok") else "✗"
            comp_hash = component_hashes.get(name, "????") if component_hashes else "????"
            lines.append(f"  {icon} {name.upper()}{port_str}: {status} [{comp_hash}]")

        # Optional services
        lines.append("")
        lines.append("Optional Services:")
        for name in ["litellm", "ollama"]:
            if name not in core_services:
                data = services.get(name, {})
                status = data.get("status", "UNKNOWN")
                port = data.get("port", "")
                port_str = f" (:{port})" if port else ""
                icon = "✓" if data.get("ok") else "○"
                comp_hash = component_hashes.get(name, "????") if component_hashes else "????"
                lines.append(f"  {icon} {name.upper()}{port_str}: {status} [{comp_hash}]")

        # Session entropy
        if entropy:
            lines.append("")
            lines.append("Session Entropy:")
            tool_count = entropy.get("tool_count", 0)
            minutes = entropy.get("minutes", 0)
            level = entropy.get("entropy", "UNKNOWN")
            last_save = entropy.get("last_save")

            if level == "HIGH":
                lines.append(f"  ⚠️ Tools: {tool_count} | Duration: {minutes}m | Level: {level}")
                lines.append("  Action: Run /save before complex tasks")
            elif level == "MEDIUM":
                lines.append(f"  Tools: {tool_count} | Duration: {minutes}m | Level: {level}")
                lines.append("  Consider: /save at next milestone")
            else:
                lines.append(f"  Tools: {tool_count} | Duration: {minutes}m | Level: {level}")

            if last_save:
                lines.append(f"  Last save: {last_save[:19]}")

        # AMNESIA detection
        if amnesia and amnesia.get("detected"):
            lines.append("")
            lines.append(f"⚠️ AMNESIA RISK: {int(amnesia['confidence']*100)}% confidence")
            lines.append(f"  Indicators: {', '.join(amnesia['indicators'])}")
            lines.append("  Action: Run /remember sim-ai to restore context")

        # Recovery actions
        if recovery_actions:
            lines.append("")
            lines.append("Auto-Recovery:")
            for action in recovery_actions:
                lines.append(f"  → {action}")
            lines.append("  (Run /health again in 30-60s to verify)")
        elif not required_ok:
            lines.append("")
            # Show resolution path for user/LLM to fix
            if resolution_path:
                lines.append(f"Resolution: {resolution_path}")
            else:
                lines.append("Manual Recovery: .\\deploy.ps1 -Action up -Profile cpu")

        return "\n".join(lines)

    @staticmethod
    def format_summary(
        services: Dict[str, Dict[str, Any]],
        master_hash: str,
        core_services: List[str],
        reason: str = "",
        recovery_actions: Optional[List[str]] = None,
        resolution_path: Optional[str] = None
    ) -> str:
        """Format summary output for unchanged state or retry ceiling."""
        required_ok = all(services.get(s, {}).get("ok", False) for s in core_services)

        if required_ok:
            return f"[HEALTH OK] Hash: {master_hash} {reason}. MCP chain ready."
        else:
            failed = [s for s in core_services if not services.get(s, {}).get("ok", False)]
            if recovery_actions:
                recovery_str = " | " + "; ".join(recovery_actions)
                return f"[HEALTH RECOVERING] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{recovery_str}"
            else:
                hint = f" | Resolution: {resolution_path}" if resolution_path else " | Recovery: .\\deploy.ps1 -Action up"
                return f"[HEALTH WARN] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{hint}"

    @staticmethod
    def format_cached(prev_state: Dict[str, Any], core_services: List[str]) -> str:
        """Format cached response when retry ceiling reached."""
        master_hash = prev_state.get("master_hash", "????????")
        components = prev_state.get("components", {})

        failed = [s for s, status in components.items()
                  if status not in ("OK", "OFF") and s in core_services]

        if failed:
            return (f"[CACHED] Hash: {master_hash} (retry ceiling reached). "
                   f"Down: {', '.join(failed)} | Recovery: .\\deploy.ps1 -Action up")
        else:
            return f"[CACHED] Hash: {master_hash} (retry ceiling reached). MCP chain ready."


class EntropyFormatter:
    """
    Formats entropy monitoring output.
    """

    @staticmethod
    def format_warning(
        level: str,
        tool_count: int,
        session_minutes: int,
        resolution_path: Optional[str] = None
    ) -> str:
        """
        Format entropy warning message.

        Args:
            level: Warning level (LOW, HIGH, TIME)
            tool_count: Current tool call count
            session_minutes: Session duration in minutes
            resolution_path: Instructions to address high entropy
        """
        if level == "HIGH":
            msg = (f"[CONTEXT ENTROPY HIGH] {tool_count} tool calls, {session_minutes}m session.\n"
                   f"Run /save before complex tasks to preserve context.")
        elif level == "LOW":
            msg = (f"[CONTEXT CHECKPOINT] {tool_count} tool calls.\n"
                   f"Consider /save at natural breakpoints.")
        elif level == "TIME":
            msg = (f"[SESSION DURATION] {session_minutes} minutes active.\n"
                   f"Consider /save if approaching milestone.")
        else:
            msg = f"[ENTROPY] Tools: {tool_count}, Duration: {session_minutes}m"

        if resolution_path:
            msg += f"\nResolution: {resolution_path}"

        return msg

    @staticmethod
    def format_status(tool_count: int, session_minutes: int) -> str:
        """Format entropy status message."""
        return f"[ENTROPY] Tools: {tool_count}, Duration: {session_minutes}m"
