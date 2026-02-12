"""
Unit tests for Kanren RAG Chunk Validation.

Per DOC-SIZE-01-v1: Tests for kanren/rag.py module.
Tests: valid_rag_chunk(), filter_rag_chunks(), ALLOWED_SOURCES, TRUSTED_TYPES.
"""

from governance.kanren.rag import (
    valid_rag_chunk,
    filter_rag_chunks,
    ALLOWED_SOURCES,
    TRUSTED_TYPES,
)


class TestValidRagChunk:
    def test_valid_chunk(self):
        result = valid_rag_chunk("typedb", True, "rule")
        assert result and result[0] is True

    def test_invalid_source(self):
        result = valid_rag_chunk("unknown", True, "rule")
        assert not result or result[0] is not True

    def test_not_verified(self):
        result = valid_rag_chunk("typedb", False, "rule")
        assert not result or result[0] is not True

    def test_invalid_type(self):
        result = valid_rag_chunk("typedb", True, "unknown")
        assert not result or result[0] is not True

    def test_all_allowed_sources(self):
        for source in ALLOWED_SOURCES:
            result = valid_rag_chunk(source, True, "rule")
            assert result and result[0] is True

    def test_all_trusted_types(self):
        for chunk_type in TRUSTED_TYPES:
            result = valid_rag_chunk("typedb", True, chunk_type)
            assert result and result[0] is True


class TestFilterRagChunks:
    def test_filters_valid(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "A"},
            {"source": "unknown", "verified": True, "type": "rule", "content": "B"},
            {"source": "typedb", "verified": False, "type": "rule", "content": "C"},
        ]
        valid = filter_rag_chunks(chunks)
        assert len(valid) == 1
        assert valid[0]["content"] == "A"

    def test_empty_input(self):
        assert filter_rag_chunks([]) == []

    def test_all_valid(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule"},
            {"source": "chromadb", "verified": True, "type": "evidence"},
        ]
        assert len(filter_rag_chunks(chunks)) == 2

    def test_all_invalid(self):
        chunks = [
            {"source": "bad", "verified": True, "type": "rule"},
            {"source": "typedb", "verified": False, "type": "rule"},
        ]
        assert len(filter_rag_chunks(chunks)) == 0

    def test_missing_keys_default_invalid(self):
        chunks = [{"content": "no keys"}]
        assert len(filter_rag_chunks(chunks)) == 0
