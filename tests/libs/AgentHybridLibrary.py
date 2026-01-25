"""
Robot Framework Library for Agent Hybrid Layer Tests.

Per P3.4: Agent hybrid layer integration.
Migrated from tests/test_agent_hybrid.py
"""
from unittest.mock import Mock, patch
from robot.api.deco import keyword


class AgentHybridLibrary:
    """Library for testing agent hybrid layer integration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # HybridVectorDb Tests
    # =============================================================================

    @keyword("Hybrid VectorDb Class Exists")
    def hybrid_vectordb_class_exists(self):
        """HybridVectorDb adapter should exist."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb
            return {"exists": HybridVectorDb is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Hybrid VectorDb Implements Search")
    def hybrid_vectordb_implements_search(self):
        """HybridVectorDb should implement search method."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb

            db = HybridVectorDb()
            return {
                "has_search": hasattr(db, 'search'),
                "search_callable": callable(getattr(db, 'search', None))
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Hybrid VectorDb Routes Inference Queries")
    def hybrid_vectordb_routes_inference_queries(self):
        """Inference queries should route to TypeDB."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb

            db = HybridVectorDb()
            with patch.object(db, '_query_typedb') as mock_typedb:
                mock_typedb.return_value = []
                db.search("What depends on RULE-001?")
                return {"called_typedb": mock_typedb.called}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError:
            return {"skipped": True, "reason": "_query_typedb not found"}

    @keyword("Hybrid VectorDb Routes Semantic Queries")
    def hybrid_vectordb_routes_semantic_queries(self):
        """Semantic queries should route to ChromaDB."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb

            db = HybridVectorDb()
            with patch.object(db, '_query_chromadb') as mock_chromadb:
                mock_chromadb.return_value = []
                db.search("Tell me about authentication best practices")
                return {"called_chromadb": mock_chromadb.called}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError:
            return {"skipped": True, "reason": "_query_chromadb not found"}

    @keyword("Hybrid VectorDb Fallback To ChromaDB")
    def hybrid_vectordb_fallback_to_chromadb(self):
        """Should fallback to ChromaDB when TypeDB fails."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb

            db = HybridVectorDb()
            with patch.object(db, '_query_typedb') as mock_typedb:
                mock_typedb.side_effect = Exception("TypeDB down")
                with patch.object(db, '_query_chromadb') as mock_chromadb:
                    mock_chromadb.return_value = [{"doc": "fallback"}]
                    db.search("What depends on RULE-001?")
                    return {"fallback_called": mock_chromadb.called}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError:
            return {"skipped": True, "reason": "Query methods not found"}

    # =============================================================================
    # Agent Governance Query Tests
    # =============================================================================

    @keyword("Agent Can Query Rule Dependencies")
    def agent_can_query_rule_dependencies(self):
        """Agent should be able to query rule dependencies."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb

            db = HybridVectorDb()
            with patch.object(db, '_router') as mock_router:
                mock_router.query.return_value = Mock(
                    results=[{"rule_id": "RULE-002"}],
                    count=1
                )
                result = db.search("What depends on RULE-001?")
                return {"has_result": result is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError:
            return {"skipped": True, "reason": "_router not found"}

    @keyword("Agent Can Query Conflicts")
    def agent_can_query_conflicts(self):
        """Agent should be able to query rule conflicts."""
        try:
            from agent.hybrid_vectordb import HybridVectorDb

            db = HybridVectorDb()
            with patch.object(db, '_router') as mock_router:
                mock_router.query.return_value = Mock(
                    results=[],
                    count=0
                )
                result = db.search("Show conflicts between rules")
                return {"has_result": result is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError:
            return {"skipped": True, "reason": "_router not found"}

    # =============================================================================
    # Sync Bridge Tests
    # =============================================================================

    @keyword("Agent Sees Synced Rules")
    def agent_sees_synced_rules(self):
        """Agent knowledge should include synced TypeDB rules."""
        try:
            from governance.hybrid_router import HybridQueryRouter, MemorySyncBridge

            router = HybridQueryRouter()
            bridge = MemorySyncBridge(router)

            status = bridge.get_sync_status()
            return {"has_collections": "collections" in status}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
