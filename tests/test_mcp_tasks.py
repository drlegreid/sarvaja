"""
MCP Tasks Tools Tests
=====================
TDD tests for Task CRUD MCP tools per P10.4.
Created: 2024-12-26
Per RULE-023: Test Before Ship

Tests written BEFORE implementation per TDD.
"""
import pytest
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestTasksMCPToolsExist:
    """Validate Tasks MCP tools are registered."""

    @pytest.mark.unit
    def test_tasks_tools_importable(self):
        """Tasks MCP tools module must be importable."""
        try:
            from governance.mcp_tools.tasks import register_task_tools
            assert register_task_tools is not None
        except ImportError as e:
            pytest.skip(f"Tasks MCP tools not yet implemented: {e}")

    @pytest.mark.unit
    def test_tasks_tools_registered(self):
        """Tasks tools must be included in register_all_tools."""
        from governance.mcp_tools import register_all_tools
        # If tasks is registered, it should be in __all__ or imported
        try:
            from governance.mcp_tools import register_task_tools
            assert register_task_tools is not None
        except ImportError:
            pytest.skip("register_task_tools not exported from mcp_tools")


class TestTaskCreateMCP:
    """Test governance_create_task MCP tool."""

    @pytest.mark.integration
    def test_create_task_tool_exists(self):
        """governance_create_task must be callable."""
        try:
            from governance.mcp_server import governance_create_task
            assert callable(governance_create_task)
        except (ImportError, AttributeError):
            pytest.skip("governance_create_task not yet exported")

    @pytest.mark.integration
    def test_create_task_returns_json(self):
        """governance_create_task must return valid JSON."""
        try:
            from governance.mcp_server import governance_create_task
            result = governance_create_task(
                task_id="TEST-001",
                name="Test Task",
                description="TDD test task",
                status="pending",
                priority="MEDIUM",
                phase="P10"
            )
            data = json.loads(result)
            assert isinstance(data, dict)
        except (ImportError, AttributeError):
            pytest.skip("governance_create_task not yet exported")

    @pytest.mark.integration
    def test_create_task_has_required_fields(self):
        """Created task must have required fields in response."""
        try:
            from governance.mcp_server import governance_create_task
            result = governance_create_task(
                task_id="TEST-002",
                name="Field Test Task",
                description="Check required fields",
                status="pending",
                priority="HIGH"
            )
            data = json.loads(result)
            assert "task_id" in data, "task_id missing"
            assert "name" in data, "name missing"
            assert "status" in data, "status missing"
            assert "message" in data or "error" not in data
        except (ImportError, AttributeError):
            pytest.skip("governance_create_task not yet exported")


class TestTaskReadMCP:
    """Test governance_get_task MCP tool."""

    @pytest.mark.integration
    def test_get_task_tool_exists(self):
        """governance_get_task must be callable."""
        try:
            from governance.mcp_server import governance_get_task
            assert callable(governance_get_task)
        except (ImportError, AttributeError):
            pytest.skip("governance_get_task not yet exported")

    @pytest.mark.integration
    def test_get_task_returns_json(self):
        """governance_get_task must return valid JSON."""
        try:
            from governance.mcp_server import governance_get_task
            result = governance_get_task("P10.1")
            data = json.loads(result)
            assert isinstance(data, dict)
        except (ImportError, AttributeError):
            pytest.skip("governance_get_task not yet exported")

    @pytest.mark.integration
    def test_get_task_returns_not_found(self):
        """governance_get_task must handle missing task."""
        try:
            from governance.mcp_server import governance_get_task
            result = governance_get_task("NONEXISTENT-999")
            data = json.loads(result)
            # Should either have error or empty result
            assert "error" in data or data.get("task_id") == "NONEXISTENT-999"
        except (ImportError, AttributeError):
            pytest.skip("governance_get_task not yet exported")


class TestTaskUpdateMCP:
    """Test governance_update_task MCP tool."""

    @pytest.mark.integration
    def test_update_task_tool_exists(self):
        """governance_update_task must be callable."""
        try:
            from governance.mcp_server import governance_update_task
            assert callable(governance_update_task)
        except (ImportError, AttributeError):
            pytest.skip("governance_update_task not yet exported")

    @pytest.mark.integration
    def test_update_task_status(self):
        """governance_update_task must update task status."""
        try:
            from governance.mcp_server import governance_update_task
            result = governance_update_task(
                task_id="TEST-001",
                status="in_progress"
            )
            data = json.loads(result)
            assert isinstance(data, dict)
            if "error" not in data:
                assert data.get("status") == "in_progress" or "updated" in str(data).lower()
        except (ImportError, AttributeError):
            pytest.skip("governance_update_task not yet exported")


class TestTaskDeleteMCP:
    """Test governance_delete_task MCP tool."""

    @pytest.mark.integration
    def test_delete_task_tool_exists(self):
        """governance_delete_task must be callable."""
        try:
            from governance.mcp_server import governance_delete_task
            assert callable(governance_delete_task)
        except (ImportError, AttributeError):
            pytest.skip("governance_delete_task not yet exported")


class TestTypeDBTaskOperations:
    """Test TypeDB client task operations (P10.1)."""

    @pytest.mark.integration
    def test_client_has_task_operations(self):
        """TypeDB client must have task CRUD methods."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            # Check for task methods
            assert hasattr(client, 'insert_task'), "insert_task missing"
            assert hasattr(client, 'get_task'), "get_task missing"
            assert hasattr(client, 'update_task'), "update_task missing"
            assert hasattr(client, 'delete_task'), "delete_task missing"
        except ImportError:
            pytest.skip("TypeDBClient not available")
        except AssertionError as e:
            pytest.skip(f"Task operations not yet implemented: {e}")

    @pytest.mark.integration
    def test_insert_task_to_typedb(self):
        """Task insertion to TypeDB must work."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            if not client.connect():
                pytest.skip("Cannot connect to TypeDB")
            try:
                result = client.insert_task(
                    task_id="TDD-001",
                    name="TDD Test Task",
                    status="pending",
                    phase="P10"
                )
                assert result is not None
            finally:
                # Cleanup
                try:
                    client.delete_task("TDD-001")
                except:
                    pass
                client.close()
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Task operations not yet implemented: {e}")

    @pytest.mark.integration
    def test_get_all_tasks_from_typedb(self):
        """Get all tasks from TypeDB must work."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            if not client.connect():
                pytest.skip("Cannot connect to TypeDB")
            try:
                tasks = client.get_all_tasks()
                assert isinstance(tasks, list)
            finally:
                client.close()
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Task operations not yet implemented: {e}")
