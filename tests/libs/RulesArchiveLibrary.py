"""
Rules Archive Library for Robot Framework
Tests for rule archive and restore functionality.
Migrated from tests/rules/test_archive.py
Per: RF-007 Robot Framework Migration
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict
from robot.api.deco import keyword


class RulesArchiveLibrary:
    """Robot Framework keywords for rules archive tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_sample_rule(self):
        """Create a sample rule for testing."""
        try:
            from governance.client import Rule
            return Rule(
                id="RULE-TEST-001",
                name="Test Rule",
                category="testing",
                priority="MEDIUM",
                status="DRAFT",
                directive="This is a test rule directive."
            )
        except ImportError:
            return None

    # =========================================================================
    # Archive Functionality Tests
    # =========================================================================

    @keyword("Delete Rule Archives By Default")
    def delete_rule_archives_by_default(self):
        """Test that delete_rule archives the rule by default."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

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
                        return {"archives_called": True, "delete_returns_true": result is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AssertionError:
            return {"archives_called": False, "delete_returns_true": False}

    @keyword("Delete Rule Can Skip Archive")
    def delete_rule_can_skip_archive(self):
        """Test that delete_rule can skip archiving with archive=False."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

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
                        return {"archive_not_called": True, "delete_returns_true": result is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AssertionError:
            return {"archive_not_called": False, "delete_returns_true": False}

    @keyword("Archive Rule Returns None For Missing")
    def archive_rule_returns_none_for_missing(self):
        """Test that archive_rule returns None for non-existent rule."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, 'get_rule_by_id', return_value=None):
                    result = client.archive_rule("RULE-NONEXISTENT")
                    return {"returns_none": result is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Archive Rule Creates Record")
    def archive_rule_creates_record(self):
        """Test that archive_rule creates an archive record."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                with patch.object(TypeDBClient, 'connect', return_value=True):
                    client = TypeDBClient()
                    client._connected = True

                    with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                        with patch.object(client, 'get_rule_dependencies', return_value=[]):
                            with patch.object(client, 'get_rules_depending_on', return_value=[]):
                                with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                                    result = client.archive_rule(sample_rule.id)

                                    files = list(tmp_path.glob("*.json"))
                                    return {
                                        "result_not_none": result is not None,
                                        "has_rule_id": result["rule"]["id"] == sample_rule.id if result else False,
                                        "has_archived_at": "archived_at" in result if result else False,
                                        "file_created": len(files) == 1
                                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Archived Rules Empty")
    def get_archived_rules_empty(self):
        """Test get_archived_rules returns empty list when no archives."""
        try:
            from governance.client import TypeDBClient

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                with patch.object(TypeDBClient, 'connect', return_value=True):
                    client = TypeDBClient()
                    client._connected = True

                    with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                        result = client.get_archived_rules()
                        return {"returns_empty_list": result == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Archived Rule Returns Most Recent")
    def get_archived_rule_returns_most_recent(self):
        """Test get_archived_rule returns the most recent archive."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                # Create two archive files
                archive1 = tmp_path / f"{sample_rule.id}_20240101_120000.json"
                archive2 = tmp_path / f"{sample_rule.id}_20240102_120000.json"

                record1 = {"rule": asdict(sample_rule), "archived_at": "2024-01-01T12:00:00"}
                record2 = {"rule": asdict(sample_rule), "archived_at": "2024-01-02T12:00:00"}

                with open(archive1, 'w') as f:
                    json.dump(record1, f)
                with open(archive2, 'w') as f:
                    json.dump(record2, f)

                with patch.object(TypeDBClient, 'connect', return_value=True):
                    client = TypeDBClient()
                    client._connected = True

                    with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                        result = client.get_archived_rule(sample_rule.id)
                        return {
                            "result_not_none": result is not None,
                            "returns_most_recent": result["archived_at"] == "2024-01-02T12:00:00" if result else False
                        }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Restore Rule Raises If Exists")
    def restore_rule_raises_if_exists(self):
        """Test restore_rule raises ValueError if rule already exists."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                archive_file = tmp_path / f"{sample_rule.id}_20240101_120000.json"
                record = {"rule": asdict(sample_rule), "archived_at": "2024-01-01T12:00:00"}
                with open(archive_file, 'w') as f:
                    json.dump(record, f)

                with patch.object(TypeDBClient, 'connect', return_value=True):
                    client = TypeDBClient()
                    client._connected = True

                    with patch('governance.typedb.queries.rules.archive.ARCHIVE_DIR', tmp_path):
                        with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                            try:
                                client.restore_rule(sample_rule.id)
                                return {"raises_error": False}
                            except ValueError as e:
                                return {"raises_error": True, "error_mentions_exists": "already exists" in str(e)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Restore Rule Returns None If No Archive")
    def restore_rule_returns_none_if_no_archive(self):
        """Test restore_rule returns None if no archive exists."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, 'get_archived_rule', return_value=None):
                    result = client.restore_rule("RULE-NONEXISTENT")
                    return {"returns_none": result is None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # MCP Archive Tools Tests
    # =========================================================================

    @keyword("MCP List Archived Rules")
    def mcp_list_archived_rules(self):
        """Test rules_list_archived returns JSON array."""
        try:
            from governance.client import TypeDBClient

            mock_client = Mock(spec=TypeDBClient)
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

                return {
                    "has_archives": "archives" in data,
                    "count_correct": data.get("count") == 1,
                    "has_rule_id": data["archives"][0]["rule_id"] == "RULE-001" if data.get("archives") else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Get Archived Rule Success")
    def mcp_get_archived_rule_success(self):
        """Test rule_get_archived returns archive data."""
        try:
            from governance.client import TypeDBClient

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            mock_client = Mock(spec=TypeDBClient)
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

                return {
                    "has_rule": "rule" in data,
                    "id_matches": data["rule"]["id"] == sample_rule.id if "rule" in data else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Get Archived Rule Not Found")
    def mcp_get_archived_rule_not_found(self):
        """Test rule_get_archived returns error for missing archive."""
        try:
            from governance.client import TypeDBClient

            mock_client = Mock(spec=TypeDBClient)
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

                return {"has_error": "error" in data}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Restore Rule Success")
    def mcp_restore_rule_success(self):
        """Test rule_restore returns restored rule."""
        try:
            from governance.client import TypeDBClient, Rule

            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            restored_rule = Rule(
                id=sample_rule.id,
                name=sample_rule.name,
                category=sample_rule.category,
                priority=sample_rule.priority,
                status="DRAFT",
                directive=sample_rule.directive
            )

            mock_client = Mock(spec=TypeDBClient)
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

                return {
                    "success": data.get("success", False),
                    "status_draft": data.get("rule", {}).get("status") == "DRAFT"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCP Restore Rule Not Found")
    def mcp_restore_rule_not_found(self):
        """Test rule_restore returns error for missing archive."""
        try:
            from governance.client import TypeDBClient

            mock_client = Mock(spec=TypeDBClient)
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

                return {"has_error": "error" in data}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
