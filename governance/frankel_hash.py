"""Frankel Hash Evidence System. Per FH-001-008, RULE-022: Content-addressable state verification."""
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_chunk_hashes(content: str, level: int = 1) -> List[Dict[str, Any]]:
    """Compute hashes at chunk levels: 0=doc, 1=sections, 2=paragraphs, 3=lines."""
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
    """Build Merkle tree from list of leaf hashes."""
    if not hashes:
        return {"root": compute_hash(""), "levels": [[]]}

    levels = [hashes[:]]

    current_level = hashes[:]
    while len(current_level) > 1:
        next_level = []
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
    """Check if content has changed compared to old hash."""
    return compute_hash(new_content) != old_hash


def capture_workspace_state(files: List[str]) -> Dict[str, Any]:
    """Capture current state of workspace files as hash snapshot."""
    project_root = Path(__file__).parent.parent

    file_hashes = {}
    for file_path in files:
        full_path = project_root / file_path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8', errors='replace')
            file_hashes[file_path] = compute_hash(content)
        else:
            file_hashes[file_path] = None

    hash_list = [h for h in file_hashes.values() if h]
    root_hash = build_merkle_tree(hash_list)["root"] if hash_list else compute_hash("")

    return {
        "timestamp": datetime.now().isoformat(),
        "files": file_hashes,
        "root_hash": root_hash,
        "file_count": len(files)
    }


def compare_states(state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two workspace states and identify changes."""
    files1 = state1.get("files", {})
    files2 = state2.get("files", {})

    changed, added, removed = [], [], []
    all_files = set(files1.keys()) | set(files2.keys())

    for f in all_files:
        h1, h2 = files1.get(f), files2.get(f)
        if h1 is None and h2 is not None:
            added.append(f)
        elif h1 is not None and h2 is None:
            removed.append(f)
        elif h1 != h2:
            changed.append(f)

    return {
        "changed": changed, "added": added, "removed": removed,
        "root_changed": state1.get("root_hash") != state2.get("root_hash")
    }


def compute_short_hash(content: str, length: int = 8) -> str:
    """Compute shortened hash for display (e.g., dashboard)."""
    return compute_hash(content)[:length].upper()


def compute_state_hash(data: Dict[str, Any], length: int = 8) -> str:
    """
    Compute Frankel-style hash from dict state (8 chars uppercase).
    Per FH-DUP-001: Consolidated implementation from hooks/core/state.py.
    """
    import json
    serialized = json.dumps(data, sort_keys=True)
    return compute_hash(serialized)[:length].upper()


# Re-export visualization functions for backwards compatibility
def render_merkle_tree(tree: Dict[str, Any], show_full: bool = False) -> str:
    """Render Merkle tree. Delegated to frankel_viz."""
    from governance.frankel_viz import render_merkle_tree as _render
    return _render(tree, show_full)


def render_file_tree(files: Dict[str, str], changed: List[str] = None) -> str:
    """Render file tree. Delegated to frankel_viz."""
    from governance.frankel_viz import render_file_tree as _render
    return _render(files, changed)


def zoom_view(content: str, level: int = 0, focus_line: int = None) -> str:
    """Generate zoom view. Delegated to frankel_viz."""
    from governance.frankel_viz import zoom_view as _zoom
    return _zoom(content, level, focus_line)


def interactive_tree_cli(file_path: str) -> None:
    """Run interactive CLI. Delegated to frankel_viz."""
    from governance.frankel_viz import interactive_tree_cli as _cli
    _cli(file_path)


if __name__ == "__main__":
    from governance.frankel_viz import main
    main()
