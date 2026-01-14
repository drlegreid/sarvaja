"""
Frankel Hash Evidence System - Content-Addressable State Verification

Per FH-001-008: R&D-FRANKEL-HASH.md
Per RULE-022: Evidence-based wisdom extension

Features:
- FH-001: Content hashing at chunk level
- FH-002: Merkle tree structure for hierarchical change detection
- FH-007: State change detection for dashboard display

Created: 2026-01-14
"""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: Text content to hash

    Returns:
        64-character hex string (SHA-256)
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_chunk_hashes(content: str, level: int = 1) -> List[Dict[str, Any]]:
    """Compute hashes at different chunk levels.

    Args:
        content: Full document content
        level: Chunking level:
            0 = Document (single hash)
            1 = Sections (split by ## headers)
            2 = Paragraphs (split by blank lines)
            3 = Lines

    Returns:
        List of chunk dicts with hash, content, start_line
    """
    if level == 0:
        return [{
            "hash": compute_hash(content),
            "content": content[:100] + "..." if len(content) > 100 else content,
            "start_line": 1,
            "level": 0
        }]

    chunks = []
    lines = content.split('\n')

    if level == 1:
        # Section level - split by markdown headers
        current_section = []
        section_start = 1

        for i, line in enumerate(lines, 1):
            if line.startswith('# ') or line.startswith('## '):
                if current_section:
                    section_content = '\n'.join(current_section)
                    chunks.append({
                        "hash": compute_hash(section_content),
                        "content": section_content[:50] + "...",
                        "start_line": section_start,
                        "level": 1
                    })
                current_section = [line]
                section_start = i
            else:
                current_section.append(line)

        # Don't forget last section
        if current_section:
            section_content = '\n'.join(current_section)
            chunks.append({
                "hash": compute_hash(section_content),
                "content": section_content[:50] + "...",
                "start_line": section_start,
                "level": 1
            })

    elif level == 2:
        # Paragraph level - split by blank lines
        current_para = []
        para_start = 1

        for i, line in enumerate(lines, 1):
            if line.strip() == '':
                if current_para:
                    para_content = '\n'.join(current_para)
                    chunks.append({
                        "hash": compute_hash(para_content),
                        "content": para_content[:50] + "...",
                        "start_line": para_start,
                        "level": 2
                    })
                    current_para = []
                    para_start = i + 1
            else:
                if not current_para:
                    para_start = i
                current_para.append(line)

        if current_para:
            para_content = '\n'.join(current_para)
            chunks.append({
                "hash": compute_hash(para_content),
                "content": para_content[:50] + "...",
                "start_line": para_start,
                "level": 2
            })

    else:  # level >= 3 - line level
        for i, line in enumerate(lines, 1):
            if line.strip():
                chunks.append({
                    "hash": compute_hash(line),
                    "content": line[:50] + "..." if len(line) > 50 else line,
                    "start_line": i,
                    "level": 3
                })

    return chunks if chunks else [{
        "hash": compute_hash(content),
        "content": content[:50] + "...",
        "start_line": 1,
        "level": level
    }]


def build_merkle_tree(hashes: List[str]) -> Dict[str, Any]:
    """Build Merkle tree from list of leaf hashes.

    Args:
        hashes: List of hash strings (leaf nodes)

    Returns:
        Dict with root hash and tree levels
    """
    if not hashes:
        return {"root": compute_hash(""), "levels": [[]]}

    levels = [hashes[:]]  # Level 0 = leaves

    current_level = hashes[:]
    while len(current_level) > 1:
        next_level = []

        # Process pairs
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            parent = compute_hash(left + right)
            next_level.append(parent)

        levels.append(next_level)
        current_level = next_level

    return {
        "root": levels[-1][0] if levels[-1] else compute_hash(""),
        "levels": levels,
        "depth": len(levels)
    }


def has_changed(new_content: str, old_hash: str) -> bool:
    """Check if content has changed compared to old hash.

    Args:
        new_content: Current content
        old_hash: Previous hash to compare against

    Returns:
        True if content changed, False if same
    """
    new_hash = compute_hash(new_content)
    return new_hash != old_hash


def capture_workspace_state(files: List[str]) -> Dict[str, Any]:
    """Capture current state of workspace files as hash snapshot.

    Args:
        files: List of file paths (relative to project root)

    Returns:
        Dict with timestamp, per-file hashes, and root hash
    """
    project_root = Path(__file__).parent.parent

    file_hashes = {}
    for file_path in files:
        full_path = project_root / file_path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8', errors='replace')
            file_hashes[file_path] = compute_hash(content)
        else:
            file_hashes[file_path] = None

    # Compute root hash from all file hashes
    hash_list = [h for h in file_hashes.values() if h]
    if hash_list:
        tree = build_merkle_tree(hash_list)
        root_hash = tree["root"]
    else:
        root_hash = compute_hash("")

    return {
        "timestamp": datetime.now().isoformat(),
        "files": file_hashes,
        "root_hash": root_hash,
        "file_count": len(files)
    }


def compare_states(state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two workspace states and identify changes.

    Args:
        state1: First state (typically older)
        state2: Second state (typically newer)

    Returns:
        Dict with changed, added, removed files
    """
    files1 = state1.get("files", {})
    files2 = state2.get("files", {})

    changed = []
    added = []
    removed = []

    all_files = set(files1.keys()) | set(files2.keys())

    for f in all_files:
        h1 = files1.get(f)
        h2 = files2.get(f)

        if h1 is None and h2 is not None:
            added.append(f)
        elif h1 is not None and h2 is None:
            removed.append(f)
        elif h1 != h2:
            changed.append(f)

    return {
        "changed": changed,
        "added": added,
        "removed": removed,
        "root_changed": state1.get("root_hash") != state2.get("root_hash")
    }


def compute_short_hash(content: str, length: int = 8) -> str:
    """Compute shortened hash for display (e.g., dashboard).

    Args:
        content: Content to hash
        length: Number of chars to return (default 8)

    Returns:
        Shortened hash string
    """
    full_hash = compute_hash(content)
    return full_hash[:length].upper()


# CLI for testing
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "hash" and len(sys.argv) >= 3:
            file_path = sys.argv[2]
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                print(f"Hash: {compute_hash(content)}")
                print(f"Short: {compute_short_hash(content)}")
            else:
                print(f"File not found: {file_path}")

        elif cmd == "chunks" and len(sys.argv) >= 3:
            file_path = sys.argv[2]
            level = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                chunks = compute_chunk_hashes(content, level)
                print(json.dumps(chunks, indent=2))
            else:
                print(f"File not found: {file_path}")

        elif cmd == "snapshot":
            files = sys.argv[2:] if len(sys.argv) > 2 else ["TODO.md", "CLAUDE.md"]
            state = capture_workspace_state(files)
            print(json.dumps(state, indent=2))

        else:
            print("Usage: python frankel_hash.py [hash|chunks|snapshot] [args]")
    else:
        # Default: show workspace snapshot
        state = capture_workspace_state(["TODO.md", "CLAUDE.md"])
        print(json.dumps(state, indent=2))
