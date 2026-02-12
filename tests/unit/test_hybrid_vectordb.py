"""
Unit tests for HybridVectorDb adapter.

Per DOC-SIZE-01-v1: Tests for agent/hybrid_vectordb.py module.
Tests: HybridVectorDb.__init__, connect, close, search, _route_to_typedb,
       _query_typedb, _query_chromadb, _format_results, health_check,
       get_query_type, add, delete, create_hybrid_vectordb.
"""

from unittest.mock import patch, MagicMock

import pytest

_P = "agent.hybrid_vectordb"


@pytest.fixture
def mock_router():
    with patch(f"{_P}.HybridQueryRouter") as MockRouter:
        router = MagicMock()
        MockRouter.return_value = router
        yield router


# ── __init__ ─────────────────────────────────────────────────────


class TestInit:
    def test_default_init(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        assert db.collection_name == "sim_ai_knowledge"
        mock_router.connect.assert_not_called()

    def test_auto_connect(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb(auto_connect=True)
        mock_router.connect.assert_called_once()

    def test_custom_collection(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb(collection_name="test_col")
        assert db.collection_name == "test_col"


# ── connect / close ──────────────────────────────────────────────


class TestConnectClose:
    def test_connect(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router.connect.return_value = {"typedb": True, "chromadb": True}
        db = HybridVectorDb()
        result = db.connect()
        assert result["typedb"] is True

    def test_close(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        db.close()
        mock_router.close.assert_called_once()


# ── search ───────────────────────────────────────────────────────


class TestSearch:
    def test_inference_query(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb, QueryResult
        mock_router._detect_query_type.return_value = "inference"
        qr = MagicMock()
        qr.results = [{"content": "rule data"}]
        mock_router.query.return_value = qr
        db = HybridVectorDb()
        results = db.search("What depends on RULE-001?")
        assert len(results) == 1

    def test_semantic_query(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router._detect_query_type.return_value = "semantic"
        qr = MagicMock()
        qr.results = [{"content": "auth docs"}]
        mock_router.query.return_value = qr
        db = HybridVectorDb()
        results = db.search("Tell me about authentication")
        assert len(results) == 1

    def test_forced_query_type(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        qr = MagicMock()
        qr.results = []
        mock_router.query.return_value = qr
        db = HybridVectorDb()
        db.search("anything", query_type="semantic")
        mock_router._detect_query_type.assert_not_called()

    def test_search_exception_returns_empty(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router._detect_query_type.side_effect = Exception("fail")
        db = HybridVectorDb()
        results = db.search("test")
        assert results == []


# ── _route_to_typedb ─────────────────────────────────────────────


class TestRouteToTypedb:
    def test_typedb_success(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        qr = MagicMock()
        qr.results = [{"id": "R-1"}]
        mock_router.query.return_value = qr
        db = HybridVectorDb()
        results = db._route_to_typedb("depends on R-1")
        assert len(results) == 1

    def test_typedb_fallback_to_chromadb(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        qr = MagicMock()
        qr.results = [{"fallback": True}]
        # First call (typedb) raises, second call (chromadb) succeeds
        mock_router.query.side_effect = [Exception("typedb fail"), qr]
        db = HybridVectorDb()
        results = db._route_to_typedb("query")
        assert len(results) == 1


# ── _format_results ──────────────────────────────────────────────


class TestFormatResults:
    def test_empty_results(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        qr = MagicMock()
        qr.results = []
        assert db._format_results(qr) == []

    def test_none_result(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        assert db._format_results(None) == []

    def test_dict_items(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        qr = MagicMock()
        qr.results = [{"id": 1}, {"id": 2}]
        results = db._format_results(qr)
        assert len(results) == 2
        assert results[0]["id"] == 1

    def test_non_dict_items(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        qr = MagicMock()
        qr.results = ["raw string"]
        results = db._format_results(qr)
        assert results[0]["content"] == "raw string"


# ── health_check / get_query_type ────────────────────────────────


class TestHealthAndQueryType:
    def test_health_check(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router.health_check.return_value = {"typedb": True, "chromadb": True}
        db = HybridVectorDb()
        result = db.health_check()
        assert result["typedb"] is True

    def test_get_query_type(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router._detect_query_type.return_value = "inference"
        db = HybridVectorDb()
        assert db.get_query_type("depends on R-1") == "inference"


# ── add ──────────────────────────────────────────────────────────


class TestAdd:
    def test_add_success(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        collection_mock = MagicMock()
        mock_router._chromadb_client.get_or_create_collection.return_value = collection_mock
        db = HybridVectorDb()
        db.add(["doc1", "doc2"], ids=["id1", "id2"])
        collection_mock.add.assert_called_once()

    def test_add_auto_ids(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        collection_mock = MagicMock()
        mock_router._chromadb_client.get_or_create_collection.return_value = collection_mock
        db = HybridVectorDb()
        db.add(["doc1"])
        call_args = collection_mock.add.call_args
        assert len(call_args.kwargs.get("ids", call_args[1].get("ids", []))) == 1

    def test_add_no_client(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router._chromadb_client = None
        db = HybridVectorDb()
        db.add(["doc1"])  # should not raise

    def test_add_exception(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router._chromadb_client.get_or_create_collection.side_effect = Exception("fail")
        db = HybridVectorDb()
        db.add(["doc1"])  # should not raise


# ── delete ───────────────────────────────────────────────────────


class TestDelete:
    def test_delete_success(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        collection_mock = MagicMock()
        mock_router._chromadb_client.get_collection.return_value = collection_mock
        db = HybridVectorDb()
        db.delete(["id1"])
        collection_mock.delete.assert_called_once_with(ids=["id1"])

    def test_delete_no_client(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router._chromadb_client = None
        db = HybridVectorDb()
        db.delete(["id1"])  # should not raise


# ── create_hybrid_vectordb factory ───────────────────────────────


class TestFactory:
    def test_create(self, mock_router):
        from agent.hybrid_vectordb import create_hybrid_vectordb
        db = create_hybrid_vectordb(collection="test")
        assert db.collection_name == "test"

    def test_create_default(self, mock_router):
        from agent.hybrid_vectordb import create_hybrid_vectordb
        db = create_hybrid_vectordb()
        assert db.collection_name == "sim_ai_knowledge"
