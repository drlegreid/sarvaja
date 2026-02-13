"""Batch 140: Unit tests for hybrid query router + HybridVectorDb."""
from dataclasses import asdict
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ===== Module 1: hybrid/router.py ============================================

from governance.hybrid.models import QueryType, QueryResult, SyncStatus


class TestQueryType:
    def test_values(self):
        assert QueryType.INFERENCE.value == "inference"
        assert QueryType.SEMANTIC.value == "semantic"
        assert QueryType.COMBINED.value == "combined"
        assert QueryType.AUTO.value == "auto"


class TestQueryResult:
    def test_defaults(self):
        r = QueryResult("q", QueryType.SEMANTIC, "chromadb", [], 0, 1.0)
        assert r.fallback_used is False
        assert r.error is None

    def test_with_results(self):
        r = QueryResult("q", QueryType.INFERENCE, "typedb", [{"a": 1}], 1, 5.0)
        assert r.count == 1
        assert r.results[0]["a"] == 1


class TestSyncStatus:
    def test_defaults(self):
        s = SyncStatus("typedb", "chromadb", 10, 2, 0)
        assert s.errors == []

    def test_with_errors(self):
        s = SyncStatus("typedb", "chromadb", 0, 0, 1, errors=["fail"])
        assert s.errors == ["fail"]


class TestHybridQueryRouterDetect:
    def setup_method(self):
        with patch("governance.hybrid.router.TypeDBClient"):
            from governance.hybrid.router import HybridQueryRouter
            self.router = HybridQueryRouter.__new__(HybridQueryRouter)
            self.router._typedb_client = None
            self.router._chromadb_client = None
            self.router.timeout_ms = 5000

    def test_inference_keywords(self):
        assert self.router._detect_query_type("What depends on RULE-001?") == "inference"
        assert self.router._detect_query_type("Show conflicting rules") == "inference"

    def test_semantic_keywords(self):
        assert self.router._detect_query_type("Tell me about authentication") == "semantic"
        assert self.router._detect_query_type("What is session management?") == "semantic"

    def test_rule_id_boosts_inference(self):
        assert self.router._detect_query_type("RULE-001 details") == "inference"

    def test_decision_id_boosts_inference(self):
        assert self.router._detect_query_type("DECISION-003 impact") == "inference"

    def test_default_is_semantic(self):
        assert self.router._detect_query_type("hello world") == "semantic"


class TestHybridQueryRouterExtract:
    def setup_method(self):
        with patch("governance.hybrid.router.TypeDBClient"):
            from governance.hybrid.router import HybridQueryRouter
            self.router = HybridQueryRouter.__new__(HybridQueryRouter)

    def test_extract_rule_id(self):
        assert self.router._extract_rule_id("What depends on RULE-001?") == "RULE-001"

    def test_extract_rule_id_none(self):
        assert self.router._extract_rule_id("no rule here") is None

    def test_extract_decision_id(self):
        assert self.router._extract_decision_id("DECISION-003 impact") == "DECISION-003"

    def test_extract_decision_id_none(self):
        assert self.router._extract_decision_id("nothing") is None


class TestHybridQueryRouterQuery:
    def setup_method(self):
        with patch("governance.hybrid.router.TypeDBClient"):
            from governance.hybrid.router import HybridQueryRouter
            self.router = HybridQueryRouter.__new__(HybridQueryRouter)
            self.router._typedb_client = None
            self.router._chromadb_client = None
            self.router.timeout_ms = 5000

    def test_semantic_no_chromadb(self):
        r = self.router.query("search something", query_type="semantic")
        assert r.error == "ChromaDB not connected"
        assert r.count == 0

    def test_inference_fallback_no_typedb(self):
        r = self.router.query("depends on RULE-001", query_type="inference")
        assert r.fallback_used is True

    def test_auto_routes_semantic(self):
        r = self.router.query("tell me about auth", query_type="auto")
        assert r.query_type == QueryType.SEMANTIC

    def test_error_handling(self):
        self.router._query_typedb = MagicMock(side_effect=Exception("boom"))
        self.router._query_chromadb = MagicMock(side_effect=Exception("boom"))
        r = self.router.query("test", query_type="semantic")
        assert r.error is not None


class TestHybridQueryRouterHealth:
    def test_health_no_clients(self):
        with patch("governance.hybrid.router.TypeDBClient"):
            with patch("governance.hybrid.router.quick_health", return_value=False):
                from governance.hybrid.router import HybridQueryRouter
                router = HybridQueryRouter.__new__(HybridQueryRouter)
                router._typedb_client = None
                router._chromadb_client = None
                h = router.health_check()
                assert h["typedb"]["connected"] is False
                assert h["chromadb"]["connected"] is False


# ===== Module 2: agent/hybrid_vectordb.py ====================================

class TestHybridVectorDbInit:
    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_defaults(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        assert db.collection_name == "sim_ai_knowledge"
        mock_router.assert_called_once()

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_custom_params(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb(typedb_host="db1", typedb_port=1730, collection_name="test")
        assert db.collection_name == "test"

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_auto_connect(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb(auto_connect=True)
        mock_router.return_value.connect.assert_called_once()


class TestHybridVectorDbSearch:
    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_inference_routing(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router.return_value._detect_query_type.return_value = "inference"
        db = HybridVectorDb()
        result = QueryResult("q", QueryType.INFERENCE, "typedb", [{"rule": "R1"}], 1, 1.0)
        mock_router.return_value.query.return_value = result
        db._route_to_typedb = MagicMock(return_value=[{"rule": "R1"}])
        r = db.search("depends on RULE-001", query_type="inference")
        assert isinstance(r, list)

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_search_error_returns_empty(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router.return_value._detect_query_type.side_effect = Exception("fail")
        db = HybridVectorDb()
        assert db.search("test") == []


class TestHybridVectorDbFormat:
    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_format_dict_results(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        result = QueryResult("q", QueryType.SEMANTIC, "chromadb", [{"a": 1}, {"b": 2}], 2, 1.0)
        assert db._format_results(result) == [{"a": 1}, {"b": 2}]

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_format_non_dict(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        result = QueryResult("q", QueryType.SEMANTIC, "chromadb", ["string_item"], 1, 1.0)
        formatted = db._format_results(result)
        assert formatted == [{"content": "string_item"}]

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_format_empty(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        result = QueryResult("q", QueryType.SEMANTIC, "chromadb", [], 0, 1.0)
        assert db._format_results(result) == []

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_format_none(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        db = HybridVectorDb()
        assert db._format_results(None) == []


class TestHybridVectorDbAdd:
    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_add_no_client(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router.return_value._chromadb_client = None
        db = HybridVectorDb()
        db.add(["doc1"])  # should not raise

    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_delete_no_client(self, mock_router):
        from agent.hybrid_vectordb import HybridVectorDb
        mock_router.return_value._chromadb_client = None
        db = HybridVectorDb()
        db.delete(["id1"])  # should not raise


class TestCreateHybridVectordb:
    @patch("agent.hybrid_vectordb.HybridQueryRouter")
    def test_factory(self, mock_router):
        from agent.hybrid_vectordb import create_hybrid_vectordb
        db = create_hybrid_vectordb(collection="test", auto_connect=False)
        assert db.collection_name == "test"
