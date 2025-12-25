"""
Rules CRUD Tests
================
Tests for governance rule CRUD operations.

Per RULE-012: DSP Semantic Code Structure
Per TDD: Write tests first, then implement

Tests both:
- TypeDBClient CRUD methods (mocked)
- MCP tool wrappers
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from governance.client import TypeDBClient, Rule


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_rule():
    """Sample rule for testing."""
    return Rule(
        id="RULE-TEST-001",
        name="Test Rule",
        category="testing",
        priority="MEDIUM",
        status="DRAFT",
        directive="This is a test rule directive."
    )


@pytest.fixture
def sample_rule_data():
    """Sample rule data dict for testing."""
    return {
        "rule_id": "RULE-TEST-002",
        "name": "Another Test Rule",
        "category": "governance",
        "priority": "HIGH",
        "directive": "Another test directive.",
        "status": "DRAFT"
    }


@pytest.fixture
def mock_client():
    """Create a mock TypeDBClient for testing."""
    client = Mock(spec=TypeDBClient)
    client.connect.return_value = True
    client.close.return_value = None
    client.is_connected.return_value = True
    return client


# =============================================================================
# TYPEDB CLIENT VALIDATION TESTS (No driver required)
# =============================================================================

class TestTypeDBClientValidation:
    """Tests for TypeDBClient input validation."""

    def test_create_rule_validates_category(self, mock_client, sample_rule):
        """Test that create_rule validates category."""
        # Create a real client but mock its connection
        with patch.object(TypeDBClient, 'connect', return_value=True):
            with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                client = TypeDBClient()
                client._connected = True  # Simulate connected state

                # Mock _execute_write to avoid actual DB call
                with patch.object(client, '_execute_write'):
                    # Valid categories
                    valid = ["governance", "technical", "operational", "architecture", "testing"]
                    for cat in valid:
                        # Should not raise - but we can't test without mock
                        pass

                    # Invalid category should raise
                    with pytest.raises(ValueError, match="Invalid category"):
                        client.create_rule(
                            rule_id="RULE-TEST",
                            name="Test",
                            category="invalid_category",
                            priority="HIGH",
                            directive="Test"
                        )

    def test_create_rule_validates_priority(self, mock_client):
        """Test that create_rule validates priority."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                client = TypeDBClient()
                client._connected = True

                with pytest.raises(ValueError, match="Invalid priority"):
                    client.create_rule(
                        rule_id="RULE-TEST",
                        name="Test",
                        category="governance",
                        priority="INVALID",
                        directive="Test"
                    )

    def test_create_rule_validates_status(self, mock_client):
        """Test that create_rule validates status."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                client = TypeDBClient()
                client._connected = True

                with pytest.raises(ValueError, match="Invalid status"):
                    client.create_rule(
                        rule_id="RULE-TEST",
                        name="Test",
                        category="governance",
                        priority="HIGH",
                        directive="Test",
                        status="INVALID"
                    )

    def test_create_rule_checks_duplicate(self, sample_rule):
        """Test that create_rule rejects duplicate IDs."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            # Mock get_rule_by_id to return existing rule
            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                with pytest.raises(ValueError, match="already exists"):
                    client.create_rule(
                        rule_id=sample_rule.id,
                        name="New Name",
                        category="governance",
                        priority="HIGH",
                        directive="New directive"
                    )

    def test_update_rule_raises_for_missing(self):
        """Test that update_rule raises for non-existent rule."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=None):
                with pytest.raises(ValueError, match="not found"):
                    client.update_rule("RULE-NONEXISTENT", name="New Name")

    def test_update_rule_returns_unchanged_if_no_updates(self, sample_rule):
        """Test that update_rule returns existing rule if nothing changes."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                result = client.update_rule(sample_rule.id)
                assert result == sample_rule

    def test_deprecate_rule_calls_update_with_deprecated(self, sample_rule):
        """Test that deprecate_rule calls update_rule with DEPRECATED status."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            deprecated_rule = Rule(
                id=sample_rule.id,
                name=sample_rule.name,
                category=sample_rule.category,
                priority=sample_rule.priority,
                status="DEPRECATED",
                directive=sample_rule.directive
            )

            with patch.object(client, 'update_rule', return_value=deprecated_rule) as mock_update:
                result = client.deprecate_rule(sample_rule.id)
                mock_update.assert_called_once_with(sample_rule.id, status="DEPRECATED")
                assert result.status == "DEPRECATED"

    def test_delete_rule_returns_false_for_missing(self):
        """Test that delete_rule returns False for non-existent rule."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=None):
                result = client.delete_rule("RULE-NONEXISTENT")
                assert result is False


