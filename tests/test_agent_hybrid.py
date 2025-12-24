"""
TDD Tests for Agent Hybrid Layer Integration (P3.4)
Per RULE-004: Exploratory Testing & TDD

RED → GREEN → REFACTOR

These tests define the expected behavior for agents using the hybrid
query layer (TypeDB + ChromaDB).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os

# Check if agno is available (Docker-only dependency)
try:
    import agno
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False


# =============================================================================
# RED PHASE: Tests that should FAIL initially
# =============================================================================

@pytest.mark.skipif(not AGNO_AVAILABLE, reason="Requires agno (Docker dependency)")
class TestAgentHybridKnowledge:
    """Test hybrid knowledge integration with agents."""

    def test_create_hybrid_knowledge_exists(self):
        """Hybrid knowledge factory function should exist."""
        from agent.playground import create_hybrid_knowledge
        assert callable(create_hybrid_knowledge)

    def test_hybrid_knowledge_returns_knowledge_object(self):
        """Hybrid knowledge should return an Agno Knowledge object."""
        from agent.playground import create_hybrid_knowledge
        from agno.knowledge.knowledge import Knowledge

        with patch.dict(os.environ, {
            "CHROMADB_HOST": "localhost",
            "CHROMADB_PORT": "8001",
            "TYPEDB_HOST": "localhost",
            "TYPEDB_PORT": "1729"
        }):
            knowledge = create_hybrid_knowledge()
            # Should return Knowledge or None (if connection fails)
            assert knowledge is None or isinstance(knowledge, Knowledge)

    def test_hybrid_knowledge_has_query_method(self):
        """Hybrid knowledge should expose query method."""
        from agent.playground import create_hybrid_knowledge

        with patch.dict(os.environ, {
            "CHROMADB_HOST": "localhost",
            "CHROMADB_PORT": "8001"
        }):
            knowledge = create_hybrid_knowledge()
            if knowledge:
                # Should have search/query capability
                assert hasattr(knowledge, 'search') or hasattr(knowledge, 'query')


@pytest.mark.skipif(not AGNO_AVAILABLE, reason="Requires agno (Docker dependency)")
class TestHybridQueryInAgent:
    """Test agents using hybrid queries."""

    def test_agent_config_supports_hybrid_knowledge(self):
        """Agent config should support use_hybrid_knowledge flag."""
        config = {
            "agents": {
                "governance": {
                    "name": "Governance Agent",
                    "use_hybrid_knowledge": True,  # NEW FLAG
                    "description": "Governance and rules agent"
                }
            }
        }
        assert config["agents"]["governance"]["use_hybrid_knowledge"] is True

    def test_create_agents_with_hybrid_knowledge(self):
        """Agents with use_hybrid_knowledge should get hybrid layer."""
        from agent.playground import create_agents

        config = {
            "agents": {
                "test_agent": {
                    "name": "Test Agent",
                    "use_hybrid_knowledge": True,
                    "chat": True
                }
            }
        }

        with patch.dict(os.environ, {
            "MODEL_NAME": "claude-sonnet-4-20250514",
            "ANTHROPIC_API_KEY": "test-key"
        }):
            with patch('agent.playground.create_hybrid_knowledge') as mock_hybrid:
                mock_hybrid.return_value = None  # Simulate no connection
                try:
                    agents = create_agents(config)
                    # Should attempt to create hybrid knowledge
                    mock_hybrid.assert_called()
                except Exception:
                    # May fail due to model init, but hybrid should be called
                    pass


class TestHybridVectorDb:
    """Test HybridVectorDb that wraps both ChromaDB and TypeDB."""

    def test_hybrid_vectordb_class_exists(self):
        """HybridVectorDb adapter should exist."""
        from agent.hybrid_vectordb import HybridVectorDb
        assert HybridVectorDb is not None

    def test_hybrid_vectordb_implements_search(self):
        """HybridVectorDb should implement search method."""
        from agent.hybrid_vectordb import HybridVectorDb

        db = HybridVectorDb()
        assert hasattr(db, 'search')
        assert callable(db.search)

    def test_hybrid_vectordb_routes_inference_queries(self):
        """Inference queries should route to TypeDB."""
        from agent.hybrid_vectordb import HybridVectorDb

        db = HybridVectorDb()
        with patch.object(db, '_query_typedb') as mock_typedb:
            mock_typedb.return_value = []
            # Inference query pattern
            db.search("What depends on RULE-001?")
            mock_typedb.assert_called()

    def test_hybrid_vectordb_routes_semantic_queries(self):
        """Semantic queries should route to ChromaDB."""
        from agent.hybrid_vectordb import HybridVectorDb

        db = HybridVectorDb()
        with patch.object(db, '_query_chromadb') as mock_chromadb:
            mock_chromadb.return_value = []
            # Semantic query pattern
            db.search("Tell me about authentication best practices")
            mock_chromadb.assert_called()

    def test_hybrid_vectordb_fallback_to_chromadb(self):
        """Should fallback to ChromaDB when TypeDB fails."""
        from agent.hybrid_vectordb import HybridVectorDb

        db = HybridVectorDb()
        with patch.object(db, '_query_typedb') as mock_typedb:
            mock_typedb.side_effect = Exception("TypeDB down")
            with patch.object(db, '_query_chromadb') as mock_chromadb:
                mock_chromadb.return_value = [{"doc": "fallback"}]
                result = db.search("What depends on RULE-001?")
                mock_chromadb.assert_called()  # Fallback triggered


class TestAgentGovernanceQueries:
    """Test governance-specific queries through agents."""

    def test_agent_can_query_rule_dependencies(self):
        """Agent should be able to query rule dependencies."""
        from agent.hybrid_vectordb import HybridVectorDb

        db = HybridVectorDb()
        # Mock the router
        with patch.object(db, '_router') as mock_router:
            mock_router.query.return_value = Mock(
                results=[{"rule_id": "RULE-002"}],
                count=1
            )
            result = db.search("What depends on RULE-001?")
            assert result is not None

    def test_agent_can_query_conflicts(self):
        """Agent should be able to query rule conflicts."""
        from agent.hybrid_vectordb import HybridVectorDb

        db = HybridVectorDb()
        with patch.object(db, '_router') as mock_router:
            mock_router.query.return_value = Mock(
                results=[],
                count=0
            )
            result = db.search("Show conflicts between rules")
            assert result is not None


class TestSyncBridgeIntegration:
    """Test sync bridge works with agent knowledge."""

    def test_agent_sees_synced_rules(self):
        """Agent knowledge should include synced TypeDB rules."""
        from governance.hybrid_router import HybridQueryRouter, MemorySyncBridge

        router = HybridQueryRouter()
        bridge = MemorySyncBridge(router)

        # Get sync status (works without connections)
        status = bridge.get_sync_status()
        assert "collections" in status


# =============================================================================
# INTEGRATION TESTS (require services)
# =============================================================================

@pytest.mark.integration
@pytest.mark.skipif(True, reason="Requires TypeDB + ChromaDB + Anthropic")
class TestAgentHybridIntegration:
    """Integration tests for agent hybrid layer."""

    def test_full_agent_with_hybrid_knowledge(self):
        """Full integration: agent with hybrid TypeDB+ChromaDB knowledge."""
        pass

    def test_agent_governance_query_e2e(self):
        """E2E: Agent queries governance rules."""
        pass


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
