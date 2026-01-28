"""Frankel Hash Visualization & CLI. Per FH-001, FH-002, DOC-SIZE-01-v1."""
from pathlib import Path
from typing import Dict, List, Any

from governance.frankel_hash import (
    compute_hash,
    compute_chunk_hashes,
    build_merkle_tree,
    capture_workspace_state,
)


# =============================================================================
# FH-002: ASCII Tree Visualization
# =============================================================================

def render_merkle_tree(tree: Dict[str, Any], show_full: bool = False) -> str:
    """
    Render Merkle tree as ASCII art.

    Args:
        tree: Output from build_merkle_tree()
        show_full: If True, show full hashes; else show 8-char short hashes

    Returns:
        ASCII string representation of the tree
    """
    levels = tree.get("levels", [])
    if not levels:
        return "(empty tree)"

    lines = []
    lines.append(f"Merkle Tree (depth={tree.get('depth', 0)})")
    lines.append("=" * 50)

    # Render from root down
    for level_idx in range(len(levels) - 1, -1, -1):
        level = levels[level_idx]
        level_name = "ROOT" if level_idx == len(levels) - 1 else f"L{level_idx}"

        # Format hashes
        if show_full:
            hashes = level
        else:
            hashes = [h[:8].upper() for h in level]

        # Calculate spacing for tree alignment
        indent = "  " * (len(levels) - 1 - level_idx)

        # Render level
        lines.append(f"{level_name}: {indent}[{' '.join(hashes)}]")

        # Add connectors (except for leaf level)
        if level_idx > 0:
            connector_indent = "  " * (len(levels) - 1 - level_idx)
            connectors = []
            for i in range(len(level)):
                connectors.append("├─┬─┤" if i < len(level) - 1 else "└─┴─┘")
            lines.append(f"     {connector_indent}{' '.join(connectors)}")

    lines.append("=" * 50)
    lines.append(f"Root: {tree.get('root', '')[:16].upper()}...")

    return "\n".join(lines)


def render_file_tree(files: Dict[str, str], changed: List[str] = None) -> str:
    """
    Render file hash tree with change indicators.

    Args:
        files: Dict of {filename: hash}
        changed: List of changed filenames to highlight

    Returns:
        ASCII tree representation
    """
    changed = changed or []
    lines = []
    lines.append("File Hash Tree")
    lines.append("=" * 50)

    for i, (filename, file_hash) in enumerate(sorted(files.items())):
        is_last = i == len(files) - 1
        prefix = "└──" if is_last else "├──"

        if file_hash:
            short_hash = file_hash[:8].upper()
            marker = " [CHANGED]" if filename in changed else ""
            lines.append(f"{prefix} {filename}: {short_hash}{marker}")
        else:
            lines.append(f"{prefix} {filename}: (missing)")

    return "\n".join(lines)


# =============================================================================
# FH-001: Interactive CLI Zoom
# =============================================================================

def zoom_view(content: str, level: int = 0, focus_line: int = None) -> str:
    """
    Generate zoom view of content at specified level.

    Levels:
        0 = Document level (single hash)
        1 = Section level (markdown headers)
        2 = Paragraph level
        3 = Line level

    Args:
        content: File content to analyze
        level: Zoom level 0-3
        focus_line: Optional line number to highlight

    Returns:
        ASCII view at the specified zoom level
    """
    chunks = compute_chunk_hashes(content, level)

    lines = []
    level_names = {0: 'Document', 1: 'Section', 2: 'Paragraph', 3: 'Line'}
    lines.append(f"Zoom Level {level}: {level_names.get(level, 'Line')}")
    lines.append("=" * 60)

    for chunk in chunks:
        short_hash = chunk["hash"][:8].upper()
        start = chunk["start_line"]
        preview = chunk["content"][:40].replace("\n", "↵")

        # Highlight focused line
        marker = " <<<" if focus_line and start <= focus_line < start + 10 else ""

        lines.append(f"[{short_hash}] L{start:4d}: {preview}{marker}")

    lines.append("=" * 60)
    lines.append(f"Total chunks: {len(chunks)}")

    return "\n".join(lines)


def interactive_tree_cli(file_path: str) -> None:
    """
    Run interactive tree navigation CLI.

    Commands:
        z0, z1, z2, z3 - Set zoom level
        t - Show Merkle tree
        f - Show file tree
        q - Quit
    """
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return

    content = path.read_text(encoding='utf-8', errors='replace')
    current_level = 1

    print(f"\nFrankel Hash Navigator - {file_path}")
    print("Commands: z0/z1/z2/z3 (zoom), t (tree), q (quit)")
    print("-" * 50)

    while True:
        # Show current view
        print(zoom_view(content, current_level))

        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == 'q':
            break
        elif cmd in ('z0', 'z1', 'z2', 'z3'):
            current_level = int(cmd[1])
        elif cmd == 't':
            chunks = compute_chunk_hashes(content, current_level)
            hashes = [c["hash"] for c in chunks]
            tree = build_merkle_tree(hashes)
            print(render_merkle_tree(tree))
        elif cmd == 'f':
            # Show file in context of workspace
            state = capture_workspace_state([file_path])
            print(render_file_tree(state["files"]))
        else:
            print("Unknown command. Use z0-z3, t, f, or q.")


# =============================================================================
# CLI Main
# =============================================================================

USAGE = """Frankel Hash CLI (FH-001, FH-002)

Commands:
    hash <file>              - Compute hash of file
    chunks <file> [level]    - Show chunks at zoom level (0-3)
    tree <file> [level]      - Show Merkle tree visualization
    zoom <file> [level]      - Show zoom view
    nav <file>               - Interactive navigation (FH-001)
    snapshot [files...]      - Capture workspace state

Examples:
    python -m governance.frankel_viz tree TODO.md 1
    python -m governance.frankel_viz nav CLAUDE.md
    python -m governance.frankel_viz zoom TODO.md 2
"""


def main():
    """CLI entry point."""
    import sys
    import json

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "hash" and len(sys.argv) >= 3:
            file_path = sys.argv[2]
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                from governance.frankel_hash import compute_short_hash
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

        elif cmd == "tree" and len(sys.argv) >= 3:
            # FH-002: ASCII tree visualization
            file_path = sys.argv[2]
            level = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                chunks = compute_chunk_hashes(content, level)
                hashes = [c["hash"] for c in chunks]
                tree = build_merkle_tree(hashes)
                print(render_merkle_tree(tree))
            else:
                print(f"File not found: {file_path}")

        elif cmd == "zoom" and len(sys.argv) >= 3:
            # FH-001: Zoom view
            file_path = sys.argv[2]
            level = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                print(zoom_view(content, level))
            else:
                print(f"File not found: {file_path}")

        elif cmd == "nav" and len(sys.argv) >= 3:
            # FH-001: Interactive navigation
            file_path = sys.argv[2]
            interactive_tree_cli(file_path)

        elif cmd == "snapshot":
            files = sys.argv[2:] if len(sys.argv) > 2 else ["TODO.md", "CLAUDE.md"]
            state = capture_workspace_state(files)
            print(json.dumps(state, indent=2))

        elif cmd in ("help", "-h", "--help"):
            print(USAGE)

        else:
            print(USAGE)
    else:
        print(USAGE)


if __name__ == "__main__":
    main()