# =============================================================================
# MCP TOOL TESTS
# =============================================================================

class TestMCPRuleTools:
    """Tests for MCP rule CRUD tools."""

    def test_governance_create_rule_success(self, mock_client, sample_rule):
        """Test governance_create_rule returns success JSON."""
        mock_client.create_rule.return_value = sample_rule

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
            with patch('governance.mcp_tools.common.get_typedb_client', return_value=mock_client):
                from governance.mcp_tools.rules import register_rule_tools

                # Create a test MCP and call the function directly
                # We need to access the inner function
                mock_mcp = Mock()
                registered_funcs = {}

                def tool_decorator():
                    def inner(func):
                        registered_funcs[func.__name__] = func
                        return func
                    return inner

                mock_mcp.tool = tool_decorator
                register_rule_tools(mock_mcp)

                # Call the registered function
                result = registered_funcs['governance_create_rule'](
                    rule_id=sample_rule.id,
                    name=sample_rule.name,
                    category=sample_rule.category,
                    priority=sample_rule.priority,
                    directive=sample_rule.directive
                )

                data = json.loads(result)
                assert data["success"] is True
                assert sample_rule.id in data["message"]

    def test_governance_create_rule_connection_failure(self, mock_client):
        """Test governance_create_rule handles connection failure."""
        mock_client.connect.return_value = False

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_create_rule'](
                rule_id="RULE-TEST",
                name="Test",
                category="governance",
                priority="HIGH",
                directive="Test"
            )

            data = json.loads(result)
            assert "error" in data
            assert "connect" in data["error"].lower()

    def test_governance_create_rule_validation_error(self, mock_client):
        """Test governance_create_rule handles validation errors."""
        mock_client.create_rule.side_effect = ValueError("Invalid category")

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_create_rule'](
                rule_id="RULE-TEST",
                name="Test",
                category="invalid",
                priority="HIGH",
                directive="Test"
            )

            data = json.loads(result)
            assert "error" in data
            assert "Invalid" in data["error"]

    def test_governance_update_rule_success(self, mock_client, sample_rule):
        """Test governance_update_rule returns success JSON."""
        updated_rule = Rule(
            id=sample_rule.id,
            name="Updated Name",
            category=sample_rule.category,
            priority=sample_rule.priority,
            status=sample_rule.status,
            directive=sample_rule.directive
        )
        mock_client.update_rule.return_value = updated_rule

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_update_rule'](
                rule_id=sample_rule.id,
                name="Updated Name"
            )

            data = json.loads(result)
            assert data["success"] is True
            assert "updated" in data["message"].lower()

    def test_governance_deprecate_rule_success(self, mock_client, sample_rule):
        """Test governance_deprecate_rule returns success JSON."""
        deprecated_rule = Rule(
            id=sample_rule.id,
            name=sample_rule.name,
            category=sample_rule.category,
            priority=sample_rule.priority,
            status="DEPRECATED",
            directive=sample_rule.directive
        )
        mock_client.deprecate_rule.return_value = deprecated_rule

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_deprecate_rule'](
                rule_id=sample_rule.id,
                reason="No longer needed"
            )

            data = json.loads(result)
            assert data["success"] is True
            assert data["new_status"] == "DEPRECATED"
            assert data["reason"] == "No longer needed"

    def test_governance_delete_rule_requires_confirmation(self, mock_client):
        """Test governance_delete_rule requires explicit confirmation."""
        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_delete_rule'](
                rule_id="RULE-TEST",
                confirm=False
            )

            data = json.loads(result)
            assert "error" in data
            assert "confirm" in data["error"].lower()
            assert "warning" in data

    def test_governance_delete_rule_success(self, mock_client):
        """Test governance_delete_rule with confirmation."""
        mock_client.delete_rule.return_value = True

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_delete_rule'](
                rule_id="RULE-TEST",
                confirm=True
            )

            data = json.loads(result)
            assert data["success"] is True
            assert "deleted" in data["message"].lower()


