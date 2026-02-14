"""
META-TAXON-01-v1: Task taxonomy formalization and auto-ID generation.

Tests cover:
1. generate_task_id() returns correct prefix + sequence
2. generate_task_id() increments past existing IDs
3. TaskCreate accepts None task_id when task_type provided
4. TaskCreate rejects None task_id AND None task_type (at service level)
5. TaskCreate validates task_type Literal values
6. create_task() auto-generates ID when task_id=None
7. /api/taxonomy returns all expected fields
8. Backward compat: explicit task_id still works
9. MCP task_create with empty task_id uses service layer
10. Constants: TASK_TYPES, TASK_PRIORITIES, TASK_TYPE_PREFIX defined
"""

from unittest.mock import patch, MagicMock
import pytest


# ── Constants ──────────────────────────────────────────────


class TestTaxonomyConstants:
    """Tests that taxonomy constants are properly defined."""

    def test_task_types_defined(self):
        from agent.governance_ui.state.constants import TASK_TYPES
        assert isinstance(TASK_TYPES, list)
        assert 'bug' in TASK_TYPES
        assert 'feature' in TASK_TYPES
        assert 'chore' in TASK_TYPES
        assert 'research' in TASK_TYPES
        assert 'gap' in TASK_TYPES
        assert 'epic' in TASK_TYPES
        assert 'test' in TASK_TYPES

    def test_task_priorities_defined(self):
        from agent.governance_ui.state.constants import TASK_PRIORITIES
        assert isinstance(TASK_PRIORITIES, list)
        assert TASK_PRIORITIES == ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

    def test_task_type_prefix_defined(self):
        from agent.governance_ui.state.constants import TASK_TYPE_PREFIX
        assert isinstance(TASK_TYPE_PREFIX, dict)
        assert TASK_TYPE_PREFIX['bug'] == 'BUG'
        assert TASK_TYPE_PREFIX['feature'] == 'FEAT'
        assert TASK_TYPE_PREFIX['chore'] == 'CHORE'
        assert TASK_TYPE_PREFIX['research'] == 'RD'
        assert TASK_TYPE_PREFIX['gap'] == 'GAP'
        assert TASK_TYPE_PREFIX['epic'] == 'EPIC'
        assert TASK_TYPE_PREFIX['test'] == 'TEST'

    def test_all_task_types_have_prefix(self):
        from agent.governance_ui.state.constants import TASK_TYPES, TASK_TYPE_PREFIX
        for tt in TASK_TYPES:
            assert tt in TASK_TYPE_PREFIX, f"Task type '{tt}' missing from TASK_TYPE_PREFIX"


# ── ID Generation ──────────────────────────────────────────


