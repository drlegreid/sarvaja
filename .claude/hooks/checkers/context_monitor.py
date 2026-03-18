"""
Context Monitor for Claude Code sessions.

Per GAP-CONTEXT-MEASUREMENT-001: Track actual context window usage.

Captures context_window metrics from Claude Code hook data:
- total_input_tokens
- total_output_tokens
- context_window_size
- used_percentage
- remaining_percentage

Usage:
    # As hook (stdin receives JSON from Claude Code)
    python context_monitor.py --capture

    # Status check
    python context_monitor.py --status
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# State file location
STATE_FILE = Path(__file__).parent.parent / ".context_state.json"


def get_default_state() -> Dict[str, Any]:
    """Get default context state."""
    return {
        "last_updated": datetime.now().isoformat(),
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "context_window_size": 200000,
        "used_percentage": 0.0,
        "remaining_percentage": 100.0,
        "tool_count": 0,
        "history": []
    }


def load_state() -> Dict[str, Any]:
    """Load context state from file."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return get_default_state()


def save_state(state: Dict[str, Any]) -> None:
    """Save context state to file."""
    try:
        state["last_updated"] = datetime.now().isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        sys.stderr.write(f"Error saving context state: {e}\n")


def capture_context(hook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture context_window metrics from hook data.

    Args:
        hook_data: JSON data from Claude Code hook

    Returns:
        Updated state dictionary
    """
    state = load_state()

    # Extract context_window if present
    context_window = hook_data.get("context_window", {})

    if context_window:
        state["total_input_tokens"] = context_window.get("total_input_tokens", 0)
        state["total_output_tokens"] = context_window.get("total_output_tokens", 0)
        state["context_window_size"] = context_window.get("context_window_size", 200000)
        state["used_percentage"] = context_window.get("used_percentage", 0.0)
        state["remaining_percentage"] = context_window.get("remaining_percentage", 100.0)

        # Add to history (keep last 20 entries)
        history = state.get("history", [])
        history.append({
            "timestamp": datetime.now().isoformat(),
            "used_pct": state["used_percentage"],
            "input_tokens": state["total_input_tokens"],
            "output_tokens": state["total_output_tokens"]
        })
        state["history"] = history[-20:]

    # Increment tool count
    state["tool_count"] = state.get("tool_count", 0) + 1

    save_state(state)
    return state


def get_level(used_pct: float) -> str:
    """Get context level based on usage percentage."""
    if used_pct >= 90:
        return "CRITICAL"
    elif used_pct >= 75:
        return "HIGH"
    elif used_pct >= 50:
        return "MEDIUM"
    else:
        return "LOW"


def format_status(state: Dict[str, Any]) -> str:
    """Format status for display."""
    used_pct = state.get("used_percentage", 0.0)
    input_tokens = state.get("total_input_tokens", 0)
    output_tokens = state.get("total_output_tokens", 0)
    context_size = state.get("context_window_size", 200000)
    tool_count = state.get("tool_count", 0)
    level = get_level(used_pct)

    lines = [
        f"Context Level: {level}",
        f"Used: {used_pct:.1f}%",
        f"Input Tokens: {input_tokens:,}",
        f"Output Tokens: {output_tokens:,}",
        f"Window Size: {context_size:,}",
        f"Tool Calls: {tool_count}",
    ]

    last_updated = state.get("last_updated")
    if last_updated:
        lines.append(f"Last Updated: {last_updated}")

    return "\n".join(lines)


def check_warning(state: Dict[str, Any]) -> Optional[str]:
    """Check if warning should be issued based on context usage."""
    used_pct = state.get("used_percentage", 0.0)
    input_tokens = state.get("total_input_tokens", 0)

    if used_pct >= 90:
        return (
            f"[CONTEXT CRITICAL] {used_pct:.0f}% full ({input_tokens:,} tokens)\n"
            f"SAVE CONTEXT NOW! Use chroma_save_session_context() or /compact"
        )
    elif used_pct >= 75:
        return (
            f"[CONTEXT HIGH] {used_pct:.0f}% full ({input_tokens:,} tokens)\n"
            f"Consider saving context or compacting soon."
        )
    elif used_pct >= 50:
        return (
            f"[CONTEXT MEDIUM] {used_pct:.0f}% full ({input_tokens:,} tokens)\n"
            f"Monitor usage - consider saving at natural breakpoints."
        )

    return None


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Context monitor for Claude Code")
    parser.add_argument("--capture", action="store_true", help="Capture context from stdin hook data")
    parser.add_argument("--status", action="store_true", help="Show current context status")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--reset", action="store_true", help="Reset context state")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress OK messages")

    args = parser.parse_args()

    try:
        if args.capture:
            # Read hook data from stdin
            hook_data = {}
            try:
                stdin_data = sys.stdin.read()
                if stdin_data:
                    hook_data = json.loads(stdin_data)
            except json.JSONDecodeError:
                pass

            state = capture_context(hook_data)

            # Check for warning
            warning = check_warning(state)
            if warning:
                # BUG-188-004: Use stderr + exit(0) — exit(1) blocks UserPromptSubmit
                print(warning, file=sys.stderr)
                sys.exit(0)

            if not args.quiet:
                print(f"[CONTEXT {get_level(state.get('used_percentage', 0))}] {state.get('used_percentage', 0):.0f}%")
            sys.exit(0)

        elif args.status:
            state = load_state()
            if args.json:
                print(json.dumps(state, indent=2))
            else:
                print(format_status(state))
            sys.exit(0)

        elif args.reset:
            state = get_default_state()
            save_state(state)
            print("Context state reset")
            sys.exit(0)

        else:
            # Default: just show brief status
            state = load_state()
            used_pct = state.get("used_percentage", 0.0)
            print(f"Context: {used_pct:.1f}% | {state.get('total_input_tokens', 0):,} tokens")
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