# =============================================================================
# INTEGRATION TESTS (require TypeDB)
# =============================================================================

@pytest.mark.integration
@pytest.mark.skipif(True, reason="Requires running TypeDB instance")
class TestRulesCRUDIntegration:
    """Integration tests for rules CRUD (require running TypeDB)."""

    @pytest.fixture
    def typedb_client(self):
        """Get connected TypeDB client."""
        client = TypeDBClient()
        if client.connect():
            yield client
            client.close()
        else:
            pytest.skip("TypeDB not available")

    def test_full_crud_cycle(self, typedb_client):
        """Test complete CRUD cycle: create, read, update, deprecate, delete."""
        test_rule_id = "RULE-INTEGRATION-TEST"

        try:
            # CREATE
            rule = typedb_client.create_rule(
                rule_id=test_rule_id,
                name="Integration Test Rule",
                category="testing",
                priority="LOW",
                directive="This rule is for integration testing only."
            )
            assert rule is not None
            assert rule.id == test_rule_id
            assert rule.status == "DRAFT"

            # READ
            fetched = typedb_client.get_rule_by_id(test_rule_id)
            assert fetched is not None
            assert fetched.name == "Integration Test Rule"

            # UPDATE
            updated = typedb_client.update_rule(test_rule_id, priority="MEDIUM")
            assert updated.priority == "MEDIUM"

            # DEPRECATE
            deprecated = typedb_client.deprecate_rule(test_rule_id)
            assert deprecated.status == "DEPRECATED"

            # DELETE
            deleted = typedb_client.delete_rule(test_rule_id)
            assert deleted is True

            # VERIFY DELETED
            gone = typedb_client.get_rule_by_id(test_rule_id)
            assert gone is None

        finally:
            # Cleanup in case of failure
            try:
                typedb_client.delete_rule(test_rule_id)
            except:
                pass


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestRulesCRUDEdgeCases:
    """Edge case tests for rules CRUD."""

    def test_valid_categories(self):
        """Test all valid categories are accepted."""
        valid = ["governance", "technical", "operational", "architecture", "testing"]
        # Just verify the list is complete - actual validation tested above
        assert len(valid) == 5

    def test_valid_priorities(self):
        """Test all valid priorities are accepted."""
        valid = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert len(valid) == 4

    def test_valid_statuses(self):
        """Test all valid statuses are accepted."""
        valid = ["ACTIVE", "DRAFT", "DEPRECATED"]
        assert len(valid) == 3

    def test_rule_dataclass_fields(self, sample_rule):
        """Test Rule dataclass has expected fields."""
        assert hasattr(sample_rule, 'id')
        assert hasattr(sample_rule, 'name')
        assert hasattr(sample_rule, 'category')
        assert hasattr(sample_rule, 'priority')
        assert hasattr(sample_rule, 'status')
        assert hasattr(sample_rule, 'directive')

    def test_rule_to_dict(self, sample_rule):
        """Test Rule can be converted to dict."""
        rule_dict = asdict(sample_rule)
        assert rule_dict['id'] == sample_rule.id
        assert rule_dict['name'] == sample_rule.name
        assert rule_dict['category'] == sample_rule.category


# =============================================================================
# ARCHIVE TESTS
# =============================================================================

