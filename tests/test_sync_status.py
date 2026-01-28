"""
Tests for governance_sync_status MCP tool.

Per GAP-SYNC-002: Divergence Validation Workflow.
"""

import yaml
import pytest


class TestSyncStatusTool:
    """Test the governance_sync_status tool."""

    def test_tool_exists(self):
        """Test that the tool is importable."""
        from governance.mcp_tools.workspace import register_workspace_tools
        assert callable(register_workspace_tools)

    def test_tool_returns_json(self):
        """Test that sync status returns valid JSON."""
        # Create a mock MCP to capture the registered function
        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator

        mock_mcp = MockMCP()
        from governance.mcp_tools.workspace import register_workspace_tools
        register_workspace_tools(mock_mcp)

        assert "governance_sync_status" in mock_mcp.tools

        # Call the tool
        result = mock_mcp.tools["governance_sync_status"]()
        assert result is not None

        # Parse TOON/YAML format (per GAP-DATA-001)
        data = yaml.safe_load(result)
        assert "rules" in data or "error" in data

    def test_sync_status_structure(self):
        """Test that sync status returns expected structure."""
        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator

        mock_mcp = MockMCP()
        from governance.mcp_tools.workspace import register_workspace_tools
        register_workspace_tools(mock_mcp)

        result = mock_mcp.tools["governance_sync_status"]()
        data = yaml.safe_load(result)

        # Check structure (even if there's an error connecting to TypeDB)
        if "error" not in data:
            assert "rules" in data
            assert "tasks" in data
            assert "sessions" in data
            assert "sync_needed" in data
            assert "timestamp" in data

            # Check nested structure
            if "rules" in data:
                assert "typedb_count" in data["rules"]
                assert "files_count" in data["rules"]
                assert "synced" in data["rules"]


class TestWorkspaceToolsRegistration:
    """Test that all workspace tools are registered."""

    def test_all_workspace_tools_registered(self):
        """Test that all 10 workspace tools are registered."""
        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator

        mock_mcp = MockMCP()
        from governance.mcp_tools.workspace import register_workspace_tools
        register_workspace_tools(mock_mcp)

        expected_tools = [
            "workspace_scan_tasks",
            "workspace_capture_tasks",
            "workspace_list_sources",
            "workspace_scan_rule_documents",
            "workspace_link_rules_to_documents",
            "workspace_get_document_for_rule",
            "workspace_get_rules_for_document",
            "governance_sync_status",  # GAP-SYNC-002
            "workspace_sync_status",   # Alias for governance_sync_status
            "workspace_sync_gaps_to_typedb",  # GAP-GAPS-TASKS-001
        ]

        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools, f"Missing tool: {tool_name}"

        assert len(mock_mcp.tools) == 10
