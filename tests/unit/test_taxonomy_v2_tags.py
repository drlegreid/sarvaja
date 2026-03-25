"""Unit tests for EPIC-TASK-TAXONOMY-V2 orthogonal tag dimensions.

Tests layer/concern/method fields through:
- Dataclass construction
- Pydantic model validation
- task_to_response conversion
- TypeDB CRUD allowlist
- Fallback store round-trip
"""
import pytest
from unittest.mock import patch, MagicMock

from governance.typedb.entities import Task
from governance.models.task import TaskCreate, TaskUpdate, TaskResponse
from agent.governance_ui.state.constants import TASK_LAYERS, TASK_CONCERNS, TASK_METHODS


class TestTagConstants:
    """Verify tag dimension constants are correctly defined."""

    def test_layers_has_expected_values(self):
        expected = {"ui", "api", "data", "infra", "schema", "monitoring", "ci-cd"}
        assert set(TASK_LAYERS) == expected

    def test_concerns_has_expected_values(self):
        expected = {"security", "performance", "reliability", "usability",
                    "data-integrity", "compliance"}
        assert set(TASK_CONCERNS) == expected

    def test_methods_has_expected_values(self):
        expected = {"spike", "exploratory", "automated", "ai-generated",
                    "gherkin", "manual", "draft"}
        assert set(TASK_METHODS) == expected


class TestTaskDataclass:
    """Test Task dataclass with new tag fields."""

    def test_default_none(self):
        task = Task(id="T-1", name="test", status="TODO", phase="P10")
        assert task.layer is None
        assert task.concern is None
        assert task.method is None

    def test_set_all_tags(self):
        task = Task(
            id="T-2", name="test", status="TODO", phase="P10",
            layer="api", concern="security", method="automated",
        )
        assert task.layer == "api"
        assert task.concern == "security"
        assert task.method == "automated"

    def test_tags_independent_of_type(self):
        """Tags are orthogonal — any type can have any tag."""
        task = Task(
            id="T-3", name="test", status="TODO", phase="P10",
            task_type="bug", layer="ui", concern="usability", method="manual",
        )
        assert task.task_type == "bug"
        assert task.layer == "ui"
        assert task.concern == "usability"
        assert task.method == "manual"


class TestPydanticModels:
    """Test Pydantic models accept and pass through tag fields."""

    def test_task_create_with_tags(self):
        tc = TaskCreate(
            description="Fix API bug",
            phase="P10",
            layer="api",
            concern="reliability",
            method="spike",
        )
        assert tc.layer == "api"
        assert tc.concern == "reliability"
        assert tc.method == "spike"

    def test_task_create_tags_optional(self):
        tc = TaskCreate(description="Simple task", phase="P10")
        assert tc.layer is None
        assert tc.concern is None
        assert tc.method is None

    def test_task_update_with_tags(self):
        tu = TaskUpdate(layer="data", concern="performance")
        assert tu.layer == "data"
        assert tu.concern == "performance"
        assert tu.method is None

    def test_task_response_with_tags(self):
        tr = TaskResponse(
            task_id="BUG-001",
            description="Test",
            phase="P10",
            status="TODO",
            layer="infra",
            concern="security",
            method="automated",
        )
        assert tr.layer == "infra"
        assert tr.concern == "security"
        assert tr.method == "automated"

    def test_task_response_tags_optional(self):
        tr = TaskResponse(
            task_id="BUG-002",
            description="Test",
            phase="P10",
            status="TODO",
        )
        assert tr.layer is None
        assert tr.concern is None
        assert tr.method is None


class TestTaskToResponse:
    """Test task_to_response includes tag fields."""

    def test_tags_in_response(self):
        from governance.stores.helpers import task_to_response

        task = Task(
            id="BUG-010", name="Test bug", status="TODO", phase="P10",
            layer="api", concern="security", method="spike",
        )
        resp = task_to_response(task)
        assert resp.layer == "api"
        assert resp.concern == "security"
        assert resp.method == "spike"

    def test_none_tags_in_response(self):
        from governance.stores.helpers import task_to_response

        task = Task(id="BUG-011", name="Test", status="TODO", phase="P10")
        resp = task_to_response(task)
        assert resp.layer is None
        assert resp.concern is None
        assert resp.method is None


