"""
Unit tests for Frankel Hash Visualization & CLI.

Per FH-001, FH-002: Tests for render_merkle_tree, render_file_tree, zoom_view.
"""

import pytest

from governance.frankel_viz import (
    render_merkle_tree,
    render_file_tree,
    zoom_view,
)


# ---------------------------------------------------------------------------
# render_merkle_tree
# ---------------------------------------------------------------------------
class TestRenderMerkleTree:
    """Tests for render_merkle_tree()."""

    def test_empty_tree(self):
        result = render_merkle_tree({"levels": []})
        assert result == "(empty tree)"

    def test_missing_levels(self):
        result = render_merkle_tree({})
        assert result == "(empty tree)"

    def test_single_level(self):
        tree = {"levels": [["abc12345def"]], "depth": 1, "root": "abc12345def67890"}
        result = render_merkle_tree(tree)
        assert "Merkle Tree (depth=1)" in result
        assert "ROOT" in result
        assert "ABC12345" in result  # short hash

    def test_multi_level(self):
        tree = {
            "levels": [
                ["aaa11111", "bbb22222"],  # leaves
                ["ccc33333"],               # root
            ],
            "depth": 2,
            "root": "ccc33333444455556666",
        }
        result = render_merkle_tree(tree)
        assert "ROOT" in result
        assert "L0" in result

    def test_show_full_hashes(self):
        tree = {"levels": [["abcdef1234567890"]], "depth": 1, "root": "abcdef1234567890"}
        result = render_merkle_tree(tree, show_full=True)
        assert "abcdef1234567890" in result

    def test_short_hashes_default(self):
        tree = {"levels": [["abcdef1234567890"]], "depth": 1, "root": "abcdef1234567890"}
        result = render_merkle_tree(tree, show_full=False)
        assert "ABCDEF12" in result  # 8 chars uppercase
        # Level lines should use short hashes (the root footer shows 16 chars though)
        lines = result.split("\n")
        level_lines = [l for l in lines if l.startswith("ROOT:") or l.startswith("L")]
        for ll in level_lines:
            assert "abcdef1234567890" not in ll  # full hash not in level lines

    def test_separator_lines(self):
        tree = {"levels": [["aaa"]], "depth": 1, "root": "aaa"}
        result = render_merkle_tree(tree)
        assert "=" * 50 in result

    def test_root_hash_in_footer(self):
        tree = {"levels": [["aaa"]], "depth": 1, "root": "abcdef1234567890abcdef"}
        result = render_merkle_tree(tree)
        assert "Root:" in result
        assert "ABCDEF1234567890" in result


# ---------------------------------------------------------------------------
# render_file_tree
# ---------------------------------------------------------------------------
class TestRenderFileTree:
    """Tests for render_file_tree()."""

    def test_empty_files(self):
        result = render_file_tree({})
        assert "File Hash Tree" in result

    def test_single_file(self):
        result = render_file_tree({"test.py": "abcdef1234567890"})
        assert "test.py" in result
        assert "ABCDEF12" in result

    def test_sorted_by_filename(self):
        files = {"z_file.py": "aaa", "a_file.py": "bbb"}
        result = render_file_tree(files)
        lines = result.split("\n")
        file_lines = [l for l in lines if ".py" in l]
        assert "a_file.py" in file_lines[0]
        assert "z_file.py" in file_lines[1]

    def test_changed_marker(self):
        result = render_file_tree(
            {"file1.py": "aaa", "file2.py": "bbb"},
            changed=["file1.py"],
        )
        assert "[CHANGED]" in result
        # Only file1 should be marked
        lines = result.split("\n")
        file1_line = [l for l in lines if "file1.py" in l][0]
        file2_line = [l for l in lines if "file2.py" in l][0]
        assert "[CHANGED]" in file1_line
        assert "[CHANGED]" not in file2_line

    def test_no_changed_files(self):
        result = render_file_tree({"file.py": "aaa"})
        assert "[CHANGED]" not in result

    def test_missing_hash(self):
        result = render_file_tree({"file.py": None})
        assert "(missing)" in result

    def test_empty_hash(self):
        result = render_file_tree({"file.py": ""})
        assert "(missing)" in result

    def test_tree_connectors(self):
        files = {"a.py": "aaa", "b.py": "bbb", "c.py": "ccc"}
        result = render_file_tree(files)
        assert "├──" in result  # non-last items
        assert "└──" in result  # last item


# ---------------------------------------------------------------------------
# zoom_view
# ---------------------------------------------------------------------------
class TestZoomView:
    """Tests for zoom_view()."""

    def test_document_level(self):
        result = zoom_view("Hello world", level=0)
        assert "Zoom Level 0: Document" in result
        assert "Total chunks:" in result

    def test_section_level(self):
        content = "# Header\nContent\n## Section\nMore content"
        result = zoom_view(content, level=1)
        assert "Zoom Level 1: Section" in result

    def test_paragraph_level(self):
        content = "Para 1\n\nPara 2\n\nPara 3"
        result = zoom_view(content, level=2)
        assert "Zoom Level 2: Paragraph" in result

    def test_line_level(self):
        content = "Line 1\nLine 2\nLine 3"
        result = zoom_view(content, level=3)
        assert "Zoom Level 3: Line" in result

    def test_unknown_level(self):
        result = zoom_view("content", level=99)
        assert "Zoom Level 99: Line" in result

    def test_contains_hashes(self):
        result = zoom_view("Some content here", level=0)
        # Should have 8-char uppercase hash
        assert "[" in result

    def test_focus_line_marker(self):
        content = "\n".join(f"Line {i}" for i in range(20))
        result = zoom_view(content, level=3, focus_line=5)
        assert "<<<" in result

    def test_no_focus_line(self):
        result = zoom_view("Content", level=0)
        assert "<<<" not in result

    def test_separator_lines(self):
        result = zoom_view("Content", level=0)
        assert "=" * 60 in result

    def test_total_chunks_count(self):
        content = "# Sec1\nBody\n# Sec2\nBody2"
        result = zoom_view(content, level=1)
        assert "Total chunks:" in result
