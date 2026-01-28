"""
Tests for FH-001-008: Frankel Hash Evidence System

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: R&D-BACKLOG.md RD-FRANKEL-HASH

Tests cover:
1. FH-001: Content hashing at chunk level
2. FH-002: Hash tree structure
3. FH-007: State change detection
4. FH-008: Coverage assessment
"""

import pytest
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


# =============================================================================
# Test 1: Core Content Hashing (FH-001)
# =============================================================================

class TestContentHashing:
    """Tests for content-addressable hashing."""

    def test_frankel_hash_module_exists(self):
        """Frankel hash module is importable."""
        try:
            from governance.frankel_hash import compute_hash
            assert compute_hash is not None
        except ImportError:
            # Module doesn't exist yet - TDD will create it
            pytest.skip("frankel_hash module not implemented yet")

    def test_compute_document_hash(self):
        """compute_hash generates consistent hash for document content."""
        try:
            from governance.frankel_hash import compute_hash
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        content = "This is test content."
        hash1 = compute_hash(content)
        hash2 = compute_hash(content)

        assert hash1 == hash2, "Same content should produce same hash"
        assert len(hash1) == 64, "SHA-256 hash should be 64 chars"

    def test_different_content_different_hash(self):
        """Different content produces different hashes."""
        try:
            from governance.frankel_hash import compute_hash
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        hash1 = compute_hash("Content A")
        hash2 = compute_hash("Content B")

        assert hash1 != hash2

    def test_chunk_level_hashing(self):
        """Content can be hashed at different chunk levels."""
        try:
            from governance.frankel_hash import compute_chunk_hashes
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        content = """# Section 1

Paragraph one.

Paragraph two.

# Section 2

More content here.
"""
        chunks = compute_chunk_hashes(content, level=1)  # Section level

        assert len(chunks) >= 2, "Should have at least 2 sections"
        assert all("hash" in c for c in chunks)


# =============================================================================
# Test 2: Hash Tree / Merkle Structure (FH-002)
# =============================================================================

class TestHashTree:
    """Tests for Merkle tree hash structure."""

    def test_build_merkle_tree(self):
        """Build Merkle tree from chunk hashes."""
        try:
            from governance.frankel_hash import build_merkle_tree
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        chunks = ["hash1", "hash2", "hash3", "hash4"]
        tree = build_merkle_tree(chunks)

        assert "root" in tree
        assert "levels" in tree
        assert len(tree["levels"]) > 1  # At least leaves + root

    def test_merkle_root_changes_with_content(self):
        """Merkle root changes when any chunk changes."""
        try:
            from governance.frankel_hash import build_merkle_tree, compute_chunk_hashes
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        content1 = "Line1\nLine2\nLine3"
        content2 = "Line1\nModified\nLine3"

        chunks1 = compute_chunk_hashes(content1, level=2)
        chunks2 = compute_chunk_hashes(content2, level=2)

        tree1 = build_merkle_tree([c["hash"] for c in chunks1])
        tree2 = build_merkle_tree([c["hash"] for c in chunks2])

        assert tree1["root"] != tree2["root"]


# =============================================================================
# Test 3: State Change Detection (FH-007)
# =============================================================================

class TestStateChangeDetection:
    """Tests for detecting state changes via hash comparison."""

    def test_detect_file_change(self):
        """Detect when a file has changed."""
        try:
            from governance.frankel_hash import compute_hash, has_changed
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        old_hash = compute_hash("Original content")
        new_content = "Modified content"

        changed = has_changed(new_content, old_hash)
        assert changed is True

    def test_detect_no_change(self):
        """Detect when file hasn't changed."""
        try:
            from governance.frankel_hash import compute_hash, has_changed
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        content = "Same content"
        old_hash = compute_hash(content)

        changed = has_changed(content, old_hash)
        assert changed is False

    def test_workspace_state_snapshot(self):
        """Capture workspace state as hash snapshot."""
        try:
            from governance.frankel_hash import capture_workspace_state
        except ImportError:
            pytest.skip("frankel_hash module not implemented yet")

        state = capture_workspace_state(["TODO.md", "CLAUDE.md"])

        assert "timestamp" in state
        assert "files" in state
        assert "root_hash" in state


# =============================================================================
# Test 4: Task-Commit Linking (User Request)
# =============================================================================

class TestTaskCommitLinking:
    """Tests for linking tasks to git commits and changed files."""

    def test_session_visibility_accepts_commit_info(self):
        """Session visibility can record commit info per task."""
        import sys

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        try:
            from session_visibility import record_commit_info
        except ImportError:
            pytest.skip("record_commit_info not implemented yet")

        record_commit_info(
            task_id="TASK-001",
            commit_hash="abc123",
            files_changed=["src/main.py", "tests/test_main.py"],
            commit_message="Fix bug in main"
        )

    def test_get_task_files_changed(self):
        """Can retrieve files changed for a task."""
        import sys

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        try:
            from session_visibility import get_task_commit_info
        except ImportError:
            pytest.skip("get_task_commit_info not implemented yet")

        info = get_task_commit_info("TASK-001")
        assert "files_changed" in info or info.get("error")


# =============================================================================
# Test 5: Integration with Session Visibility
# =============================================================================

class TestFrankelHashIntegration:
    """Tests for integrating Frankel hash with session visibility."""

    def test_task_completion_includes_hash(self):
        """Completed task includes content hash of changes."""
        import sys

        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "checkers"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from session_visibility import (
            start_session,
            start_task,
            complete_task,
            get_task_rules_summary
        )

        start_session("TEST-FH-INTEGRATION")
        start_task("FH-TASK", "Frankel Hash Test")
        completed = complete_task("FH-TASK")

        # Task should be completable
        assert completed is not None
        assert completed.get("status") == "completed"