class TestTypeDBCRUDAllowlist:
    """Test that new attributes are in the TypeDB allowlist."""

    def test_task_layer_in_allowlist(self):
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert "task-layer" in _ALLOWED_TASK_ATTR_NAMES

    def test_task_concern_in_allowlist(self):
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert "task-concern" in _ALLOWED_TASK_ATTR_NAMES

    def test_task_method_in_allowlist(self):
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert "task-method" in _ALLOWED_TASK_ATTR_NAMES


class TestInsertTaskSignature:
    """Test insert_task accepts new tag parameters."""

    def test_insert_task_has_tag_params(self):
        import inspect
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        sig = inspect.signature(TaskCRUDOperations.insert_task)
        params = sig.parameters
        assert "layer" in params
        assert "concern" in params
        assert "method" in params

    def test_update_task_has_tag_params(self):
        import inspect
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        sig = inspect.signature(TaskCRUDOperations.update_task)
        params = sig.parameters
        assert "layer" in params
        assert "concern" in params
        assert "method" in params


class TestFallbackStoreRoundTrip:
    """Test layer/concern/method survive fallback store round-trip."""

    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    @patch("governance.services.tasks._tasks_store", {})
    def test_create_stores_tags_in_fallback(
        self, mock_log, mock_mon, mock_audit, mock_session, mock_client
    ):
        from governance.services.tasks import create_task, _tasks_store

        result = create_task(
            task_id="TAG-001",
            description="Test with tags",
            task_type="bug",
            phase="P10",
            layer="api",
            concern="security",
            method="spike",
        )

        assert "TAG-001" in _tasks_store
        assert _tasks_store["TAG-001"]["layer"] == "api"
        assert _tasks_store["TAG-001"]["concern"] == "security"
        assert _tasks_store["TAG-001"]["method"] == "spike"

    @patch("governance.services.tasks_mutations.get_typedb_client", return_value=None)
    @patch("governance.services.tasks_mutations._tasks_store", {
        "TAG-002": {"task_id": "TAG-002", "description": "test", "status": "TODO",
                    "phase": "P10", "linked_sessions": [],
                    "layer": None, "concern": None, "method": None}
    })
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.log_event")
    def test_update_stores_tags_in_fallback(
        self, mock_log, mock_mon, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task
        from governance.services.tasks_mutations import _tasks_store

        update_task("TAG-002", layer="data", concern="performance", method="automated")

        assert _tasks_store["TAG-002"]["layer"] == "data"
        assert _tasks_store["TAG-002"]["concern"] == "performance"
        assert _tasks_store["TAG-002"]["method"] == "automated"


class TestBackwardCompatibility:
    """Verify canonical types accepted, deprecated types rejected (EPIC-TASK-TAXONOMY-V2)."""

    def test_canonical_types_accepted_in_create(self):
        """All 6 canonical task_type values pass Pydantic validation."""
        canonical = ["bug", "feature", "chore", "research", "spec", "test"]
        for t in canonical:
            tc = TaskCreate(description=f"Test {t}", phase="P10", task_type=t)
            assert tc.task_type == t

    def test_deprecated_types_rejected_in_create(self):
        """Deprecated types (gap, epic, specification) are rejected by Pydantic."""
        from pydantic import ValidationError
        for t in ["gap", "epic", "specification"]:
            with pytest.raises(ValidationError):
                TaskCreate(description=f"Test {t}", phase="P10", task_type=t)

    def test_canonical_types_accepted_in_update(self):
        """All 6 canonical task_type values pass Pydantic validation."""
        canonical = ["bug", "feature", "chore", "research", "spec", "test"]
        for t in canonical:
            tu = TaskUpdate(task_type=t)
            assert tu.task_type == t

    def test_deprecated_types_rejected_in_update(self):
        """Deprecated types (gap, epic, specification) are rejected by Pydantic."""
        from pydantic import ValidationError
        for t in ["gap", "epic", "specification"]:
            with pytest.raises(ValidationError):
                TaskUpdate(task_type=t)
