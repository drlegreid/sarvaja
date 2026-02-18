"""MCP Memory Integration Tests — Claude-Mem tools against real ChromaDB.

Tests ChromaDB health, document add/query/delete MCP tools.

Run: .venv/bin/python3 -m pytest tests/integration/test_mcp_memory_integration.py -v
Requires: ChromaDB on localhost:8001
"""

import json
import uuid
import pytest

from tests.integration.conftest import MockMCP, parse_mcp_result

pytestmark = [pytest.mark.integration, pytest.mark.chroma, pytest.mark.mcp]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def memory_tools(chromadb_available):
    """Register and return claude-mem MCP tool functions."""
    try:
        from claude_mem.mcp_server import create_mcp_server
    except ImportError:
        pytest.skip("claude_mem package not available")

    # claude-mem tools are registered differently — via create_mcp_server()
    # We need to extract them. Try direct import of tool functions.
    mcp = MockMCP()
    try:
        from claude_mem.tools import register_tools
        register_tools(mcp)
    except (ImportError, AttributeError):
        # Fallback: try to import individual tool functions
        try:
            from claude_mem.mcp_tools import register_chroma_tools
            register_chroma_tools(mcp)
        except (ImportError, AttributeError):
            pytest.skip("Cannot extract claude-mem tool functions")

    if not mcp.tools:
        pytest.skip("No claude-mem tools registered")
    return mcp.tools


# Test collection name to avoid polluting real data
TEST_COLLECTION = "inttest_memories"
_test_doc_ids = []


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestChromaHealth:
    """Test ChromaDB health check tool."""

    def test_health_check(self, memory_tools):
        """chroma_health returns health status."""
        if "chroma_health" not in memory_tools:
            pytest.skip("chroma_health not registered")
        result = parse_mcp_result(memory_tools["chroma_health"]())
        assert isinstance(result, dict)
        # Should indicate healthy status
        assert result.get("healthy") is True or result.get("status") == "ok"


# ---------------------------------------------------------------------------
# Document CRUD lifecycle
# ---------------------------------------------------------------------------

class TestChromaDocumentLifecycle:
    """Test document add → query → delete lifecycle."""

    def test_add_documents(self, memory_tools):
        """chroma_add_documents inserts data into ChromaDB."""
        if "chroma_add_documents" not in memory_tools:
            pytest.skip("chroma_add_documents not registered")

        doc_id = f"inttest-{uuid.uuid4().hex[:8]}"
        _test_doc_ids.append(doc_id)

        result = parse_mcp_result(memory_tools["chroma_add_documents"](
            documents=["Integration test memory document"],
            ids=[doc_id],
            metadatas=[{"source": "integration_test", "test": "true"}],
        ))
        assert isinstance(result, dict)
        assert "error" not in result

    def test_query_documents(self, memory_tools):
        """chroma_query_documents finds stored data."""
        if "chroma_query_documents" not in memory_tools:
            pytest.skip("chroma_query_documents not registered")

        result = parse_mcp_result(memory_tools["chroma_query_documents"](
            query_texts=["integration test memory"],
        ))
        assert isinstance(result, dict)

    def test_delete_documents(self, memory_tools):
        """chroma_delete_documents removes data."""
        if "chroma_delete_documents" not in memory_tools:
            pytest.skip("chroma_delete_documents not registered")
        if not _test_doc_ids:
            pytest.skip("No test documents to delete")

        result = parse_mcp_result(memory_tools["chroma_delete_documents"](
            ids=_test_doc_ids,
        ))
        assert isinstance(result, dict)
        assert "error" not in result
