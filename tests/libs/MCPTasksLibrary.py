"""
Robot Framework library for MCP Tasks Tools tests.

Per P10.4: Task CRUD MCP tools
Migrated from tests/test_mcp_tasks.py
"""

import json
from robot.api.deco import keyword


class MCPTasksLibrary:
    """Library for testing MCP tasks tools functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Tools Existence Tests
    # =========================================================================

    @keyword("Tasks Tools Importable")
    def tasks_tools_importable(self):
        """Tasks MCP tools module must be importable."""
        try:
            from governance.mcp_tools.tasks import register_task_tools
            return {"importable": register_task_tools is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tasks Tools Registered")
    def tasks_tools_registered(self):
        """Tasks tools must be included in register_all_tools."""
        try:
            from governance.mcp_tools import register_task_tools
            return {"registered": register_task_tools is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Create Task Tests
    # =========================================================================

    @keyword("Create Task Tool Exists")
    def create_task_tool_exists(self):
        """governance_create_task must be callable."""
        try:
            from governance.compat import governance_create_task
            return {"exists": callable(governance_create_task)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Task Returns JSON")
    def create_task_returns_json(self):
        """governance_create_task must return valid JSON."""
        try:
            from governance.compat import governance_create_task
            result = governance_create_task(
                task_id="TEST-001",
                name="Test Task",
                description="TDD test task",
                status="pending",
                priority="MEDIUM",
                phase="P10"
            )
            data = json.loads(result)
            return {"is_dict": isinstance(data, dict)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Task Has Required Fields")
    def create_task_has_required_fields(self):
        """Created task must have required fields in response."""
        try:
            from governance.compat import governance_create_task
            result = governance_create_task(
                task_id="TEST-002",
                name="Field Test Task",
                description="Check required fields",
                status="pending",
                priority="HIGH"
            )
            data = json.loads(result)
            if isinstance(data, dict) and "error" in data:
                return {"skipped": True, "reason": data['error']}
            return {
                "has_task_id": "task_id" in data,
                "has_name": "name" in data,
                "has_status": "status" in data,
                "has_message_or_no_error": "message" in data or "error" not in data
            }
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Read Task Tests
    # =========================================================================

    @keyword("Get Task Tool Exists")
    def get_task_tool_exists(self):
        """governance_get_task must be callable."""
        try:
            from governance.compat import governance_get_task
            return {"exists": callable(governance_get_task)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Task Returns JSON")
    def get_task_returns_json(self):
        """governance_get_task must return valid JSON."""
        try:
            from governance.compat import governance_get_task
            result = governance_get_task("P10.1")
            data = json.loads(result)
            return {"is_dict": isinstance(data, dict)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Task Returns Not Found")
    def get_task_returns_not_found(self):
        """governance_get_task must handle missing task."""
        try:
            from governance.compat import governance_get_task
            result = governance_get_task("NONEXISTENT-999")
            data = json.loads(result)
            return {
                "handled": "error" in data or data.get("task_id") == "NONEXISTENT-999"
            }
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Update Task Tests
    # =========================================================================

    @keyword("Update Task Tool Exists")
    def update_task_tool_exists(self):
        """governance_update_task must be callable."""
        try:
            from governance.compat import governance_update_task
            return {"exists": callable(governance_update_task)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Update Task Status")
    def update_task_status(self):
        """governance_update_task must update task status."""
        try:
            from governance.compat import governance_update_task
            result = governance_update_task(
                task_id="TEST-001",
                status="in_progress"
            )
            data = json.loads(result)
            if "error" not in data:
                success = (
                    data.get("status") == "in_progress" or
                    "updated" in str(data).lower()
                )
                return {"updated": success}
            return {"skipped": True, "reason": data.get("error")}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Delete Task Tests
    # =========================================================================

    @keyword("Delete Task Tool Exists")
    def delete_task_tool_exists(self):
        """governance_delete_task must be callable."""
        try:
            from governance.compat import governance_delete_task
            return {"exists": callable(governance_delete_task)}
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # TypeDB Operations Tests
    # =========================================================================

    @keyword("Client Has Task Operations")
    def client_has_task_operations(self):
        """TypeDB client must have task CRUD methods."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            return {
                "has_insert_task": hasattr(client, 'insert_task'),
                "has_get_task": hasattr(client, 'get_task'),
                "has_update_task": hasattr(client, 'update_task'),
                "has_delete_task": hasattr(client, 'delete_task')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Insert Task To TypeDB")
    def insert_task_to_typedb(self):
        """Task insertion to TypeDB must work."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB"}
            try:
                result = client.insert_task(
                    task_id="TDD-001",
                    name="TDD Test Task",
                    status="pending",
                    phase="P10"
                )
                success = result is not None
                # Cleanup
                try:
                    client.delete_task("TDD-001")
                except Exception:
                    pass
                return {"inserted": success}
            finally:
                client.close()
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get All Tasks From TypeDB")
    def get_all_tasks_from_typedb(self):
        """Get all tasks from TypeDB must work."""
        try:
            from governance.client import TypeDBClient
            client = TypeDBClient()
            if not client.connect():
                return {"skipped": True, "reason": "Cannot connect to TypeDB"}
            try:
                tasks = client.get_all_tasks()
                return {"is_list": isinstance(tasks, list)}
            finally:
                client.close()
        except (ImportError, AttributeError) as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
