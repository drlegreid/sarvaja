#!/usr/bin/env python3
"""
Context Preload Hook — SessionStart.

Loads strategic context (decisions, tech choices, active phase, open gaps,
recent sessions) at session start and injects it as additionalContext.

Also recovers recent session contexts from ChromaDB (P3-13) to restore
awareness of previous session work across compactions and restarts.

Per GAP-CONTEXT-PREVENT: Wire context preloader into SessionStart.
Per RECOVER-AMNES-01-v1: Autonomous context recovery.
Per P3-13: ChromaDB context recovery on session start.

Created: 2026-02-15
Updated: 2026-03-20 — Added ChromaDB recovery (P3-13)
"""

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
PROJECT_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(HOOKS_DIR))


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


def _recover_chromadb_contexts(limit: int = 3) -> list:
    """Recover recent session contexts from ChromaDB.

    Returns list of summary strings from saved contexts.
    """
    try:
        from auto_save import recover_recent_contexts
        contexts = recover_recent_contexts(n_results=limit)
        summaries = []
        for ctx in contexts:
            meta = ctx.get("metadata", {})
            sid = meta.get("session_id", "unknown")
            tool_count = meta.get("tool_count", "?")
            trigger = meta.get("trigger", "manual")
            summaries.append(f"- **{sid}** (tools: {tool_count}, trigger: {trigger})")
        return summaries
    except Exception:
        return []


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

    # Recent session context from evidence files
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

    # ChromaDB recovered contexts (P3-13)
    try:
        chroma_summaries = _recover_chromadb_contexts(limit=3)
        if chroma_summaries:
            parts.append("### Recovered Session Contexts (ChromaDB)")
            parts.extend(chroma_summaries)
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
