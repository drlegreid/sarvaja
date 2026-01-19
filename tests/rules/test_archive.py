"""
Rules Archive Tests
===================
Tests for rule archive and restore functionality.
Per DOC-SIZE-01-v1: Split from test_rules_crud.py (838 lines)
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict

from governance.client import TypeDBClient, Rule


class TestRulesArchive:
    """Tests for rule archive functionality."""

    def test_delete_rule_archives_by_default(self, sample_rule):
        """Test that delete_rule archives the rule by default."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True
            mock_session = MagicMock()
            mock_tx = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
            mock_session.transaction.return_value.__exit__ = MagicMock(return_value=False)
            client._driver = MagicMock()
            client._driver.session.return_value = mock_session

            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                with patch.object(client, 'archive_rule', return_value={"rule": asdict(sample_rule)}) as mock_archive:
                    result = client.delete_rule(sample_rule.id)
                    mock_archive.assert_called_once_with(sample_rule.id, reason="deleted")
                    assert result is True

    def test_delete_rule_can_skip_archive(self, sample_rule):
        """Test that delete_rule can skip archiving with archive=False."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True
            mock_session = MagicMock()
            mock_tx = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
            mock_session.transaction.return_value.__exit__ = MagicMock(return_value=False)
            client._driver = MagicMock()
            client._driver.session.return_value = mock_session

            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                with patch.object(client, 'archive_rule') as mock_archive:
                    result = client.delete_rule(sample_rule.id, archive=False)
                    mock_archive.assert_not_called()
                    assert result is True

    def test_archive_rule_returns_none_for_missing(self):
        """Test that archive_rule returns None for non-existent rule."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=None):
                result = client.archive_rule("RULE-NONEXISTENT")
                assert result is None

    def test_archive_rule_creates_record(self, sample_rule, tmp_path):
        """Test that archive_rule creates an archive record."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                with patch.object(client, 'get_rule_dependencies', return_value=[]):
                    with patch.object(client, 'get_rules_depending_on', return_value=[]):
                        with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                            result = client.archive_rule(sample_rule.id)

                            assert result is not None
                            assert result["rule"]["id"] == sample_rule.id
                            assert "archived_at" in result
                            assert result["reason"] == "archived"

                            files = list(tmp_path.glob("*.json"))
                            assert len(files) == 1
                            assert sample_rule.id in files[0].name

    def test_get_archived_rules_empty(self, tmp_path):
        """Test get_archived_rules returns empty list when no archives."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                result = client.get_archived_rules()
                assert result == []

    def test_get_archived_rule_returns_most_recent(self, sample_rule, tmp_path):
        """Test get_archived_rule returns the most recent archive."""
        import json as json_module

        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            tmp_path.mkdir(parents=True, exist_ok=True)
            archive1 = tmp_path / f"{sample_rule.id}_20240101_120000.json"
            archive2 = tmp_path / f"{sample_rule.id}_20240102_120000.json"

            record1 = {"rule": asdict(sample_rule), "archived_at": "2024-01-01T12:00:00"}
            record2 = {"rule": asdict(sample_rule), "archived_at": "2024-01-02T12:00:00"}

            with open(archive1, 'w') as f:
                json_module.dump(record1, f)
            with open(archive2, 'w') as f:
                json_module.dump(record2, f)

            with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                result = client.get_archived_rule(sample_rule.id)
                assert result is not None
                assert result["archived_at"] == "2024-01-02T12:00:00"

    def test_restore_rule_raises_if_exists(self, sample_rule, tmp_path):
        """Test restore_rule raises ValueError if rule already exists."""
        import json as json_module

        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            tmp_path.mkdir(parents=True, exist_ok=True)
            archive_file = tmp_path / f"{sample_rule.id}_20240101_120000.json"
            record = {"rule": asdict(sample_rule), "archived_at": "2024-01-01T12:00:00"}
            with open(archive_file, 'w') as f:
                json_module.dump(record, f)

            with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                    with pytest.raises(ValueError, match="already exists"):
                        client.restore_rule(sample_rule.id)

    def test_restore_rule_returns_none_if_no_archive(self):
        """Test restore_rule returns None if no archive exists."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_archived_rule', return_value=None):
                result = client.restore_rule("RULE-NONEXISTENT")
                assert result is None


class TestMCPArchiveTools:
    """Tests for MCP archive tool wrappers."""

    def test_governance_list_archived_rules(self, mock_client):
        """Test rules_list_archived returns JSON array."""
        mock_client.get_archived_rules.return_value = [
            {
                "rule": {"id": "RULE-001", "name": "Test"},
                "archived_at": "2024-01-01T12:00:00",
                "reason": "deleted",
                "dependencies": [],
                "dependents": []
            }
        ]

        with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rules_list_archived']()

            data = json.loads(result)
            assert "archives" in data
            assert data["count"] == 1
            assert data["archives"][0]["rule_id"] == "RULE-001"

    def test_governance_get_archived_rule_success(self, mock_client, sample_rule):
        """Test rule_get_archived returns archive data."""
        mock_client.get_archived_rule.return_value = {
            "rule": asdict(sample_rule),
            "archived_at": "2024-01-01T12:00:00",
            "reason": "deleted"
        }

        with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_get_archived'](rule_id=sample_rule.id)

            data = json.loads(result)
            assert "rule" in data
            assert data["rule"]["id"] == sample_rule.id

    def test_governance_get_archived_rule_not_found(self, mock_client):
        """Test rule_get_archived returns error for missing archive."""
        mock_client.get_archived_rule.return_value = None

        with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_get_archived'](rule_id="RULE-NONEXISTENT")

            data = json.loads(result)
            assert "error" in data

    def test_governance_restore_rule_success(self, mock_client, sample_rule):
        """Test rule_restore returns restored rule."""
        restored_rule = Rule(
            id=sample_rule.id,
            name=sample_rule.name,
            category=sample_rule.category,
            priority=sample_rule.priority,
            status="DRAFT",
            directive=sample_rule.directive
        )
        mock_client.restore_rule.return_value = restored_rule

        with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_restore'](rule_id=sample_rule.id)

            data = json.loads(result)
            assert data["success"] is True
            assert "restored" in data["message"].lower()
            assert data["rule"]["status"] == "DRAFT"

    def test_governance_restore_rule_not_found(self, mock_client):
        """Test rule_restore returns error for missing archive."""
        mock_client.restore_rule.return_value = None

        with patch('governance.mcp_tools.rules_archive.get_typedb_client', return_value=mock_client):
            from governance.mcp_tools.rules import register_rule_tools

            mock_mcp = Mock()
            registered_funcs = {}

            def tool_decorator():
                def inner(func):
                    registered_funcs[func.__name__] = func
                    return func
                return inner

            mock_mcp.tool = tool_decorator
            register_rule_tools(mock_mcp)

            result = registered_funcs['rule_restore'](rule_id="RULE-NONEXISTENT")

            data = json.loads(result)
            assert "error" in data
