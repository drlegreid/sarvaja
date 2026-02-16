#!/usr/bin/env python3
"""
Context Preload Hook — SessionStart.

Loads strategic context (decisions, tech choices, active phase, open gaps,
recent sessions) at session start and injects it as additionalContext.

Per GAP-CONTEXT-PREVENT: Wire context preloader into SessionStart.
Per RECOVER-AMNES-01-v1: Autonomous context recovery.

Created: 2026-02-15
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _get_recent_sessions(evidence_dir: Path, limit: int = 5) -> list:
    """Get most recent session evidence files for context."""
    if not evidence_dir.is_dir():
        return []
    files = []
    for fp in evidence_dir.glob("SESSION-*.md"):
        # Skip chat test artifacts
        name = fp.name
        if "-CHAT-TEST" in name or "-CHAT-FAIL" in name or "-CHAT-BOOM" in name:
            continue
        files.append((fp.stat().st_mtime, fp.stem))
    files.sort(reverse=True)
    return [name for _, name in files[:limit]]


def main():
    """Load strategic context and output as additionalContext JSON."""
    parts = []

    try:
        from governance.context_preloader import preload_session_context

        context = preload_session_context(force_refresh=True)
        prompt = context.to_agent_prompt()
        if prompt.strip():
            parts.append(prompt)
    except Exception as e:
        parts.append(f"[Context preload partial] Decisions/tech: {e}")

    # Recent session context
    try:
        evidence_dir = PROJECT_ROOT / "evidence"
        recent = _get_recent_sessions(evidence_dir)
        if recent:
            parts.append("### Recent Sessions")
            for name in recent:
                parts.append(f"- {name}")
            parts.append("")
    except Exception:
        pass

    # Open gaps count from GAP-INDEX
    try:
        gap_index = PROJECT_ROOT / "docs" / "gaps" / "GAP-INDEX.md"
        if gap_index.exists():
            import re
            content = gap_index.read_text(encoding="utf-8")
            open_count = len(re.findall(r"\|\s*OPEN\s*\|", content))
            if open_count:
                parts.append(f"### Open Gaps: {open_count}")
                parts.append("")
    except Exception:
        pass

    if not parts:
        sys.exit(0)

    output = "\n".join(parts)
    result = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": output,
        }
    }
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
