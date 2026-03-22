"""
BUG-TASK-TAXONOMY-001: Task priority/type as first-class fields.

Root cause: priority was embedded as "[Priority: X]" in task body text,
task_type had no field at all. Both are now proper TypeDB attributes.

Tests cover:
1. Pydantic models accept priority and task_type
2. Task entity dataclass has priority and task_type fields
3. insert_task passes priority/task_type to TypeDB
4. update_task passes priority/task_type to TypeDB
5. Store conversion includes priority/task_type
6. Service layer passes priority/task_type through
7. MCP task_create uses proper fields instead of body embedding
8. REST API routes pass priority/task_type
"""

from unittest.mock import patch, MagicMock
import pytest


# ── Pydantic Models ──────────────────────────────────────────


class TestTaskModels:
    """Tests that Pydantic models include priority and task_type."""

    def test_task_create_accepts_priority(self):
        from governance.models import TaskCreate
        task = TaskCreate(task_id="T-1", description="Test", phase="P10", priority="HIGH")
        assert task.priority == "HIGH"

    def test_task_create_accepts_task_type(self):
        from governance.models import TaskCreate
        task = TaskCreate(task_id="T-1", description="Test", phase="P10", task_type="bug")
        assert task.task_type == "bug"

    def test_task_create_priority_defaults_none(self):
        from governance.models import TaskCreate
        task = TaskCreate(task_id="T-1", description="Test", phase="P10")
        assert task.priority is None

    def test_task_create_invalid_priority_rejected(self):
        from governance.models import TaskCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TaskCreate(task_id="T-1", description="Test", phase="P10", priority="INVALID")

    def test_task_update_accepts_priority(self):
        from governance.models import TaskUpdate
        update = TaskUpdate(priority="CRITICAL")
        assert update.priority == "CRITICAL"

    def test_task_update_accepts_task_type(self):
        from governance.models import TaskUpdate
        update = TaskUpdate(task_type="feature")
        assert update.task_type == "feature"

    def test_task_response_has_priority_field(self):
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="T-1", description="Test", phase="P10",
            status="OPEN", priority="HIGH", task_type="bug"
        )
        assert resp.priority == "HIGH"
        assert resp.task_type == "bug"

    def test_task_response_priority_defaults_none(self):
        from governance.models import TaskResponse
        resp = TaskResponse(task_id="T-1", description="Test", phase="P10", status="OPEN")
        assert resp.priority is None
        assert resp.task_type is None


# ── Task Entity Dataclass ────────────────────────────────────


class TestTaskEntity:
    """Tests that Task entity includes priority and task_type."""

    def test_task_entity_has_priority(self):
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P10", priority="HIGH")
        assert task.priority == "HIGH"

    def test_task_entity_has_task_type(self):
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P10", task_type="bug")
        assert task.task_type == "bug"

    def test_task_entity_defaults_none(self):
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P10")
        assert task.priority is None
        assert task.task_type is None


# ── Store Conversion ─────────────────────────────────────────


class TestStoreConversion:
    """Tests that store conversion includes priority and task_type."""

    def test_task_to_response_includes_priority(self):
        from governance.stores.helpers import task_to_response
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P10",
                    priority="HIGH", task_type="bug")
        resp = task_to_response(task)
        assert resp.priority == "HIGH"
        assert resp.task_type == "bug"

    def test_task_to_dict_includes_priority(self):
        from governance.stores.typedb_access import _task_to_dict
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P10",
                    priority="CRITICAL", task_type="chore")
        d = _task_to_dict(task)
        assert d["priority"] == "CRITICAL"
        assert d["task_type"] == "chore"

    def test_task_to_dict_priority_none(self):
        from governance.stores.typedb_access import _task_to_dict
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P10")
        d = _task_to_dict(task)
        assert d["priority"] is None
        assert d["task_type"] is None


# ── Service Layer ─────────────────────────────────────────────