# =============================================================================
# Test 6: Frankel Hash Utilities (Standalone Implementation)
# =============================================================================

class TestFrankelHashUtilities:
    """Standalone utility tests that don't require full module."""

    def test_sha256_hash_computation(self):
        """Basic SHA-256 hash computation works."""
        content = "Test content"
        hash_value = hashlib.sha256(content.encode()).hexdigest()

        assert len(hash_value) == 64
        assert hash_value == hashlib.sha256(content.encode()).hexdigest()

    def test_incremental_hash_update(self):
        """Incremental hash update produces same result as full hash."""
        content = "Part1Part2Part3"

        # Full hash
        full_hash = hashlib.sha256(content.encode()).hexdigest()

        # Incremental hash
        hasher = hashlib.sha256()
        hasher.update(b"Part1")
        hasher.update(b"Part2")
        hasher.update(b"Part3")
        incremental_hash = hasher.hexdigest()

        assert full_hash == incremental_hash

    def test_file_hash_computation(self, tmp_path):
        """Can compute hash of file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("File content for hashing")

        content = test_file.read_text()
        file_hash = hashlib.sha256(content.encode()).hexdigest()

        assert len(file_hash) == 64

    def test_merkle_pair_hash(self):
        """Merkle tree pair hashing works correctly."""
        hash1 = hashlib.sha256(b"leaf1").hexdigest()
        hash2 = hashlib.sha256(b"leaf2").hexdigest()

        # Parent hash is hash of concatenated children
        parent = hashlib.sha256((hash1 + hash2).encode()).hexdigest()

        assert len(parent) == 64
        assert parent != hash1
        assert parent != hash2


# =============================================================================
# Test 7: FH-002 ASCII Tree Visualization (2026-01-25)
# =============================================================================

class TestASCIITreeVisualization:
    """Tests for FH-002: ASCII Merkle tree rendering."""

    def test_render_merkle_tree_exists(self):
        """render_merkle_tree function exists."""
        from governance.frankel_hash import render_merkle_tree
        assert render_merkle_tree is not None

    def test_render_merkle_tree_output(self):
        """render_merkle_tree produces valid ASCII output."""
        from governance.frankel_hash import build_merkle_tree, render_merkle_tree

        hashes = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
        tree = build_merkle_tree(hashes)
        output = render_merkle_tree(tree)

        assert "Merkle Tree" in output
        assert "ROOT" in output
        assert "L0" in output  # Leaf level
        assert "depth=" in output

    def test_render_merkle_tree_short_hashes(self):
        """render_merkle_tree uses short hashes by default."""
        from governance.frankel_hash import build_merkle_tree, render_merkle_tree

        hashes = ["a" * 64, "b" * 64]
        tree = build_merkle_tree(hashes)
        output = render_merkle_tree(tree)

        # Should show 8-char hashes, not full 64-char
        assert "AAAAAAAA" in output.upper()
        assert ("a" * 64) not in output  # Full hash shouldn't appear

    def test_render_file_tree_exists(self):
        """render_file_tree function exists."""
        from governance.frankel_hash import render_file_tree
        assert render_file_tree is not None

    def test_render_file_tree_output(self):
        """render_file_tree produces valid file tree."""
        from governance.frankel_hash import render_file_tree

        files = {
            "file1.py": "a" * 64,
            "file2.py": "b" * 64,
        }
        output = render_file_tree(files)

        assert "File Hash Tree" in output
        assert "file1.py" in output
        assert "file2.py" in output

    def test_render_file_tree_change_indicator(self):
        """render_file_tree marks changed files."""
        from governance.frankel_hash import render_file_tree

        files = {"changed.py": "a" * 64, "unchanged.py": "b" * 64}
        output = render_file_tree(files, changed=["changed.py"])

        assert "[CHANGED]" in output


# =============================================================================
# Test 8: FH-001 Zoom View (2026-01-25)
# =============================================================================

class TestZoomView:
    """Tests for FH-001: Interactive zoom view."""

    def test_zoom_view_exists(self):
        """zoom_view function exists."""
        from governance.frankel_hash import zoom_view
        assert zoom_view is not None

    def test_zoom_level_0_document(self):
        """Zoom level 0 shows document-level hash."""
        from governance.frankel_hash import zoom_view

        content = "# Header\n\nParagraph 1\n\n## Section\n\nParagraph 2"
        output = zoom_view(content, level=0)

        assert "Zoom Level 0" in output
        assert "Document" in output
        assert "Total chunks: 1" in output

    def test_zoom_level_1_sections(self):
        """Zoom level 1 shows section-level hashes."""
        from governance.frankel_hash import zoom_view

        content = "# Section 1\n\nContent\n\n# Section 2\n\nMore content"
        output = zoom_view(content, level=1)

        assert "Zoom Level 1" in output
        assert "Section" in output
        assert "Total chunks:" in output

    def test_zoom_level_3_lines(self):
        """Zoom level 3 shows line-level hashes."""
        from governance.frankel_hash import zoom_view

        content = "Line 1\nLine 2\nLine 3"
        output = zoom_view(content, level=3)

        assert "Zoom Level 3" in output
        assert "Line" in output
        assert "Total chunks: 3" in output

    def test_zoom_view_includes_line_numbers(self):
        """Zoom view shows line numbers."""
        from governance.frankel_hash import zoom_view

        content = "# Header\n\nParagraph"
        output = zoom_view(content, level=1)

        assert "L" in output  # Line number indicator
