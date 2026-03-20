#!/usr/bin/env python3
"""
Auto-Save — Direct ChromaDB context save from hooks.

Per P3-13 (Context Prevention Wiring): Enables automatic context saving
when entropy reaches critical thresholds, without requiring Claude to act.

Connects directly to ChromaDB (localhost:8001) and saves a session context
document with entropy state, git info, and recent tool history.

Usage:
    # From entropy_cli.py when --auto-save is enabled:
    from auto_save import auto_save_context

    # Standalone test:
    python auto_save.py --test
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

HOOKS_DIR = Path(__file__).parent
PROJECT_DIR = HOOKS_DIR.parent.parent
ENTROPY_STATE_FILE = HOOKS_DIR / ".entropy_state.json"

CHROMADB_HOST = os.environ.get("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.environ.get("CHROMADB_PORT", "8001"))
COLLECTION_NAME = "claude_memories"


def _get_chromadb_collection():
    """Get ChromaDB collection for saving context."""
    try:
        import chromadb
        client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Claude-mem memories for AMNESIA recovery"}
        )
    except Exception:
        return None


def _get_entropy_state() -> dict:
    """Read current entropy state."""
    try:
        if ENTROPY_STATE_FILE.exists():
            return json.loads(ENTROPY_STATE_FILE.read_text())
    except Exception:
        pass
    return {}


def _get_git_info() -> dict:
    """Get current git branch and recent commits."""
    info = {"branch": "unknown", "recent_commits": []}
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=3, cwd=str(PROJECT_DIR)
        )
        info["branch"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, timeout=3, cwd=str(PROJECT_DIR)
        )
        info["recent_commits"] = result.stdout.strip().split("\n")
    except Exception:
        pass
    return info


def _get_modified_files() -> list:
    """Get recently modified tracked files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~3", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(PROJECT_DIR)
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split("\n") if f]
            return files[:20]  # Cap at 20 files
    except Exception:
        pass
    return []


def auto_save_context(trigger: str = "entropy_threshold") -> Optional[str]:
    """
    Save session context to ChromaDB automatically.

    Args:
        trigger: What triggered the auto-save (for audit trail)

    Returns:
        Context document ID if successful, None on failure
    """
    collection = _get_chromadb_collection()
    if collection is None:
        return None

    entropy = _get_entropy_state()
    git_info = _get_git_info()
    modified_files = _get_modified_files()

    tool_count = entropy.get("tool_count", 0)
    session_start = entropy.get("session_start", datetime.now().isoformat())
    session_hash = entropy.get("session_hash", "0000")
    recent_tools = entropy.get("recent_tools", [])

    # Build session ID from entropy state
    try:
        date_str = datetime.fromisoformat(session_start).strftime("%Y-%m-%d")
    except Exception:
        date_str = datetime.now().strftime("%Y-%m-%d")

    session_id = f"SESSION-{date_str}-AUTO-{session_hash}"
    doc_id = f"ctx-{session_id}"

    # Build context document
    tool_summary = ""
    if recent_tools:
        from collections import Counter
        counts = Counter(recent_tools)
        top_tools = counts.most_common(5)
        tool_summary = ", ".join(f"{t}({c})" for t, c in top_tools)

    context = f"""# Auto-Saved Session: {session_id}
Project: sarvaja-platform
Date: {datetime.now().isoformat()}
Trigger: {trigger}

## Session State
- Tool calls: {tool_count}
- Session start: {session_start}
- Branch: {git_info['branch']}
- Top tools: {tool_summary or 'N/A'}

## Recent Commits
{chr(10).join(f'- {c}' for c in git_info['recent_commits'][:5])}

## Files Modified
{chr(10).join(f'- {f}' for f in modified_files[:15]) or '- None tracked'}
"""

    metadata = {
        "type": "session_context",
        "session_id": session_id,
        "project": "sarvaja-platform",
        "trigger": trigger,
        "tool_count": tool_count,
        "file_count": len(modified_files),
        "auto_saved": "true",
    }

    try:
        collection.upsert(
            ids=[doc_id],
            documents=[context],
            metadatas=[metadata],
        )
        return doc_id
    except Exception:
        return None


def recover_recent_contexts(n_results: int = 3) -> list:
    """
    Recover recent session contexts from ChromaDB.

    Args:
        n_results: Number of recent contexts to retrieve

    Returns:
        List of context documents (dicts with id, document, metadata)
    """
    collection = _get_chromadb_collection()
    if collection is None:
        return []

    try:
        results = collection.query(
            query_texts=["sarvaja-platform session context recent"],
            n_results=n_results,
            where={"type": "session_context"},
        )

        contexts = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                ctx = {
                    "id": results["ids"][0][i] if results.get("ids") else "",
                    "document": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                }
                contexts.append(ctx)
        return contexts
    except Exception:
        return []


def main():
    """CLI entry point for testing."""
    if "--test" in sys.argv:
        print("Testing auto-save...")
        doc_id = auto_save_context(trigger="manual_test")
        if doc_id:
            print(f"Saved: {doc_id}")
        else:
            print("Failed to save (ChromaDB may be unavailable)")

        print("\nTesting recover...")
        contexts = recover_recent_contexts(n_results=2)
        print(f"Found {len(contexts)} recent contexts")
        for ctx in contexts:
            print(f"  - {ctx['id']}: {ctx['metadata'].get('session_id', '?')}")
    else:
        # Default: auto-save
        doc_id = auto_save_context()
        if doc_id:
            print(f"Auto-saved: {doc_id}", file=sys.stderr)


if __name__ == "__main__":
    main()
