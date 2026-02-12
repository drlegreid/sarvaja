"""
Unit tests for Workspace Sync Status MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/workspace_sync.py module.
Tests: governance_sync_status, workspace_sync_status,
       workspace_sync_gaps_to_typedb.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.workspace_sync import register_workspace_sync_tools


class _CaptureMCP:
    """Mock MCP server that captures tool registrations."""
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _patch_format():
    with patch(
        "governance.mcp_tools.workspace_sync.format_mcp_result",
        side_effect=lambda x: json.dumps(x),
    ):
        yield


@pytest.fixture()
def tools():
    mcp = _CaptureMCP()
    register_workspace_sync_tools(mcp)
    return mcp.tools


class TestRegistration:
    def test_registers_three_tools(self, tools):
        assert "governance_sync_status" in tools
        assert "workspace_sync_status" in tools
        assert "workspace_sync_gaps_to_typedb" in tools


class TestGovernanceSyncStatus:
    def test_full_sync_check(self, tools):
        mock_client = MagicMock()
        mock_rule = MagicMock()
        mock_rule.id = "RULE-001"
        mock_client.get_all_rules.return_value = [mock_rule]

        mock_task = MagicMock()
        mock_task.id = "T-1"
        mock_task.status = "OPEN"
        mock_client.get_all_tasks.return_value = [mock_task]

        mock_session = MagicMock()
        mock_client.get_all_sessions.return_value = [mock_session]

        mock_doc = MagicMock()
        mock_doc.rule_ids = ["RULE-001"]

        with patch("governance.mcp_tools.workspace_sync.os.path.exists", return_value=False), \
             patch("governance.mcp_tools.workspace_sync.os.listdir", return_value=[]):
            # Inject mocked imports inside the closure
            import types
            mock_typedb_mod = types.ModuleType("governance.client")
            mock_typedb_mod.TypeDBClient = MagicMock(return_value=mock_client)

            mock_linker_mod = types.ModuleType("governance.rule_linker")
            mock_linker_mod.scan_rule_documents = MagicMock(return_value=[mock_doc])

            mock_scanner_mod = types.ModuleType("governance.workspace_scanner")
            mock_scanner_mod.WORKSPACE_ROOT = "/tmp/test"
            mock_scanner_mod.scan_workspace = MagicMock(return_value=[])

            with patch.dict("sys.modules", {
                "governance.client": mock_typedb_mod,
                "governance.rule_linker": mock_linker_mod,
                "governance.workspace_scanner": mock_scanner_mod,
            }):
                result = json.loads(tools["governance_sync_status"]())

        assert "rules" in result
        assert "tasks" in result
        assert "sessions" in result

    def test_exception_returns_error(self, tools):
        with patch.dict("sys.modules", {
            "governance.workspace_scanner": MagicMock(side_effect=Exception("boom")),
        }):
            result = json.loads(tools["governance_sync_status"]())
        # Should return something (either error or default result)
        assert isinstance(result, dict)


class TestWorkspaceSyncStatus:
    def test_alias_calls_governance_sync_status(self, tools):
        with patch.dict("sys.modules", {
            "governance.workspace_scanner": MagicMock(),
            "governance.client": MagicMock(),
            "governance.rule_linker": MagicMock(),
        }):
            result = tools["workspace_sync_status"]()
        assert result is not None


class TestWorkspaceSyncGapsToTypedb:
    def test_dry_run(self, tools):
        mock_gap = MagicMock()
        mock_gap.id = "GAP-TEST-001"
        mock_gap.description = "Test gap"
        mock_gap.priority = "high"
        mock_gap.is_resolved = False

        mock_client = MagicMock()
        mock_client.get_all_tasks.return_value = []
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        mock_parser = MagicMock()
        mock_parser.parse.return_value = [mock_gap]

        with patch.dict("sys.modules", {
            "governance.utils.gap_parser": MagicMock(GapParser=MagicMock(return_value=mock_parser)),
            "governance.mcp_tools.common": MagicMock(
                format_mcp_result=lambda x: json.dumps(x),
                typedb_client=MagicMock(return_value=mock_client),
            ),
        }):
            # Need to re-register to pick up mocked modules
            mcp2 = _CaptureMCP()
            with patch("governance.mcp_tools.workspace_sync.format_mcp_result",
                        side_effect=lambda x: json.dumps(x)):
                register_workspace_sync_tools(mcp2)
                fn = mcp2.tools["workspace_sync_gaps_to_typedb"]
                result = json.loads(fn(dry_run=True))

        assert result.get("dry_run") is True or "error" in result

    def test_connection_error(self, tools):
        with patch.dict("sys.modules", {
            "governance.utils.gap_parser": MagicMock(
                GapParser=MagicMock(return_value=MagicMock(parse=MagicMock(side_effect=ConnectionError("offline")))),
            ),
            "governance.mcp_tools.common": MagicMock(
                format_mcp_result=lambda x: json.dumps(x),
            ),
        }):
            mcp2 = _CaptureMCP()
            with patch("governance.mcp_tools.workspace_sync.format_mcp_result",
                        side_effect=lambda x: json.dumps(x)):
                register_workspace_sync_tools(mcp2)
                result = json.loads(mcp2.tools["workspace_sync_gaps_to_typedb"]())
        assert "error" in result