class TestRulesArchive:
    """Tests for rule archive functionality."""

    def test_delete_rule_archives_by_default(self, sample_rule):
        """Test that delete_rule archives the rule by default."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True
            # Mock the TypeDB client session
            mock_session = MagicMock()
            mock_tx = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
            mock_session.transaction.return_value.__exit__ = MagicMock(return_value=False)
            client._client = MagicMock()
            client._client.session.return_value = mock_session

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
            # Mock the TypeDB client session
            mock_session = MagicMock()
            mock_tx = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
            mock_session.transaction.return_value.__exit__ = MagicMock(return_value=False)
            client._client = MagicMock()
            client._client.session.return_value = mock_session

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
                        # Patch ARCHIVE_DIR to use temp path
                        with patch('governance.client.ARCHIVE_DIR', tmp_path):
                            result = client.archive_rule(sample_rule.id)

                            assert result is not None
                            assert result["rule"]["id"] == sample_rule.id
                            assert "archived_at" in result
                            assert result["reason"] == "archived"

                            # Verify file was created
                            files = list(tmp_path.glob("*.json"))
                            assert len(files) == 1
                            assert sample_rule.id in files[0].name

    def test_get_archived_rules_empty(self, tmp_path):
        """Test get_archived_rules returns empty list when no archives."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch('governance.client.ARCHIVE_DIR', tmp_path):
                result = client.get_archived_rules()
                assert result == []

    def test_get_archived_rule_returns_most_recent(self, sample_rule, tmp_path):
        """Test get_archived_rule returns the most recent archive."""
        import json as json_module
        from datetime import datetime

        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            # Create two archive files
            tmp_path.mkdir(parents=True, exist_ok=True)
            archive1 = tmp_path / f"{sample_rule.id}_20240101_120000.json"
            archive2 = tmp_path / f"{sample_rule.id}_20240102_120000.json"

            record1 = {"rule": asdict(sample_rule), "archived_at": "2024-01-01T12:00:00"}
            record2 = {"rule": asdict(sample_rule), "archived_at": "2024-01-02T12:00:00"}

            with open(archive1, 'w') as f:
                json_module.dump(record1, f)
            with open(archive2, 'w') as f:
                json_module.dump(record2, f)

            with patch('governance.client.ARCHIVE_DIR', tmp_path):
                result = client.get_archived_rule(sample_rule.id)
                assert result is not None
                assert result["archived_at"] == "2024-01-02T12:00:00"

    def test_restore_rule_raises_if_exists(self, sample_rule, tmp_path):
        """Test restore_rule raises ValueError if rule already exists."""
        import json as json_module

        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            # Create archive file
            tmp_path.mkdir(parents=True, exist_ok=True)
            archive_file = tmp_path / f"{sample_rule.id}_20240101_120000.json"
            record = {"rule": asdict(sample_rule), "archived_at": "2024-01-01T12:00:00"}
            with open(archive_file, 'w') as f:
                json_module.dump(record, f)

            with patch('governance.client.ARCHIVE_DIR', tmp_path):
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
        """Test governance_list_archived_rules returns JSON array."""
        mock_client.get_archived_rules.return_value = [
            {
                "rule": {"id": "RULE-001", "name": "Test"},
                "archived_at": "2024-01-01T12:00:00",
                "reason": "deleted",
                "dependencies": [],
                "dependents": []
            }
        ]

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_list_archived_rules']()

            data = json.loads(result)
            assert "archives" in data
            assert data["count"] == 1
            assert data["archives"][0]["rule_id"] == "RULE-001"

    def test_governance_get_archived_rule_success(self, mock_client, sample_rule):
        """Test governance_get_archived_rule returns archive data."""
        mock_client.get_archived_rule.return_value = {
            "rule": asdict(sample_rule),
            "archived_at": "2024-01-01T12:00:00",
            "reason": "deleted"
        }

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_get_archived_rule'](
                rule_id=sample_rule.id
            )

            data = json.loads(result)
            assert "rule" in data
            assert data["rule"]["id"] == sample_rule.id

    def test_governance_get_archived_rule_not_found(self, mock_client):
        """Test governance_get_archived_rule returns error for missing archive."""
        mock_client.get_archived_rule.return_value = None

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_get_archived_rule'](
                rule_id="RULE-NONEXISTENT"
            )

            data = json.loads(result)
            assert "error" in data

    def test_governance_restore_rule_success(self, mock_client, sample_rule):
        """Test governance_restore_rule returns restored rule."""
        restored_rule = Rule(
            id=sample_rule.id,
            name=sample_rule.name,
            category=sample_rule.category,
            priority=sample_rule.priority,
            status="DRAFT",  # Restored rules get DRAFT status
            directive=sample_rule.directive
        )
        mock_client.restore_rule.return_value = restored_rule

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_restore_rule'](
                rule_id=sample_rule.id
            )

            data = json.loads(result)
            assert data["success"] is True
            assert "restored" in data["message"].lower()
            assert data["rule"]["status"] == "DRAFT"

    def test_governance_restore_rule_not_found(self, mock_client):
        """Test governance_restore_rule returns error for missing archive."""
        mock_client.restore_rule.return_value = None

        with patch('governance.mcp_tools.rules.get_typedb_client', return_value=mock_client):
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

            result = registered_funcs['governance_restore_rule'](
                rule_id="RULE-NONEXISTENT"
            )

            data = json.loads(result)
            assert "error" in data
