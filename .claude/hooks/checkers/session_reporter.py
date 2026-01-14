"""
Session Reporter Checker
========================
Detects session-end signals and reminds about reporting rules.

Per REPORT-HUMOR-01-v1 (RULE-046): Session Wisdom & Humor
Per REPORT-ISSUE-01-v1 (RULE-049): GitHub Issue Protocol

Triggers:
- UserPromptSubmit: Keywords like "done", "bye", "end session", "closing"
- Stop hook: When session explicitly ends

Created: 2026-01-14
"""

import json
import sys
import os
from typing import Optional

# Session-end signal keywords
END_SIGNALS = [
    "done", "bye", "goodbye", "end session", "closing", "wrapping up",
    "that's all", "thats all", "i'm done", "im done", "finishing",
    "call it a day", "session end", "end of session", "signing off",
    "thanks for today", "that will be all", "we're done", "were done"
]

def check_for_end_signal(user_input: str) -> bool:
    """Check if user input signals session end."""
    lower_input = user_input.lower().strip()

    # Direct match for short inputs
    if lower_input in ["done", "bye", "goodbye", "thanks"]:
        return True

    # Phrase match for longer inputs
    for signal in END_SIGNALS:
        if signal in lower_input:
            return True

    return False


def generate_reminder() -> str:
    """Generate session reporting reminder per RULE-046 & RULE-049."""
    reminder = """
[SESSION-END REMINDER]

Per REPORT-HUMOR-01-v1 (RULE-046) & REPORT-ISSUE-01-v1 (RULE-049):

Before closing, consider:

1. **Session Wisdom (RULE-046)**
   Include a contextually relevant Zen koan or insight based on session activities.

2. **GitHub Issue (RULE-049)**
   Create a STATUS or CERT issue depending on milestone completion:
   - STATUS: `[STATUS]: {epoch}: {koan_name}` - Tactical update
   - CERT: `[CERT]: {epoch}: {koan_name}` - Strategic milestone

Run `/report` to generate full session closure with templates.
""".strip()
    return reminder


def output_json(context: str) -> None:
    """Output valid JSON for Claude Code context injection."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context
        }
    }
    print(json.dumps(output))


def main():
    """Main entry point for UserPromptSubmit hook."""
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No input or invalid JSON - skip silently
        output_json("")
        return

    # Get user message from prompt
    user_message = input_data.get("prompt", {}).get("content", "")

    if not user_message:
        output_json("")
        return

    # Check for session-end signals
    if check_for_end_signal(user_message):
        reminder = generate_reminder()
        output_json(reminder)
    else:
        # No end signal - empty output (no injection)
        output_json("")


if __name__ == "__main__":
    main()
