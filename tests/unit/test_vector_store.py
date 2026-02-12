"""
Unit tests for Vector Store Implementation.

Per DOC-SIZE-01-v1: Tests for vector_store/store.py module.
Tests: VectorStore — connect, close, insert, insert_batch, search,
       search_by_source, delete_by_source, clear_cache, _cosine_similarity.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

from governance.vector_store.models import VectorDocument, SimilarityResult
from governance.vector_store.store import VectorStore


def _make_doc(doc_id="doc-1", content="test", embedding=None,
              source="RULE-001", source_type="rule"):
    return VectorDocument(
        id=doc_id,
        content=content,
        embedding=embedding or [1.0, 0.0, 0.0],
        model="test-model",
        dimension=3,
        source=source,
        source_type=source_type,
    )


class TestInit:
    def test_defaults(self):
        store = VectorStore()
        assert store.host == "localhost"
        assert store.port == 1729
        assert store.database == "sim-ai-governance"
        assert store._connected is False

    def test_custom_params(self):
        store = VectorStore(host="remote", port=9999, database="test-db")
        assert store.host == "remote"
        assert store.port == 9999


class TestConnect:
    def test_import_error(self):
        store = VectorStore()
        with patch.dict(sys.modules, {"typedb": None, "typedb.driver": None}):
            # Force ImportError by making the import fail
            with patch("builtins.__import__", side_effect=ImportError("no typedb")):
                result = store.connect()
        assert result is False

    def test_connection_error(self):
        store = VectorStore()
        mock_typedb = MagicMock()
        mock_typedb.TypeDB.driver.side_effect = Exception("connection refused")
        with patch.dict(sys.modules, {
            "typedb": MagicMock(),
            "typedb.driver": mock_typedb,
        }):
            result = store.connect()
        assert result is False


class TestClose:
    def test_close_connected(self):
        store = VectorStore()
        store._client = MagicMock()
        store._connected = True
        store.close()
        store._client.close.assert_called_once()
        assert store._connected is False

    def test_close_not_connected(self):
        store = VectorStore()
        store.close()  # Should not raise


class TestInsert:
    def test_not_connected(self):
        store = VectorStore()
        with pytest.raises(RuntimeError, match="Not connected"):
            store.insert(_make_doc())

    def test_success(self):
        store = VectorStore()
        store._connected = True
        store._client = MagicMock()
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        store._client.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        store._client.transaction.return_value.__exit__ = MagicMock(return_value=False)
        doc = _make_doc()
        result = store.insert(doc)
        assert result is True
        assert doc.id in store._cache

    def test_failure(self):
        store = VectorStore()
        store._connected = True
        store._client = MagicMock()
        store._client.transaction.side_effect = Exception("insert error")
        result = store.insert(_make_doc())
        assert result is False


class TestInsertBatch:
    def test_not_connected(self):
        store = VectorStore()
        with pytest.raises(RuntimeError, match="Not connected"):
            store.insert_batch([_make_doc()])

    def test_success(self):
        store = VectorStore()
        store._connected = True
        store._client = MagicMock()
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        store._client.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        store._client.transaction.return_value.__exit__ = MagicMock(return_value=False)
        docs = [_make_doc("d1"), _make_doc("d2")]
        count = store.insert_batch(docs)
        assert count == 2
        assert "d1" in store._cache
        assert "d2" in store._cache


class TestSearch:
    def test_with_cached_docs(self):
        store = VectorStore()
        store._connected = True
        store._cache = {
            "d1": _make_doc("d1", embedding=[1.0, 0.0, 0.0]),
            "d2": _make_doc("d2", embedding=[0.0, 1.0, 0.0]),
        }
        results = store.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert isinstance(results[0], SimilarityResult)
        # d1 should be first (identical vector)
        assert results[0].vector_id == "d1"
        assert results[0].score > results[1].score

    def test_source_type_filter(self):
        store = VectorStore()
        store._connected = True
        store._cache = {
            "d1": _make_doc("d1", source_type="rule", embedding=[1.0, 0.0, 0.0]),
            "d2": _make_doc("d2", source_type="decision", embedding=[1.0, 0.0, 0.0]),
        }
        results = store.search([1.0, 0.0, 0.0], source_type="rule")
        assert len(results) == 1
        assert results[0].source_type == "rule"

    def test_threshold_filter(self):
        store = VectorStore()
        store._connected = True
        store._cache = {
            "d1": _make_doc("d1", embedding=[1.0, 0.0, 0.0]),
            "d2": _make_doc("d2", embedding=[0.0, 1.0, 0.0]),
        }
        results = store.search([1.0, 0.0, 0.0], threshold=0.9)
        assert len(results) == 1  # Only d1 has score ~1.0

    def test_top_k_limit(self):
        store = VectorStore()
        store._connected = True
        store._cache = {
            f"d{i}": _make_doc(f"d{i}", embedding=[1.0, 0.0, 0.0])
            for i in range(10)
        }
        results = store.search([1.0, 0.0, 0.0], top_k=3)
        assert len(results) == 3

    def test_empty_cache_triggers_load(self):
        store = VectorStore()
        store._connected = True
        store._cache = {}
        # Mock get_all_vectors to avoid TypeDB call
        store.get_all_vectors = MagicMock(return_value=[])
        results = store.search([1.0, 0.0, 0.0])
        store.get_all_vectors.assert_called_once()
        assert results == []


class TestSearchBySource:
    def test_found(self):
        store = VectorStore()
        store._connected = True
        doc = _make_doc("d1", source="RULE-001")
        store._cache = {"d1": doc}
        result = store.search_by_source("RULE-001")
        assert result is doc

    def test_not_found(self):
        store = VectorStore()
        store._connected = True
        store._cache = {"d1": _make_doc("d1", source="RULE-001")}
        result = store.search_by_source("NONEXISTENT")
        assert result is None

    def test_empty_cache_triggers_load(self):
        store = VectorStore()
        store._connected = True
        store._cache = {}
        store.get_all_vectors = MagicMock(return_value=[])
        result = store.search_by_source("X")
        store.get_all_vectors.assert_called_once()
        assert result is None


class TestDeleteBySource:
    def test_not_connected(self):
        store = VectorStore()
        with pytest.raises(RuntimeError, match="Not connected"):
            store.delete_by_source("RULE-001")

    def test_success(self):
        store = VectorStore()
        store._connected = True
        store._client = MagicMock()
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        store._client.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        store._client.transaction.return_value.__exit__ = MagicMock(return_value=False)
        store._cache = {"d1": _make_doc("d1", source="RULE-001")}
        result = store.delete_by_source("RULE-001")
        assert result is True
        assert "d1" not in store._cache

    def test_failure(self):
        store = VectorStore()
        store._connected = True
        store._client = MagicMock()
        store._client.transaction.side_effect = Exception("delete error")
        result = store.delete_by_source("RULE-001")
        assert result is False


class TestClearCache:
    def test_clears(self):
        store = VectorStore()
        store._cache = {"d1": _make_doc()}
        store.clear_cache()
        assert store._cache == {}


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert VectorStore._cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert VectorStore._cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert VectorStore._cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_different_lengths(self):
        assert VectorStore._cosine_similarity([1, 0], [1, 0, 0]) == 0.0

    def test_zero_vector(self):
        assert VectorStore._cosine_similarity([0, 0], [1, 0]) == 0.0
