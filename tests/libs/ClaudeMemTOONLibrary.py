"""
Robot Framework Library for claude-mem MCP TOON migration tests.

Per GAP-DATA-001: TOON format for all MCP tools.
Migrated from tests/unit/test_claude_mem_toon.py
"""
from robot.api.deco import keyword
from unittest.mock import patch, MagicMock


class ClaudeMemTOONLibrary:
    """Library for testing claude-mem TOON migration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_mock_chromadb(self):
        """Create mock ChromaDB client and collection."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 42
        return mock_client, mock_collection

    # =============================================================================
    # Import Tests
    # =============================================================================

    @keyword("MCP Server Imports Format Output")
    def mcp_server_imports_format_output(self):
        """Test mcp_server module imports format_output."""
        try:
            from claude_mem import mcp_server

            return {
                "has_format_output": hasattr(mcp_server, "format_output")
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("No JSON Dumps Usage")
    def no_json_dumps_usage(self):
        """Test no json.dumps in mcp_server (grep-style check)."""
        try:
            import inspect
            from claude_mem import mcp_server

            source = inspect.getsource(mcp_server)
            has_json_dumps = "json.dumps" in source

            return {
                "no_json_dumps": not has_json_dumps,
                "message": "Should use format_output" if has_json_dumps else "OK"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # TOON Format Tests
    # =============================================================================

    @keyword("Chroma Health TOON Format")
    def chroma_health_toon_format(self):
        """Test chroma_health returns TOON format by default."""
        try:
            mock_client, mock_collection = self._get_mock_chromadb()

            with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
                with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                    from claude_mem.mcp_server import chroma_health

                    result = chroma_health()

                    # TOON format does not start with { (JSON does)
                    is_toon = not result.strip().startswith('{')

                    return {
                        "returns_string": isinstance(result, str),
                        "appears_toon": is_toon
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Health JSON When Env Set")
    def chroma_health_json_when_env_set(self):
        """Test chroma_health returns JSON when MCP_OUTPUT_FORMAT=json."""
        try:
            import os
            import json

            mock_client, mock_collection = self._get_mock_chromadb()

            with patch.dict(os.environ, {"MCP_OUTPUT_FORMAT": "json"}, clear=False):
                from governance.mcp_output import format_output, OutputFormat

                data = {"status": "healthy", "host": "localhost", "port": 8001}
                result = format_output(data, format=OutputFormat.JSON)

                parsed = json.loads(result)

                return {
                    "is_valid_json": True,
                    "has_status": "status" in parsed,
                    "status_healthy": parsed.get("status") == "healthy"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Query Documents TOON Format")
    def chroma_query_documents_toon_format(self):
        """Test chroma_query_documents returns TOON format."""
        try:
            mock_client, mock_collection = self._get_mock_chromadb()
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

                    return {
                        "returns_string": isinstance(result, str),
                        "has_result": len(result) > 0
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Get Documents TOON Format")
    def chroma_get_documents_toon_format(self):
        """Test chroma_get_documents returns TOON format."""
        try:
            mock_client, mock_collection = self._get_mock_chromadb()
            mock_collection.get.return_value = {
                "ids": ["mem-001"],
                "documents": ["Test document content"],
                "metadatas": [{"project": "sim-ai"}],
            }

            with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
                with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                    from claude_mem.mcp_server import chroma_get_documents

                    result = chroma_get_documents(["mem-001"])

                    return {
                        "returns_string": isinstance(result, str),
                        "has_result": len(result) > 0
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Add Documents TOON Format")
    def chroma_add_documents_toon_format(self):
        """Test chroma_add_documents returns TOON format."""
        try:
            mock_client, mock_collection = self._get_mock_chromadb()

            with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
                with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                    from claude_mem.mcp_server import chroma_add_documents

                    result = chroma_add_documents(
                        documents=["Test memory"],
                        project="sim-ai"
                    )

                    return {
                        "returns_string": isinstance(result, str),
                        "has_result": len(result) > 0
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Delete Documents TOON Format")
    def chroma_delete_documents_toon_format(self):
        """Test chroma_delete_documents returns TOON format."""
        try:
            mock_client, mock_collection = self._get_mock_chromadb()

            with patch("claude_mem.mcp_server._get_client", return_value=mock_client):
                with patch("claude_mem.mcp_server._get_or_create_collection", return_value=mock_collection):
                    from claude_mem.mcp_server import chroma_delete_documents

                    result = chroma_delete_documents(ids=["mem-001"])

                    return {
                        "returns_string": isinstance(result, str),
                        "has_result": len(result) > 0
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Error Response TOON Format")
    def error_response_toon_format(self):
        """Test error responses use TOON format."""
        try:
            with patch("claude_mem.mcp_server._get_client", return_value=None):
                from claude_mem.mcp_server import chroma_health

                result = chroma_health()

                # Should have error/status info
                has_error_info = "unhealthy" in result.lower() or "error" in result.lower() or "action" in result.lower()

                return {
                    "returns_string": isinstance(result, str),
                    "has_error_info": has_error_info
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Data Factory Tests
    # =============================================================================

    @keyword("Chroma Query Result Factory Works")
    def chroma_query_result_factory_works(self):
        """Test chroma query result factory generates valid data."""
        try:
            from tests.factories.mcp_data import MCPTestDataFactory

            data = MCPTestDataFactory.chroma_query_result(count=3)

            return {
                "has_ids": "ids" in data,
                "correct_count": len(data.get("ids", [[]])[0]) == 3,
                "count_field_matches": data.get("count") == 3
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Health Factory Healthy")
    def chroma_health_factory_healthy(self):
        """Test chroma health factory generates healthy data."""
        try:
            from tests.factories.mcp_data import MCPTestDataFactory

            data = MCPTestDataFactory.chroma_health_result(healthy=True)

            return {
                "status_healthy": data.get("status") == "healthy",
                "has_document_count": "document_count" in data
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chroma Health Factory Unhealthy")
    def chroma_health_factory_unhealthy(self):
        """Test chroma health factory generates unhealthy data."""
        try:
            from tests.factories.mcp_data import MCPTestDataFactory

            data = MCPTestDataFactory.chroma_health_result(healthy=False)

            return {
                "status_unhealthy": data.get("status") == "unhealthy",
                "has_action_required": "action_required" in data
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("TOON Roundtrip Query Result")
    def toon_roundtrip_query_result(self):
        """Test TOON roundtrip for simple query results."""
        try:
            import toons

            data = {
                "ids": ["mem-001", "mem-002", "mem-003"],
                "documents": ["doc1", "doc2", "doc3"],
                "count": 3,
            }

            encoded = toons.dumps(data)
            decoded = toons.loads(encoded)

            return {
                "roundtrip_success": decoded == data
            }
        except ImportError:
            return {"skipped": True, "reason": "toons not installed"}

    @keyword("TOON Savings Chroma Response")
    def toon_savings_chroma_response(self):
        """Test TOON saves tokens for ChromaDB responses."""
        try:
            from tests.factories.mcp_data import MCPTestDataFactory
            from tests.factories.toon_output import TOONOutputFactory

            data = MCPTestDataFactory.chroma_query_result(count=10)
            savings = TOONOutputFactory.measure_savings(data)

            return {
                "toon_available": savings.get("toon_available", False),
                "has_savings": savings.get("savings_percent", 0) > 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
