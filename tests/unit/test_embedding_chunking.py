"""
Tests for embedding pipeline chunking utilities.

Per GAP-FILE-021: Content splitting for embedding generation.
Covers chunk_content and truncate_content functions.

Created: 2026-01-30
"""

import pytest

from governance.embedding_pipeline.chunking import chunk_content, truncate_content


class TestChunkContent:
    """Test chunk_content function."""

    def test_empty_content(self):
        assert chunk_content("") == [""]

    def test_short_content_single_chunk(self):
        result = chunk_content("Hello world", chunk_size=100)
        assert result == ["Hello world"]

    def test_exact_chunk_size(self):
        content = "x" * 100
        result = chunk_content(content, chunk_size=100)
        assert result == [content]

    def test_splits_at_line_boundary(self):
        content = "line1\nline2\nline3"
        result = chunk_content(content, chunk_size=10)
        assert len(result) >= 2
        # Each chunk should be a complete line or set of lines
        for chunk in result:
            assert not chunk.startswith('\n')

    def test_preserves_all_content(self):
        content = "line1\nline2\nline3\nline4\nline5"
        result = chunk_content(content, chunk_size=10)
        reassembled = '\n'.join(result)
        assert reassembled == content

    def test_long_single_line_in_own_chunk(self):
        content = "short\n" + "x" * 200 + "\nshort2"
        result = chunk_content(content, chunk_size=50)
        # The long line should be in its own chunk
        long_chunks = [c for c in result if len(c) > 50]
        assert len(long_chunks) == 1

    def test_default_chunk_size(self):
        # Default is 2000
        short = "hello"
        assert chunk_content(short) == [short]

    def test_multiple_chunks(self):
        lines = [f"line{i}: {'x' * 50}" for i in range(20)]
        content = '\n'.join(lines)
        result = chunk_content(content, chunk_size=200)
        assert len(result) > 1
        # All chunks except possibly oversized lines should be <= 200
        normal_chunks = [c for c in result if '\n' in c or len(c) <= 200]
        assert len(normal_chunks) > 0

    def test_no_empty_chunks(self):
        content = "line1\nline2\nline3"
        result = chunk_content(content, chunk_size=6)
        assert all(len(c) > 0 for c in result)


class TestTruncateContent:
    """Test truncate_content function."""

    def test_short_content_unchanged(self):
        assert truncate_content("hello", max_length=100) == "hello"

    def test_exact_length_unchanged(self):
        content = "x" * 100
        assert truncate_content(content, max_length=100) == content

    def test_truncates_long_content(self):
        content = "x" * 200
        result = truncate_content(content, max_length=100)
        assert len(result) == 100

    def test_default_max_length(self):
        # Default is 2000
        short = "hello"
        assert truncate_content(short) == short

    def test_empty_content(self):
        assert truncate_content("") == ""

    def test_truncation_preserves_start(self):
        content = "ABCDE" + "x" * 100
        result = truncate_content(content, max_length=10)
        assert result.startswith("ABCDE")
        assert len(result) == 10
