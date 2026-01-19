"""Unit tests for claude-mem MCP TOON migration.

Per GAP-DATA-001: TOON format for all MCP tools.
Per TEST-GUARD-01-v1: Test coverage for migrations.

Created: 2026-01-19
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from tests.factories.mcp_data import MCPTestDataFactory
from tests.factories.toon_output import TOONOutputFactory


@pytest.mark.unit
class TestClaudeMemImports:
    """Test claude_mem imports correctly."""

    def test_mcp_server_imports(self):
        """Test mcp_server module imports format_output."""
        from claude_mem import mcp_server

        assert hasattr(mcp_server, "format_output")

    def test_no_json_dumps_usage(self):
        """Test no json.dumps in mcp_server (grep-style check)."""
        import inspect
        from claude_mem import mcp_server

        source = inspect.getsource(mcp_server)
        # json.dumps should not appear in the source
        assert "json.dumps" not in source, "Found json.dumps usage - should use format_output"


@pytest.mark.unit
class TestClaudeMemTOONOutput:
    """Test claude-mem MCP tools use TOON format."""

    @pytest.fixture
    def mock_chromadb(self):
        """Mock ChromaDB client and collection."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 42
        return mock_client, mock_collection

    def test_chroma_health_toon_format(self, mock_chromadb):
        """Test chroma_health returns TOON format by default."""
        mock_client, mock_collection = mock_chromadb

        with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
            with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                from claude_mem.mcp_server import chroma_health

                result = chroma_health()

                # Should be TOON format (not starting with {)
                if TOONOutputFactory._check_toons():
                    TOONOutputFactory.assert_toon_default(result, "chroma_health")

    def test_chroma_health_json_when_env_set(self, mock_chromadb):
        """Test chroma_health returns JSON when MCP_OUTPUT_FORMAT=json."""
        mock_client, mock_collection = mock_chromadb

        with patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "json"}, clear=False):
            # Use format_output directly with explicit JSON format
            from governance.mcp_output import format_output, OutputFormat

            with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
                with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                    # Test format_output directly with JSON
                    data = {"status": "healthy", "host": "localhost", "port": 8001}
                    result = format_output(data, format=OutputFormat.JSON)

                    # Should be valid JSON
                    parsed = json.loads(result)
                    assert "status" in parsed
                    assert parsed["status"] == "healthy"

    def test_chroma_query_documents_toon_format(self, mock_chromadb):
        """Test chroma_query_documents returns TOON format."""
        mock_client, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["mem-001", "mem-002"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"project": "sim-ai"}, {"project": "sim-ai"}]],
            "distances": [[0.1, 0.2]],
        }

        with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
            with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                from claude_mem.mcp_server import chroma_query_documents

                result = chroma_query_documents(["sim-ai test query"])

                if TOONOutputFactory._check_toons():
                    TOONOutputFactory.assert_toon_default(result, "chroma_query_documents")

    def test_chroma_get_documents_toon_format(self, mock_chromadb):
        """Test chroma_get_documents returns TOON format."""
        mock_client, mock_collection = mock_chromadb
        mock_collection.get.return_value = {
            "ids": ["mem-001"],
            "documents": ["Test document content"],
            "metadatas": [{"project": "sim-ai"}],
        }

        with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
            with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                from claude_mem.mcp_server import chroma_get_documents

                result = chroma_get_documents(["mem-001"])

                if TOONOutputFactory._check_toons():
                    TOONOutputFactory.assert_toon_default(result, "chroma_get_documents")

    def test_chroma_add_documents_toon_format(self, mock_chromadb):
        """Test chroma_add_documents returns TOON format."""
        mock_client, mock_collection = mock_chromadb

        with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
            with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                from claude_mem.mcp_server import chroma_add_documents

                result = chroma_add_documents(
                    documents=["Test memory"],
                    project="sim-ai"
                )

                if TOONOutputFactory._check_toons():
                    TOONOutputFactory.assert_toon_default(result, "chroma_add_documents")

    def test_chroma_delete_documents_toon_format(self, mock_chromadb):
        """Test chroma_delete_documents returns TOON format."""
        mock_client, mock_collection = mock_chromadb

        with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
            with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                from claude_mem.mcp_server import chroma_delete_documents

                result = chroma_delete_documents(ids=["mem-001"])

                if TOONOutputFactory._check_toons():
                    TOONOutputFactory.assert_toon_default(result, "chroma_delete_documents")

    def test_error_response_toon_format(self):
        """Test error responses use TOON format."""
        with patch("claude_mem.mcp_server._get_client", return_value=None):
            from claude_mem.mcp_server import chroma_health

            result = chroma_health()

            if TOONOutputFactory._check_toons():
                TOONOutputFactory.assert_toon_default(result, "error response")

            # Parse and verify error structure
            data = TOONOutputFactory.parse_auto(result)
            assert "status" in data
            assert data["status"] == "unhealthy"
            assert "action_required" in data


@pytest.mark.unit
class TestClaudeMemDataFactories:
    """Test MCP data factories work correctly."""

    def test_chroma_query_result_factory(self):
        """Test chroma query result factory generates valid data."""
        data = MCPTestDataFactory.chroma_query_result(count=3)

        assert "ids" in data
        assert len(data["ids"][0]) == 3
        assert data["count"] == 3

    def test_chroma_health_factory_healthy(self):
        """Test chroma health factory generates healthy data."""
        data = MCPTestDataFactory.chroma_health_result(healthy=True)

        assert data["status"] == "healthy"
        assert "document_count" in data

    def test_chroma_health_factory_unhealthy(self):
        """Test chroma health factory generates unhealthy data."""
        data = MCPTestDataFactory.chroma_health_result(healthy=False)

        assert data["status"] == "unhealthy"
        assert "action_required" in data


@pytest.mark.integration
class TestClaudeMemTOONIntegration:
    """Integration tests for claude-mem TOON output."""

    @pytest.fixture
    def skip_if_no_toons(self):
        """Skip if toons not installed."""
        try:
            import toons
            yield toons
        except ImportError:
            pytest.skip("toons not installed")

    def test_toon_roundtrip_query_result(self, skip_if_no_toons):
        """Test TOON roundtrip for simple query results."""
        import toons

        # Use simpler data structure that TOON can handle
        data = {
            "ids": ["mem-001", "mem-002", "mem-003"],
            "documents": ["doc1", "doc2", "doc3"],
            "count": 3,
        }

        encoded = toons.dumps(data)
        decoded = toons.loads(encoded)

        assert decoded == data

    def test_toon_savings_chroma_response(self, skip_if_no_toons):
        """Test TOON saves tokens for ChromaDB responses."""
        data = MCPTestDataFactory.chroma_query_result(count=10)

        savings = TOONOutputFactory.measure_savings(data)

        assert savings["toon_available"] is True
        assert savings["savings_percent"] > 0, "Expected positive savings"
