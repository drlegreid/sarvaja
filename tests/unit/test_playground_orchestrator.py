"""
Unit tests for Playground Orchestrator.

Batch 123: Tests for agent/playground_orchestrator.py
- create_chromadb_knowledge(): ChromaDB connection factory
- create_hybrid_knowledge(): Hybrid TypeDB+ChromaDB factory
- create_orchestrator(): OrchestratorEngine factory
- start_orchestration(): Async start
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


_MOD = "agent.playground_orchestrator"


# ── create_chromadb_knowledge ────────────────────────────────


class TestCreateChromadbKnowledge:
    """Tests for create_chromadb_knowledge factory."""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_chromadb_host_returns_none(self):
        from agent.playground_orchestrator import create_chromadb_knowledge
        os.environ.pop("CHROMADB_HOST", None)
        result = create_chromadb_knowledge()
        assert result is None

    @patch.dict(os.environ, {"CHROMADB_HOST": "localhost", "CHROMADB_PORT": "8001"})
    def test_successful_connection(self):
        # Inject mock chromadb into sys.modules for lazy import
        mock_chromadb = MagicMock()
        mock_client = MagicMock()
        mock_chromadb.HttpClient.return_value = mock_client

        with patch.dict(sys.modules, {"chromadb": mock_chromadb}):
            from agent.playground_orchestrator import create_chromadb_knowledge, ChromaDb, Knowledge
            with patch(f"{_MOD}.ChromaDb") as mock_cls, \
                 patch(f"{_MOD}.Knowledge") as mock_knowledge:
                mock_vector_db = MagicMock()
                mock_cls.return_value = mock_vector_db
                mock_knowledge_instance = MagicMock()
                mock_knowledge.return_value = mock_knowledge_instance

                result = create_chromadb_knowledge()
                assert result is mock_knowledge_instance
                mock_client.heartbeat.assert_called_once()
                mock_cls.assert_called_once_with(collection="sim_ai_knowledge")

    @patch.dict(os.environ, {"CHROMADB_HOST": "localhost"})
    def test_connection_failure_returns_none(self):
        mock_chromadb = MagicMock()
        mock_chromadb.HttpClient.side_effect = Exception("Connection refused")

        with patch.dict(sys.modules, {"chromadb": mock_chromadb}):
            from agent.playground_orchestrator import create_chromadb_knowledge
            result = create_chromadb_knowledge()
            assert result is None

    @patch.dict(os.environ, {"CHROMADB_HOST": "host", "CHROMA_AUTH_TOKEN": "secret"})
    def test_auth_token_passed(self):
        mock_chromadb = MagicMock()
        mock_chromadb.HttpClient.return_value = MagicMock()

        with patch.dict(sys.modules, {"chromadb": mock_chromadb}):
            from agent.playground_orchestrator import create_chromadb_knowledge
            with patch(f"{_MOD}.ChromaDb", return_value=MagicMock()), \
                 patch(f"{_MOD}.Knowledge", return_value=MagicMock()):
                create_chromadb_knowledge()
                call_kwargs = mock_chromadb.HttpClient.call_args[1]
                assert call_kwargs["headers"]["X-Chroma-Token"] == "secret"


# ── create_hybrid_knowledge ──────────────────────────────────


class TestCreateHybridKnowledge:
    """Tests for create_hybrid_knowledge factory."""

    @patch(f"{_MOD}.HYBRID_AVAILABLE", False)
    @patch(f"{_MOD}.create_chromadb_knowledge", return_value=None)
    def test_no_hybrid_falls_back_to_chromadb(self, mock_chromadb):
        from agent.playground_orchestrator import create_hybrid_knowledge
        result = create_hybrid_knowledge()
        mock_chromadb.assert_called_once()

    @patch(f"{_MOD}.HYBRID_AVAILABLE", True)
    @patch.dict(os.environ, {}, clear=True)
    def test_no_chromadb_host_returns_none(self):
        from agent.playground_orchestrator import create_hybrid_knowledge
        os.environ.pop("CHROMADB_HOST", None)
        result = create_hybrid_knowledge()
        assert result is None

    @patch(f"{_MOD}.HYBRID_AVAILABLE", True)
    @patch.dict(os.environ, {"CHROMADB_HOST": "localhost", "CHROMADB_PORT": "8001"})
    @patch(f"{_MOD}.HybridVectorDb")
    @patch(f"{_MOD}.Knowledge")
    def test_successful_hybrid(self, mock_knowledge, mock_hybrid):
        from agent.playground_orchestrator import create_hybrid_knowledge
        mock_db = MagicMock()
        mock_hybrid.return_value = mock_db
        mock_knowledge.return_value = MagicMock()

        result = create_hybrid_knowledge()
        assert result is not None
        mock_hybrid.assert_called_once()
        call_kwargs = mock_hybrid.call_args[1]
        assert call_kwargs["chromadb_host"] == "localhost"
        assert call_kwargs["collection_name"] == "sim_ai_knowledge"

    @patch(f"{_MOD}.HYBRID_AVAILABLE", True)
    @patch.dict(os.environ, {"CHROMADB_HOST": "localhost"})
    @patch(f"{_MOD}.HybridVectorDb", side_effect=Exception("Init failed"))
    @patch(f"{_MOD}.create_chromadb_knowledge", return_value=None)
    def test_hybrid_failure_falls_back_to_chromadb(self, mock_chromadb, mock_hybrid):
        from agent.playground_orchestrator import create_hybrid_knowledge
        result = create_hybrid_knowledge()
        mock_chromadb.assert_called_once()


# ── create_orchestrator ──────────────────────────────────────


class TestCreateOrchestrator:
    """Tests for create_orchestrator factory."""

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", False)
    def test_not_available_returns_none(self):
        from agent.playground_orchestrator import create_orchestrator
        result = create_orchestrator([], {})
        assert result is None

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch("governance.client.get_client", return_value=None)
    def test_no_typedb_client_returns_none(self, mock_client):
        from agent.playground_orchestrator import create_orchestrator
        result = create_orchestrator([], {})
        assert result is None

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch(f"{_MOD}.OrchestratorEngine")
    @patch(f"{_MOD}.AgentInfo")
    @patch("governance.client.get_client")
    def test_registers_agents_from_config(self, mock_client, mock_agent_info, mock_engine):
        from agent.playground_orchestrator import create_orchestrator
        mock_client.return_value = MagicMock()
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance

        config = {
            "agents": {
                "code-agent": {"name": "Code Agent", "role": "coding", "trust_score": "0.9"},
                "research-agent": {"name": "Research Agent", "role": "research"},
            }
        }
        result = create_orchestrator([], config)
        assert result is mock_engine_instance
        assert mock_engine_instance.register_agent.call_count == 2

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch(f"{_MOD}.OrchestratorEngine")
    @patch(f"{_MOD}.AgentInfo")
    @patch("governance.client.get_client")
    def test_default_trust_score(self, mock_client, mock_agent_info, mock_engine):
        from agent.playground_orchestrator import create_orchestrator
        mock_client.return_value = MagicMock()
        mock_engine.return_value = MagicMock()

        config = {"agents": {"agent-1": {"name": "Agent 1"}}}
        create_orchestrator([], config)
        call_kwargs = mock_agent_info.call_args[1]
        assert call_kwargs["trust_score"] == 0.8

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch(f"{_MOD}.OrchestratorEngine")
    @patch(f"{_MOD}.AgentInfo")
    @patch("governance.client.get_client")
    def test_default_role_is_coding(self, mock_client, mock_agent_info, mock_engine):
        from agent.playground_orchestrator import create_orchestrator, AgentRole
        mock_client.return_value = MagicMock()
        mock_engine.return_value = MagicMock()

        config = {"agents": {"agent-1": {"name": "Agent 1"}}}
        create_orchestrator([], config)
        call_kwargs = mock_agent_info.call_args[1]
        assert call_kwargs["role"] == AgentRole.CODING

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch("governance.client.get_client", side_effect=Exception("TypeDB down"))
    def test_exception_returns_none(self, mock_client):
        from agent.playground_orchestrator import create_orchestrator
        result = create_orchestrator([], {})
        assert result is None

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch(f"{_MOD}.OrchestratorEngine")
    @patch("governance.client.get_client")
    def test_empty_config_no_agents(self, mock_client, mock_engine):
        from agent.playground_orchestrator import create_orchestrator
        mock_client.return_value = MagicMock()
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance

        result = create_orchestrator([], {})
        assert result is mock_engine_instance
        mock_engine_instance.register_agent.assert_not_called()

    @patch(f"{_MOD}.ORCHESTRATOR_AVAILABLE", True)
    @patch(f"{_MOD}.OrchestratorEngine")
    @patch(f"{_MOD}.AgentInfo")
    @patch("governance.client.get_client")
    @patch.dict(os.environ, {"ORCHESTRATOR_POLL_INTERVAL": "30.0"})
    def test_poll_interval_from_env(self, mock_client, mock_agent_info, mock_engine):
        from agent.playground_orchestrator import create_orchestrator
        mock_client.return_value = MagicMock()
        mock_engine.return_value = MagicMock()

        create_orchestrator([], {"agents": {}})
        call_args = mock_engine.call_args
        assert call_args[1]["poll_interval"] == 30.0


# ── start_orchestration ──────────────────────────────────────


class TestStartOrchestration:
    """Tests for start_orchestration async function."""

    @pytest.mark.asyncio
    async def test_calls_engine_start(self):
        from agent.playground_orchestrator import start_orchestration
        engine = MagicMock()
        engine.start = AsyncMock()
        engine._poller = MagicMock()
        engine._poller._poll_interval = 10.0

        await start_orchestration(engine)
        engine.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handles_start_failure(self):
        from agent.playground_orchestrator import start_orchestration
        engine = MagicMock()
        engine.start = AsyncMock(side_effect=Exception("Start failed"))

        # Should not raise — catches exception internally
        await start_orchestration(engine)
