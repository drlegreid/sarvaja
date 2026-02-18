"""
Tests for embedding pipeline chunking utilities.

Per GAP-FILE-021: Tests for chunking.py module.
Covers content chunking and truncation for embeddings.

Created: 2026-01-30
"""

import pytest

from governance.embedding_pipeline.chunking import chunk_content, truncate_content


class TestChunkContent:
    """Test content chunking for embeddings."""

    def test_empty_content(self):
        """Empty content returns empty list."""
        assert chunk_content("") == []

    def test_short_content_single_chunk(self):
        """Content shorter than chunk_size returns single chunk."""
        result = chunk_content("Hello world", chunk_size=100)
        assert result == ["Hello world"]

    def test_exact_chunk_size(self):
        """Content exactly at chunk_size returns single chunk."""
        content = "x" * 100
        result = chunk_content(content, chunk_size=100)
        assert len(result) == 1

    def test_splits_at_lines(self):
        """Content is split at line boundaries."""
        content = "Line 1\nLine 2\nLine 3\nLine 4"
        result = chunk_content(content, chunk_size=15)
        assert len(result) > 1
        # Each chunk should contain complete lines
        for chunk in result:
            assert not chunk.startswith("\n")

    def test_long_single_line(self):
        """Single long line goes into its own chunk."""
        content = "A" * 200
        result = chunk_content(content, chunk_size=100)
        assert len(result) == 1
        assert result[0] == "A" * 200

    def test_preserves_content(self):
        """All content is preserved across chunks."""
        content = "\n".join(f"Line {i}" for i in range(50))
        result = chunk_content(content, chunk_size=100)
        reassembled = "\n".join(result)
        assert reassembled == content

    def test_default_chunk_size(self):
        """Default chunk size is 2000."""
        content = "x" * 1999
        result = chunk_content(content)
        assert len(result) == 1

    def test_multiple_chunks(self):
        """Large content produces multiple chunks."""
        lines = [f"Line {i}: " + "x" * 50 for i in range(100)]
        content = "\n".join(lines)
        result = chunk_content(content, chunk_size=500)
        assert len(result) > 1

    def test_chunks_respect_size(self):
        """Most chunks are within chunk_size (except oversized single lines)."""
        lines = [f"Normal line {i}" for i in range(100)]
        content = "\n".join(lines)
        result = chunk_content(content, chunk_size=100)
        for chunk in result:
            # Regular lines should fit within chunk_size
            assert len(chunk) <= 100 + 50  # Some tolerance for line joining


class TestTruncateContent:
    """Test content truncation."""

    def test_short_content_unchanged(self):
        """Content shorter than max_length is unchanged."""
        assert truncate_content("Hello", max_length=100) == "Hello"

    def test_exact_length_unchanged(self):
        """Content exactly at max_length is unchanged."""
        content = "x" * 100
        assert truncate_content(content, max_length=100) == content

    def test_long_content_truncated(self):
        """Content longer than max_length is truncated."""
        content = "x" * 200
        result = truncate_content(content, max_length=100)
        assert len(result) == 100

    def test_default_max_length(self):
        """Default max_length is 2000."""
        content = "x" * 2001
        result = truncate_content(content)
        assert len(result) == 2000

    def test_empty_content(self):
        """Empty content is unchanged."""
        assert truncate_content("") == ""

    def test_truncation_preserves_prefix(self):
        """Truncation preserves the beginning of content."""
        content = "ABCDEFGHIJ"
        result = truncate_content(content, max_length=5)
        assert result == "ABCDE"
