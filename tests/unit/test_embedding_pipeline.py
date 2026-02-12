"""
Unit tests for Embedding Pipeline Core.

Per DOC-SIZE-01-v1: Tests for embedding_pipeline/pipeline.py module.
Tests: EmbeddingPipeline embed/store/needs_update, chunked embedding,
       embed_rules/decisions/sessions, run_full_pipeline, factory.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

_P_COMPAT = "governance.embedding_pipeline.pipeline"

# Mock vector store imports before importing pipeline
_mock_vs = MagicMock()
_mock_vs.VectorDocument = type("VectorDocument", (), {
    "__init__": lambda self, **kw: self.__dict__.update(kw),
})
_mock_vs.VectorStore = MagicMock
_mock_vs.EmbeddingGenerator = MagicMock


class _FakeVectorDoc:
    def __init__(self, doc_id, content, source=None):
        self.id = doc_id
        self.content = content
        self.source = source or doc_id


def _make_gen():
    gen = MagicMock()
    gen.generate.return_value = [0.1] * 384
    return gen


def _make_store():
    store = MagicMock()
    store._cache = {}
    return store


@pytest.fixture()
def pipeline():
    gen = _make_gen()
    store = _make_store()

    with patch(f"{_P_COMPAT}.create_vector_from_rule",
               side_effect=lambda rid, c, g: _FakeVectorDoc(rid, c)), \
         patch(f"{_P_COMPAT}.create_vector_from_decision",
               side_effect=lambda did, c, g: _FakeVectorDoc(did, c)), \
         patch(f"{_P_COMPAT}.create_vector_from_session",
               side_effect=lambda sid, c, g: _FakeVectorDoc(sid, c)), \
         patch(f"{_P_COMPAT}.create_embedding_generator", return_value=gen):
        from governance.embedding_pipeline.pipeline import EmbeddingPipeline
        p = EmbeddingPipeline(embedding_generator=gen, vector_store=store)
        p.store = store
        p.store._cache = {}
        yield p


class TestEmbedRule:
    def test_basic(self, pipeline):
        doc = pipeline.embed_rule("RULE-001", "Test rule")
        assert doc.id == "RULE-001"

    def test_with_directive(self, pipeline):
        doc = pipeline.embed_rule("RULE-002", "Rule name", "Do something")
        assert doc.id == "RULE-002"


class TestEmbedDecision:
    def test_basic(self, pipeline):
        doc = pipeline.embed_decision("DECISION-001", "Important decision")
        assert doc.id == "DECISION-001"


class TestEmbedSession:
    def test_basic(self, pipeline):
        doc = pipeline.embed_session("SESSION-2026-02-11-TEST", "Session content")
        assert doc.id == "SESSION-2026-02-11-TEST"

    def test_truncates_long_content(self, pipeline):
        pipeline.chunk_size = 10
        doc = pipeline.embed_session("S-1", "x" * 1000)
        assert doc.id == "S-1"


class TestEmbedSessionChunked:
    def test_single_chunk(self, pipeline):
        pipeline.chunk_size = 5000
        docs = pipeline.embed_session_chunked("S-1", "Short content")
        assert len(docs) == 1
        assert docs[0].source == "S-1"

    def test_multiple_chunks(self, pipeline):
        pipeline.chunk_size = 10
        content = "line1\nline2\nline3\nline4\nline5"
        docs = pipeline.embed_session_chunked("S-1", content)
        assert len(docs) >= 2
        for doc in docs:
            assert doc.source == "S-1"
            assert "chunk" in doc.id


class TestStoreEmbedding:
    def test_store_single(self, pipeline):
        doc = _FakeVectorDoc("DOC-1", "content")
        result = pipeline.store_embedding(doc)
        assert result is True
        assert "DOC-1" in pipeline.store._cache

    def test_store_multiple(self, pipeline):
        docs = [_FakeVectorDoc(f"DOC-{i}", f"content-{i}") for i in range(3)]
        count = pipeline.store_embeddings(docs)
        assert count == 3
        assert len(pipeline.store._cache) == 3


class TestNeedsUpdate:
    def test_needs_update_true(self, pipeline):
        assert pipeline.needs_update("SOURCE-1") is True

    def test_needs_update_false(self, pipeline):
        doc = _FakeVectorDoc("DOC-1", "content", source="SOURCE-1")
        pipeline.store._cache["DOC-1"] = doc
        assert pipeline.needs_update("SOURCE-1") is False


class TestGetEmbeddedSources:
    def test_empty(self, pipeline):
        assert pipeline.get_embedded_sources() == []

    def test_with_sources(self, pipeline):
        pipeline.store._cache["A"] = _FakeVectorDoc("A", "c", source="src-1")
        pipeline.store._cache["B"] = _FakeVectorDoc("B", "c", source="src-2")
        sources = pipeline.get_embedded_sources()
        assert set(sources) == {"src-1", "src-2"}


class TestEmbedRules:
    def test_success(self, pipeline):
        rules_json = json.dumps([
            {"id": "RULE-001", "name": "Test", "directive": "Do X"},
            {"id": "RULE-002", "name": "Test2"},
        ])
        with patch(f"{_P_COMPAT}.governance_query_rules", return_value=rules_json):
            docs = pipeline.embed_rules()
        assert len(docs) == 2

    def test_error_returns_empty(self, pipeline):
        with patch(f"{_P_COMPAT}.governance_query_rules",
                   return_value=json.dumps({"error": "fail"})):
            docs = pipeline.embed_rules()
        assert docs == []

    def test_exception_returns_empty(self, pipeline):
        with patch(f"{_P_COMPAT}.governance_query_rules",
                   side_effect=Exception("boom")):
            docs = pipeline.embed_rules()
        assert docs == []


class TestEmbedDecisions:
    def test_success(self, pipeline):
        decisions_json = json.dumps({
            "decisions": [
                {"decision_id": "DECISION-001", "name": "D1", "context": "ctx"},
            ]
        })
        with patch(f"{_P_COMPAT}.governance_list_decisions",
                   return_value=decisions_json):
            docs = pipeline.embed_decisions()
        assert len(docs) == 1

    def test_error_returns_empty(self, pipeline):
        with patch(f"{_P_COMPAT}.governance_list_decisions",
                   return_value=json.dumps({"error": "fail"})):
            docs = pipeline.embed_decisions()
        assert docs == []


class TestEmbedSessions:
    def test_success(self, pipeline):
        sessions_json = json.dumps({
            "sessions": [{"session_id": "SESSION-2026-02-11-TEST"}]
        })
        detail_json = json.dumps({"content": "session content"})

        with patch(f"{_P_COMPAT}.governance_list_sessions",
                   return_value=sessions_json), \
             patch(f"{_P_COMPAT}.governance_get_session",
                   return_value=detail_json):
            docs = pipeline.embed_sessions(limit=5)
        assert len(docs) == 1

    def test_empty_content_skipped(self, pipeline):
        sessions_json = json.dumps({
            "sessions": [{"session_id": "S-1"}]
        })
        detail_json = json.dumps({"content": ""})

        with patch(f"{_P_COMPAT}.governance_list_sessions",
                   return_value=sessions_json), \
             patch(f"{_P_COMPAT}.governance_get_session",
                   return_value=detail_json):
            docs = pipeline.embed_sessions()
        assert docs == []


class TestRunFullPipeline:
    def test_dry_run(self, pipeline):
        with patch.object(pipeline, "embed_rules", return_value=[_FakeVectorDoc("R", "c")]), \
             patch.object(pipeline, "embed_decisions", return_value=[_FakeVectorDoc("D", "c")]), \
             patch.object(pipeline, "embed_sessions", return_value=[]):
            result = pipeline.run_full_pipeline(dry_run=True)

        assert result["dry_run"] is True
        assert result["rules"] == 1
        assert result["decisions"] == 1
        assert result["sessions"] == 0
        assert result["total"] == 2
        assert len(pipeline.store._cache) == 0  # dry run = no store

    def test_stores_on_real_run(self, pipeline):
        docs = [_FakeVectorDoc("R1", "c"), _FakeVectorDoc("R2", "c")]
        with patch.object(pipeline, "embed_rules", return_value=docs), \
             patch.object(pipeline, "embed_decisions", return_value=[]), \
             patch.object(pipeline, "embed_sessions", return_value=[]):
            result = pipeline.run_full_pipeline(dry_run=False)

        assert result["rules"] == 2
        assert result["total"] == 2
        assert len(pipeline.store._cache) == 2


class TestFactory:
    def test_create_embedding_pipeline(self):
        with patch(f"{_P_COMPAT}.create_embedding_generator") as mock_gen:
            mock_gen.return_value = _make_gen()
            from governance.embedding_pipeline.pipeline import create_embedding_pipeline
            p = create_embedding_pipeline(use_mock=True)
            assert p is not None