class TestTaskIdGeneration:
    """Tests for generate_task_id()."""

    def test_generates_correct_prefix_bug(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            result = generate_task_id("bug")
        assert result.startswith("BUG-")
        assert result == "BUG-001"

    def test_generates_correct_prefix_feature(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            result = generate_task_id("feature")
        assert result == "FEAT-001"

    def test_generates_correct_prefix_research(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            result = generate_task_id("research")
        assert result == "RD-001"

    def test_increments_past_existing_memory(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        store = {"BUG-005": {}, "BUG-010": {}, "OTHER-001": {}}
        with patch.dict("governance.stores._tasks_store", store, clear=True):
            result = generate_task_id("bug")
        assert result == "BUG-011"

    def test_increments_past_existing_typedb(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        mock_client = MagicMock()
        task1 = MagicMock(spec=["id"])
        task1.id = "FEAT-003"
        task2 = MagicMock(spec=["id"])
        task2.id = "FEAT-007"
        mock_client.get_all_tasks.return_value = [task1, task2]
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            result = generate_task_id("feature", mock_client)
        assert result == "FEAT-008"

    def test_unknown_type_uses_task_prefix(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            result = generate_task_id("unknown_type")
        assert result.startswith("TASK-")

    def test_zero_padded_three_digits(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            result = generate_task_id("bug")
        assert result == "BUG-001"

    def test_counter_persists_across_calls(self):
        from governance.services.task_id_gen import generate_task_id, _counters
        _counters.clear()
        with patch.dict("governance.stores._tasks_store", {}, clear=True):
            r1 = generate_task_id("bug")
            r2 = generate_task_id("bug")
        assert r1 == "BUG-001"
        assert r2 == "BUG-002"


# ── Pydantic Model Updates ─────────────────────────────────


class TestPydanticModels:
    """Tests that Pydantic models support optional task_id and Literal task_type."""

    def test_task_create_accepts_none_task_id(self):
        from governance.models import TaskCreate
        task = TaskCreate(description="Test", phase="P10", task_type="bug")
        assert task.task_id is None
        assert task.task_type == "bug"

    def test_task_create_accepts_explicit_task_id(self):
        from governance.models import TaskCreate
        task = TaskCreate(task_id="MY-CUSTOM-001", description="Test", phase="P10")
        assert task.task_id == "MY-CUSTOM-001"

    def test_task_create_rejects_invalid_task_type(self):
        from governance.models import TaskCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TaskCreate(description="Test", phase="P10", task_type="invalid_type")

    def test_task_create_accepts_valid_task_types(self):
        from governance.models import TaskCreate
        for tt in ['bug', 'feature', 'chore', 'research', 'gap', 'epic', 'test']:
            task = TaskCreate(description="Test", phase="P10", task_type=tt)
            assert task.task_type == tt

    def test_task_update_rejects_invalid_task_type(self):
        from governance.models import TaskUpdate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TaskUpdate(task_type="not_a_real_type")

    def test_task_update_accepts_valid_task_type(self):
        from governance.models import TaskUpdate
        update = TaskUpdate(task_type="bug")
        assert update.task_type == "bug"


# ── Service Layer Auto-ID ───────────────────────────────────


class TestServiceAutoId:
    """Tests that create_task() auto-generates ID when task_id is None."""

    @patch("governance.services.tasks.task_to_response")
    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_auto_generates_id(self, mock_client_fn, mock_resp):
        from governance.services.tasks import create_task
        from governance.services.task_id_gen import _counters
        _counters.clear()

        mock_client_fn.return_value = None  # No TypeDB

        with patch.dict("governance.services.tasks._tasks_store", {}, clear=True):
            result = create_task(
                task_id=None, description="Auto test", task_type="bug", phase="P10"
            )
            assert result["task_id"].startswith("BUG-")

    @patch("governance.services.tasks.task_to_response")
    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_explicit_id_still_works(self, mock_client_fn, mock_resp):
        from governance.services.tasks import create_task

        mock_client_fn.return_value = None

        with patch.dict("governance.services.tasks._tasks_store", {}, clear=True):
            result = create_task(
                task_id="CUSTOM-001", description="Explicit ID", phase="P10"
            )
            assert result["task_id"] == "CUSTOM-001"

    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_no_id_no_type_raises(self, mock_client_fn):
        from governance.services.tasks import create_task

        mock_client_fn.return_value = None

        with pytest.raises(ValueError, match="Either task_id or task_type"):
            create_task(task_id=None, description="No ID", phase="P10")

    @patch("governance.services.tasks.task_to_response")
    @patch("governance.services.tasks.get_typedb_client")
    def test_create_task_empty_string_id_auto_generates(self, mock_client_fn, mock_resp):
        from governance.services.tasks import create_task
        from governance.services.task_id_gen import _counters
        _counters.clear()

        mock_client_fn.return_value = None

        with patch.dict("governance.services.tasks._tasks_store", {}, clear=True):
            result = create_task(
                task_id="", description="Empty ID test", task_type="feature", phase="P10"
            )
            assert result["task_id"].startswith("FEAT-")


# ── MCP Tool ────────────────────────────────────────────────


class TestMCPTaxonomyTool:
    """Tests that MCP taxonomy_get and task_create work correctly."""

    def test_mcp_taxonomy_get_registered(self):
        from governance.mcp_tools.tasks_crud import register_task_crud_tools
        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def decorator(func):
                captured[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)
        assert "taxonomy_get" in captured

    def test_mcp_taxonomy_get_returns_types(self):
        from governance.mcp_tools.tasks_crud import register_task_crud_tools
        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def decorator(func):
                captured[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        raw = captured["taxonomy_get"]()
        # format_mcp_result may return JSON or TOON format; check string contents
        assert "task_types" in raw
        assert "bug" in raw
        assert "BUG" in raw

    def test_mcp_task_create_optional_id(self):
        from governance.mcp_tools.tasks_crud import register_task_crud_tools
        import inspect

        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def decorator(func):
                captured[func.__name__] = func
                return func
            return decorator

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)

        sig = inspect.signature(captured["task_create"])
        # task_id should have a default (empty string = auto-generate)
        assert sig.parameters["task_id"].default == ""
        # name should be required (first positional)
        assert sig.parameters["name"].default is inspect.Parameter.empty


# ── REST Taxonomy Route ─────────────────────────────────────


class TestTaxonomyRoute:
    """Tests for /api/taxonomy endpoint."""

    @pytest.mark.asyncio
    async def test_taxonomy_endpoint_returns_all_fields(self):
        from governance.routes.taxonomy import get_taxonomy
        result = await get_taxonomy()
        assert "task_types" in result
        assert "task_priorities" in result
        assert "task_type_prefixes" in result
        assert "task_statuses" in result
        assert "task_phases" in result
        assert "rule_categories" in result
        assert "rule_priorities" in result
        assert "rule_statuses" in result

    @pytest.mark.asyncio
    async def test_taxonomy_types_match_constants(self):
        from governance.routes.taxonomy import get_taxonomy
        from agent.governance_ui.state.constants import TASK_TYPES
        result = await get_taxonomy()
        assert result["task_types"] == TASK_TYPES