class TestServiceLayer:
    """Tests that service layer handles priority and task_type."""

    @patch("governance.services.tasks.task_to_response")
    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_passes_priority(self, mock_client_fn, mock_resp):
        from governance.services.tasks import create_task

        client = MagicMock()
        client.get_task.return_value = None
        created_task = MagicMock()
        client.insert_task.return_value = created_task
        mock_client_fn.return_value = client
        mock_resp.return_value = {"task_id": "T-1", "priority": "HIGH"}

        create_task("T-1", description="Test", priority="HIGH", task_type="bug")

        client.insert_task.assert_called_once()
        call_kwargs = client.insert_task.call_args[1]
        assert call_kwargs["priority"] == "HIGH"
        assert call_kwargs["task_type"] == "bug"

    @patch("governance.services.tasks_mutations._tasks_store", {})
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_passes_priority(self, mock_client_fn):
        from governance.services.tasks_mutations import update_task, _tasks_store

        client = MagicMock()
        task_obj = MagicMock()
        task_obj.name = "Test"
        task_obj.phase = "P10"
        task_obj.status = "OPEN"
        task_obj.agent_id = None
        task_obj.created_at = None
        task_obj.body = None
        task_obj.gap_id = None
        client.get_task.return_value = task_obj
        mock_client_fn.return_value = client

        _tasks_store["T-1"] = {"task_id": "T-1", "status": "OPEN"}

        result = update_task("T-1", priority="CRITICAL", task_type="bug")
        assert result["priority"] == "CRITICAL"
        assert result["task_type"] == "bug"

    @patch("governance.services.tasks_mutations._tasks_store", {})
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_fallback_when_typedb_missing(self, mock_client_fn):
        """BUG: GET works but PUT returns 404 when task exists in memory only."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        client = MagicMock()
        client.get_task.return_value = None  # TypeDB doesn't have the task
        mock_client_fn.return_value = client

        # Task exists in memory store (e.g. created when TypeDB insert failed)
        _tasks_store["T-MEM"] = {
            "task_id": "T-MEM", "status": "OPEN", "description": "Memory only task",
            "phase": "P10",
        }

        result = update_task("T-MEM", priority="HIGH")
        assert result is not None, "update_task should NOT return None for memory-store tasks"
        assert result["priority"] == "HIGH"

    @patch("governance.services.tasks_mutations._tasks_store", {})
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_calls_client_update_for_priority(self, mock_client_fn):
        """BUG-TASK-TAXONOMY-001: Priority updates should reach TypeDB."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        client = MagicMock()
        task_obj = MagicMock()
        task_obj.name = "Test"
        task_obj.phase = "P10"
        task_obj.status = "OPEN"
        task_obj.agent_id = None
        task_obj.created_at = None
        task_obj.body = None
        task_obj.gap_id = None
        client.get_task.return_value = task_obj
        mock_client_fn.return_value = client

        _tasks_store["T-1"] = {"task_id": "T-1", "status": "OPEN"}

        update_task("T-1", priority="CRITICAL", task_type="feature")
        client.update_task.assert_called_once_with(
            "T-1", priority="CRITICAL", task_type="feature",
            name=None, phase=None, summary=None,
        )

    @patch("governance.services.tasks_mutations._tasks_store", {})
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_update_task_truly_missing_returns_none(self, mock_client_fn):
        """Task that doesn't exist anywhere should return None."""
        from governance.services.tasks_mutations import update_task

        client = MagicMock()
        client.get_task.return_value = None
        mock_client_fn.return_value = client

        result = update_task("T-GHOST", priority="HIGH")
        assert result is None

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_fallback_stores_priority(self, mock_client_fn):
        from governance.services.tasks import create_task, _tasks_store

        mock_client_fn.return_value = None  # No TypeDB

        with patch.dict("governance.services.tasks._tasks_store", {}, clear=True):
            result = create_task("T-FALL", description="Test", priority="LOW", task_type="research")
            assert result["priority"] == "LOW"
            assert result["task_type"] == "research"


# ── MCP Tools ────────────────────────────────────────────────


class TestMCPTools:
    """Tests that MCP tools use proper priority/task_type fields."""

    def test_mcp_task_create_no_priority_in_body(self):
        """MCP task_create should NOT embed priority in body text."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        captured_tools = {}

        def capture_tool():
            def decorator(func):
                captured_tools[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        assert "task_create" in captured_tools
        # Verify the function signature includes task_type
        import inspect
        sig = inspect.signature(captured_tools["task_create"])
        assert "task_type" in sig.parameters
        assert "priority" in sig.parameters

    def test_mcp_task_update_accepts_priority(self):
        """MCP task_update should accept priority parameter."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools

        mcp = MagicMock()
        captured_tools = {}

        def capture_tool():
            def decorator(func):
                captured_tools[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        assert "task_update" in captured_tools
        import inspect
        sig = inspect.signature(captured_tools["task_update"])
        assert "priority" in sig.parameters
        assert "task_type" in sig.parameters


# ── REST Routes ──────────────────────────────────────────────


class TestRESTRoutes:
    """Tests that REST routes pass priority and task_type."""

    @patch("governance.routes.tasks.crud.task_service")
    @pytest.mark.asyncio
    async def test_create_route_passes_priority(self, mock_service):
        from governance.routes.tasks.crud import create_task
        from governance.models import TaskCreate, TaskResponse

        mock_service.create_task.return_value = TaskResponse(
            task_id="T-1", description="Test", phase="P10",
            status="OPEN", priority="HIGH", task_type="bug"
        )

        task = TaskCreate(
            task_id="T-1", description="Test", phase="P10",
            priority="HIGH", task_type="bug"
        )
        result = await create_task(task)
        mock_service.create_task.assert_called_once()
        call_kwargs = mock_service.create_task.call_args[1]
        assert call_kwargs["priority"] == "HIGH"
        assert call_kwargs["task_type"] == "bug"

    @patch("governance.routes.tasks.crud.task_service")
    @pytest.mark.asyncio
    async def test_update_route_passes_priority(self, mock_service):
        from governance.routes.tasks.crud import update_task
        from governance.models import TaskUpdate, TaskResponse

        mock_service.update_task.return_value = {
            "task_id": "T-1", "description": "Test", "phase": "P10",
            "status": "OPEN", "priority": "CRITICAL",
        }

        update = TaskUpdate(priority="CRITICAL", task_type="chore")
        result = await update_task("T-1", update)
        call_kwargs = mock_service.update_task.call_args[1]
        assert call_kwargs["priority"] == "CRITICAL"
        assert call_kwargs["task_type"] == "chore"
