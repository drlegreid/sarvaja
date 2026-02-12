"""
Unit tests for KanrenRAGFilter.

Per DOC-SIZE-01-v1: Tests for kanren/filter.py module.
Tests: KanrenRAGFilter — search_validated, _results_to_chunks, search_for_task.
"""

from unittest.mock import MagicMock, patch

import pytest

from governance.kanren.filter import KanrenRAGFilter


def _make_result(vector_id="v1", content="test", source="RULE-001",
                 source_type="rule", score=0.9):
    r = MagicMock()
    r.vector_id = vector_id
    r.content = content
    r.source = source
    r.source_type = source_type
    r.score = score
    return r


def _make_vector(vec_id="v1", content="test content", source="RULE-001",
                 source_type="rule"):
    v = MagicMock()
    v.id = vec_id
    v.content = content
    v.source = source
    v.source_type = source_type
    return v


class TestInit:
    def test_default_no_store(self):
        f = KanrenRAGFilter()
        assert f._store is None

    def test_with_store(self):
        store = MagicMock()
        f = KanrenRAGFilter(vector_store=store)
        assert f._store is store


class TestGetStore:
    def test_lazy_creates_store(self):
        f = KanrenRAGFilter()
        mock_store = MagicMock()
        with patch("governance.vector_store.VectorStore", return_value=mock_store):
            store = f._get_store()
        assert store is mock_store
        mock_store.connect.assert_called_once()

    def test_reuses_existing_store(self):
        store = MagicMock()
        f = KanrenRAGFilter(vector_store=store)
        assert f._get_store() is store


class TestResultsToChunks:
    def test_rule_type(self):
        f = KanrenRAGFilter()
        results = [_make_result(source_type="rule")]
        chunks = f._results_to_chunks(results)
        assert len(chunks) == 1
        assert chunks[0]["source"] == "typedb"
        assert chunks[0]["type"] == "rule"

    def test_session_type(self):
        f = KanrenRAGFilter()
        results = [_make_result(source_type="session")]
        chunks = f._results_to_chunks(results)
        assert chunks[0]["source"] == "chromadb"

    def test_decision_type(self):
        f = KanrenRAGFilter()
        results = [_make_result(source_type="decision")]
        chunks = f._results_to_chunks(results)
        assert chunks[0]["source"] == "typedb"

    def test_verified_flag(self):
        f = KanrenRAGFilter()
        high = _make_result(score=0.9)
        low = _make_result(score=0.3)
        chunks = f._results_to_chunks([high, low])
        assert chunks[0]["verified"] is True
        assert chunks[1]["verified"] is False

    def test_empty_results(self):
        f = KanrenRAGFilter()
        assert f._results_to_chunks([]) == []


class TestSearchValidated:
    def test_basic_search(self):
        store = MagicMock()
        store.search.return_value = [_make_result()]
        with patch("governance.kanren.filter.filter_rag_chunks",
                   side_effect=lambda x: x):
            f = KanrenRAGFilter(vector_store=store)
            results = f.search_validated([1.0, 0.0])
        assert len(results) == 1
        store.search.assert_called_once()

    def test_with_source_type(self):
        store = MagicMock()
        store.search.return_value = []
        with patch("governance.kanren.filter.filter_rag_chunks",
                   return_value=[]):
            f = KanrenRAGFilter(vector_store=store)
            f.search_validated([1.0], source_type="rule")
        store.search.assert_called_once_with([1.0], 10, "rule", 0.0)

    def test_kanren_filters_results(self):
        store = MagicMock()
        store.search.return_value = [_make_result(), _make_result(vector_id="v2")]
        with patch("governance.kanren.filter.filter_rag_chunks",
                   return_value=[{"id": "v1"}]):
            f = KanrenRAGFilter(vector_store=store)
            results = f.search_validated([1.0])
        assert len(results) == 1


class TestSearchForTask:
    def test_basic(self):
        store = MagicMock()
        store.get_all_vectors.return_value = [
            _make_vector(content="test content about rules"),
        ]
        task_ctx = MagicMock()
        agent_ctx = MagicMock()
        with patch("governance.kanren.filter.filter_rag_chunks",
                   side_effect=lambda x: x), \
             patch("governance.kanren.filter.assemble_context",
                   return_value={"chunks": []}):
            f = KanrenRAGFilter(vector_store=store)
            result = f.search_for_task("rules", task_ctx, agent_ctx)
        assert isinstance(result, dict)

    def test_text_matching(self):
        store = MagicMock()
        store.get_all_vectors.return_value = [
            _make_vector(content="test about rules"),
            _make_vector(content="unrelated content"),
        ]
        task_ctx = MagicMock()
        agent_ctx = MagicMock()
        captured_chunks = []
        with patch("governance.kanren.filter.filter_rag_chunks",
                   side_effect=lambda x: (captured_chunks.extend(x) or x)), \
             patch("governance.kanren.filter.assemble_context",
                   return_value={"chunks": captured_chunks}):
            f = KanrenRAGFilter(vector_store=store)
            f.search_for_task("rules", task_ctx, agent_ctx)
        # Only "test about rules" matches
        assert len(captured_chunks) == 1
