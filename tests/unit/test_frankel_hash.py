"""
Tests for Frankel Hash Evidence System.

Per FH-001-008, RULE-022: Content-addressable state verification.
Covers hash computation, chunk hashing, Merkle trees, and state comparison.

Created: 2026-01-30
"""

import hashlib
import pytest

from governance.frankel_hash import (
    compute_hash,
    compute_chunk_hashes,
    build_merkle_tree,
    has_changed,
    compare_states,
    compute_short_hash,
    compute_state_hash,
)


class TestComputeHash:
    """Test SHA-256 hash computation."""

    def test_deterministic(self):
        """Same content produces same hash."""
        assert compute_hash("hello") == compute_hash("hello")

    def test_different_content(self):
        """Different content produces different hash."""
        assert compute_hash("hello") != compute_hash("world")

    def test_sha256_format(self):
        """Hash is valid SHA-256 hex digest (64 chars)."""
        h = compute_hash("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_known_value(self):
        """Verify against known SHA-256."""
        expected = hashlib.sha256(b"test").hexdigest()
        assert compute_hash("test") == expected

    def test_empty_string(self):
        """Empty string produces valid hash."""
        h = compute_hash("")
        assert len(h) == 64

    def test_unicode(self):
        """Unicode content hashes correctly."""
        h = compute_hash("héllo wörld")
        assert len(h) == 64


class TestComputeChunkHashes:
    """Test chunk-level hashing."""

    def test_level_0_whole_document(self):
        """Level 0 returns single document-level hash."""
        chunks = compute_chunk_hashes("Hello\nWorld", level=0)
        assert len(chunks) == 1
        assert chunks[0]["level"] == 0
        assert chunks[0]["start_line"] == 1

    def test_level_1_sections(self):
        """Level 1 splits by markdown headers."""
        content = "# Section 1\nContent A\n## Section 2\nContent B"
        chunks = compute_chunk_hashes(content, level=1)
        assert len(chunks) == 2
        assert all(c["level"] == 1 for c in chunks)

    def test_level_2_paragraphs(self):
        """Level 2 splits by blank lines."""
        content = "Para 1 line 1\nPara 1 line 2\n\nPara 2 line 1"
        chunks = compute_chunk_hashes(content, level=2)
        assert len(chunks) == 2
        assert all(c["level"] == 2 for c in chunks)

    def test_level_3_lines(self):
        """Level 3 splits by non-empty lines."""
        content = "Line 1\nLine 2\n\nLine 3"
        chunks = compute_chunk_hashes(content, level=3)
        assert len(chunks) == 3  # Blank lines excluded

    def test_each_chunk_has_hash(self):
        """Each chunk has a hash field."""
        chunks = compute_chunk_hashes("# A\ntext\n# B\ntext", level=1)
        for chunk in chunks:
            assert "hash" in chunk
            assert len(chunk["hash"]) == 64

    def test_content_truncated(self):
        """Content field is truncated with ellipsis."""
        long_content = "x" * 200
        chunks = compute_chunk_hashes(long_content, level=0)
        assert chunks[0]["content"].endswith("...")
        assert len(chunks[0]["content"]) <= 103  # 100 + "..."

    def test_empty_content_fallback(self):
        """Empty content at section level falls back to full doc."""
        chunks = compute_chunk_hashes("no headers here", level=1)
        assert len(chunks) >= 1

    def test_start_line_tracking(self):
        """Chunks track start_line correctly."""
        content = "# First\nA\n# Second\nB"
        chunks = compute_chunk_hashes(content, level=1)
        assert chunks[0]["start_line"] == 1
        assert chunks[1]["start_line"] == 3


class TestBuildMerkleTree:
    """Test Merkle tree construction."""

    def test_empty_input(self):
        """Empty list produces tree with empty root."""
        tree = build_merkle_tree([])
        assert "root" in tree
        assert tree["levels"] == [[]]

    def test_single_hash(self):
        """Single hash is its own root."""
        h = compute_hash("test")
        tree = build_merkle_tree([h])
        assert tree["root"] == h
        assert tree["depth"] == 1

    def test_two_hashes(self):
        """Two hashes produce a tree of depth 2."""
        h1, h2 = compute_hash("a"), compute_hash("b")
        tree = build_merkle_tree([h1, h2])
        assert tree["depth"] == 2
        expected_root = compute_hash(h1 + h2)
        assert tree["root"] == expected_root

    def test_odd_number_of_hashes(self):
        """Odd number duplicates last hash for pairing."""
        hashes = [compute_hash(str(i)) for i in range(3)]
        tree = build_merkle_tree(hashes)
        assert tree["depth"] >= 2

    def test_power_of_two(self):
        """Power-of-two input produces balanced tree."""
        hashes = [compute_hash(str(i)) for i in range(4)]
        tree = build_merkle_tree(hashes)
        assert tree["depth"] == 3  # 4 leaves -> 2 -> 1

    def test_deterministic(self):
        """Same input always produces same tree."""
        hashes = [compute_hash(str(i)) for i in range(5)]
        t1 = build_merkle_tree(hashes)
        t2 = build_merkle_tree(hashes)
        assert t1["root"] == t2["root"]

    def test_different_order_different_root(self):
        """Different order of hashes produces different root."""
        h1, h2 = compute_hash("a"), compute_hash("b")
        t1 = build_merkle_tree([h1, h2])
        t2 = build_merkle_tree([h2, h1])
        assert t1["root"] != t2["root"]


class TestHasChanged:
    """Test content change detection."""

    def test_unchanged(self):
        """Same content returns False."""
        content = "hello"
        h = compute_hash(content)
        assert has_changed(content, h) is False

    def test_changed(self):
        """Different content returns True."""
        h = compute_hash("hello")
        assert has_changed("world", h) is True

    def test_empty_to_content(self):
        """Empty to content is a change."""
        h = compute_hash("")
        assert has_changed("new content", h) is True


class TestCompareStates:
    """Test workspace state comparison."""

    def test_identical_states(self):
        """Identical states show no changes."""
        state = {"files": {"a.py": "hash1"}, "root_hash": "root1"}
        result = compare_states(state, state)
        assert result["changed"] == []
        assert result["added"] == []
        assert result["removed"] == []
        assert result["root_changed"] is False

    def test_file_changed(self):
        """Changed file detected."""
        s1 = {"files": {"a.py": "hash1"}, "root_hash": "r1"}
        s2 = {"files": {"a.py": "hash2"}, "root_hash": "r2"}
        result = compare_states(s1, s2)
        assert "a.py" in result["changed"]
        assert result["root_changed"] is True

    def test_file_added(self):
        """New file detected."""
        s1 = {"files": {}, "root_hash": "r1"}
        s2 = {"files": {"new.py": "hash1"}, "root_hash": "r2"}
        result = compare_states(s1, s2)
        assert "new.py" in result["added"]

    def test_file_removed(self):
        """Removed file detected."""
        s1 = {"files": {"old.py": "hash1"}, "root_hash": "r1"}
        s2 = {"files": {}, "root_hash": "r2"}
        result = compare_states(s1, s2)
        assert "old.py" in result["removed"]

    def test_mixed_changes(self):
        """Multiple change types detected together."""
        s1 = {"files": {"keep.py": "h1", "change.py": "h2", "remove.py": "h3"}, "root_hash": "r1"}
        s2 = {"files": {"keep.py": "h1", "change.py": "h9", "add.py": "h4"}, "root_hash": "r2"}
        result = compare_states(s1, s2)
        assert "change.py" in result["changed"]
        assert "add.py" in result["added"]
        assert "remove.py" in result["removed"]
        assert "keep.py" not in result["changed"]

    def test_none_hash_treated_as_missing(self):
        """None hash in state1 + real hash in state2 = added."""
        s1 = {"files": {"a.py": None}, "root_hash": "r1"}
        s2 = {"files": {"a.py": "hash1"}, "root_hash": "r2"}
        result = compare_states(s1, s2)
        assert "a.py" in result["added"]


class TestComputeShortHash:
    """Test shortened hash for display."""

    def test_default_length(self):
        """Default length is 8 chars."""
        h = compute_short_hash("test")
        assert len(h) == 8

    def test_uppercase(self):
        """Short hash is uppercase."""
        h = compute_short_hash("test")
        assert h == h.upper()

    def test_custom_length(self):
        """Custom length works."""
        h = compute_short_hash("test", length=12)
        assert len(h) == 12

    def test_deterministic(self):
        """Same content produces same short hash."""
        assert compute_short_hash("x") == compute_short_hash("x")


class TestComputeStateHash:
    """Test state dict hashing."""

    def test_deterministic(self):
        """Same dict produces same hash."""
        data = {"a": 1, "b": 2}
        assert compute_state_hash(data) == compute_state_hash(data)

    def test_key_order_irrelevant(self):
        """Key order doesn't affect hash (sort_keys=True)."""
        assert compute_state_hash({"a": 1, "b": 2}) == compute_state_hash({"b": 2, "a": 1})

    def test_uppercase_format(self):
        """Hash is 8 chars uppercase."""
        h = compute_state_hash({"test": True})
        assert len(h) == 8
        assert h == h.upper()

    def test_different_data(self):
        """Different data produces different hash."""
        assert compute_state_hash({"a": 1}) != compute_state_hash({"a": 2})
