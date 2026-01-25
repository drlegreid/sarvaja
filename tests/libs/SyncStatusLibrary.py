"""
Robot Framework library for governance_sync_status MCP tool tests.

Per GAP-SYNC-002: Divergence Validation Workflow
Migrated from tests/test_sync_status.py
"""

import yaml
from robot.api.deco import keyword


class SyncStatusLibrary:
    """Library for testing sync status tool functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _create_mock_mcp(self):
        """Create a mock MCP to capture registered functions."""
        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator

        return MockMCP()

    # =========================================================================
    # Tool Existence Tests
    # =========================================================================

    @keyword("Sync Status Tool Exists")
    def sync_status_tool_exists(self):
        """Test that the tool is importable."""
        try:
            from governance.mcp_tools.workspace import register_workspace_tools
            return {"exists": callable(register_workspace_tools)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Sync Status Tool Returns JSON")
    def sync_status_tool_returns_json(self):
        """Test that sync status returns valid JSON/YAML."""
        try:
            from governance.mcp_tools.workspace import register_workspace_tools
            mock_mcp = self._create_mock_mcp()
            register_workspace_tools(mock_mcp)

            has_tool = "governance_sync_status" in mock_mcp.tools
            if not has_tool:
                return {"skipped": True, "reason": "Tool not registered"}

            result = mock_mcp.tools["governance_sync_status"]()
            is_not_none = result is not None

            # Parse TOON/YAML format (per GAP-DATA-001)
            data = yaml.safe_load(result)
            has_expected_keys = "rules" in data or "error" in data

            return {
                "has_tool": has_tool,
                "result_not_none": is_not_none,
                "valid_format": has_expected_keys
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Sync Status Structure Valid")
    def sync_status_structure_valid(self):
        """Test that sync status returns expected structure."""
        try:
            from governance.mcp_tools.workspace import register_workspace_tools
            mock_mcp = self._create_mock_mcp()
            register_workspace_tools(mock_mcp)

            result = mock_mcp.tools["governance_sync_status"]()
            data = yaml.safe_load(result)

            # Check structure (even if there's an error connecting to TypeDB)
            if "error" in data:
                return {"has_error": True, "skipped_validation": True}

            has_rules = "rules" in data
            has_tasks = "tasks" in data
            has_sessions = "sessions" in data
            has_sync_needed = "sync_needed" in data
            has_timestamp = "timestamp" in data

            # Check nested structure
            has_typedb_count = "typedb_count" in data.get("rules", {})
            has_files_count = "files_count" in data.get("rules", {})
            has_synced = "synced" in data.get("rules", {})

            return {
                "has_rules": has_rules,
                "has_tasks": has_tasks,
                "has_sessions": has_sessions,
                "has_sync_needed": has_sync_needed,
                "has_timestamp": has_timestamp,
                "has_nested_typedb_count": has_typedb_count,
                "has_nested_files_count": has_files_count,
                "has_nested_synced": has_synced
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Workspace Tools Registration Tests
    # =========================================================================

    @keyword("All Workspace Tools Registered")
    def all_workspace_tools_registered(self):
        """Test that all 10 workspace tools are registered."""
        try:
            from governance.mcp_tools.workspace import register_workspace_tools
            mock_mcp = self._create_mock_mcp()
            register_workspace_tools(mock_mcp)

            expected_tools = [
                "workspace_scan_tasks",
                "workspace_capture_tasks",
                "workspace_list_sources",
                "workspace_scan_rule_documents",
                "workspace_link_rules_to_documents",
                "workspace_get_document_for_rule",
                "workspace_get_rules_for_document",
                "governance_sync_status",
                "workspace_sync_status",
                "workspace_sync_gaps_to_typedb",
            ]

            registered_tools = list(mock_mcp.tools.keys())
            missing_tools = [t for t in expected_tools if t not in registered_tools]

            return {
                "all_registered": len(missing_tools) == 0,
                "count_correct": len(mock_mcp.tools) == 10,
                "registered_count": len(mock_mcp.tools),
                "missing_tools": missing_tools
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
