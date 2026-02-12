"""
Unit tests for Kanren RAG Chunk Validation.

Per DOC-SIZE-01-v1: Tests for kanren/rag.py module.
Tests: valid_rag_chunk, filter_rag_chunks.
"""

import pytest

from governance.kanren.rag import (
    valid_rag_chunk,
    filter_rag_chunks,
    ALLOWED_SOURCES,
    TRUSTED_TYPES,
)


class TestConstants:
    """Tests for module constants."""

    def test_allowed_sources(self):
        assert "typedb" in ALLOWED_SOURCES
        assert "chromadb" in ALLOWED_SOURCES
        assert "evidence" in ALLOWED_SOURCES

    def test_trusted_types(self):
        assert "rule" in TRUSTED_TYPES
        assert "decision" in TRUSTED_TYPES
        assert "evidence" in TRUSTED_TYPES
        assert "task" in TRUSTED_TYPES


class TestValidRagChunk:
    """Tests for valid_rag_chunk()."""

    def test_valid_chunk(self):
        result = valid_rag_chunk("typedb", True, "rule")
        assert result and result[0] is True

    def test_invalid_source(self):
        result = valid_rag_chunk("unknown_source", True, "rule")
        assert not result or (result and result[0] is not True)

    def test_unverified_chunk(self):
        result = valid_rag_chunk("typedb", False, "rule")
        assert not result or (result and result[0] is not True)

    def test_invalid_type(self):
        result = valid_rag_chunk("typedb", True, "unknown_type")
        assert not result or (result and result[0] is not True)

    def test_all_valid_sources(self):
        for source in ALLOWED_SOURCES:
            result = valid_rag_chunk(source, True, "rule")
            assert result and result[0] is True

    def test_all_valid_types(self):
        for chunk_type in TRUSTED_TYPES:
            result = valid_rag_chunk("typedb", True, chunk_type)
            assert result and result[0] is True


class TestFilterRagChunks:
    """Tests for filter_rag_chunks()."""

    def test_empty_list(self):
        result = filter_rag_chunks([])
        assert result == []

    def test_all_valid(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "rule 1"},
            {"source": "chromadb", "verified": True, "type": "evidence", "content": "ev 1"},
        ]
        result = filter_rag_chunks(chunks)
        assert len(result) == 2

    def test_filters_invalid_source(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule"},
            {"source": "invalid", "verified": True, "type": "rule"},
        ]
        result = filter_rag_chunks(chunks)
        assert len(result) == 1

    def test_filters_unverified(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule"},
            {"source": "typedb", "verified": False, "type": "rule"},
        ]
        result = filter_rag_chunks(chunks)
        assert len(result) == 1

    def test_filters_invalid_type(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule"},
            {"source": "typedb", "verified": True, "type": "spam"},
        ]
        result = filter_rag_chunks(chunks)
        assert len(result) == 1

    def test_missing_fields_filtered(self):
        chunks = [{"content": "no metadata"}]
        result = filter_rag_chunks(chunks)
        assert len(result) == 0

    def test_preserves_chunk_data(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "test", "score": 0.9},
        ]
        result = filter_rag_chunks(chunks)
        assert result[0]["content"] == "test"
        assert result[0]["score"] == 0.9
