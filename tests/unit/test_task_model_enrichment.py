"""TDD Tests for EPIC-GOV-TASKS-V2 Phase 9c: Task Model Enrichment + UX Defaults.

5 concerns:
1. "specification" task type
2. summary field (separate from description)
3. TASK-HANDOVER-01-v1 rule
4. Default sort created_at DESC + whitelist
5. Priority field cleanup ([Priority: X] extraction)

Per TEST-GUARD-01: Tests written FIRST, implementation follows.
"""
import re
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ============================================================================
# Concern 1: "specification" task type
# ============================================================================

class TestSpecificationTaskType:
    """BDD: Add 'specification' to task type taxonomy."""

    def test_task_types_includes_specification(self):
        """Scenario: specification is a valid task type."""
        from agent.governance_ui.state.constants import TASK_TYPES
        assert "specification" in TASK_TYPES

    def test_task_type_prefix_has_spec(self):
        """Scenario: specification maps to SPEC prefix for auto-ID."""
        from agent.governance_ui.state.constants import TASK_TYPE_PREFIX
        assert TASK_TYPE_PREFIX["specification"] == "SPEC"

    def test_pydantic_task_create_accepts_specification(self):
        """Scenario: TaskCreate model validates specification type."""
        from governance.models import TaskCreate
        task = TaskCreate(
            description="Auth spec", phase="P9c",
            task_type="specification"
        )
        assert task.task_type == "specification"

    def test_pydantic_task_update_accepts_specification(self):
        """Scenario: TaskUpdate model validates specification type."""
        from governance.models import TaskUpdate
        update = TaskUpdate(task_type="specification")
        assert update.task_type == "specification"

    def test_initial_state_type_options_includes_specification(self):
        """Scenario: Dashboard type filter includes specification."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "specification" in state["task_type_options"]

    def test_mcp_task_create_docstring_includes_specification(self):
        """Scenario: MCP task_create docstring lists specification as valid type."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools
        mcp = MagicMock()
        captured = {}

        def capture_tool():
            def wrapper(fn):
                captured[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = capture_tool
        register_task_crud_tools(mcp)
        assert "specification" in captured["task_create"].__doc__


# ============================================================================
# Concern 2: summary field (separate from description)
# ============================================================================

class TestSummaryField:
    """BDD: Add summary field to task model, auto-generate if missing."""

    def test_task_response_has_summary_field(self):
        """Scenario: TaskResponse includes summary field."""
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="TEST-001", description="Full details",
            phase="P9c", status="OPEN", summary="tasks > add summary"
        )
        assert resp.summary == "tasks > add summary"

    def test_task_response_summary_defaults_none(self):
        """Scenario: summary defaults to None if not provided."""
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="TEST-001", description="Full details",
            phase="P9c", status="OPEN"
        )
        assert resp.summary is None

    def test_task_create_has_summary_field(self):
        """Scenario: TaskCreate accepts optional summary."""
        from governance.models import TaskCreate
        task = TaskCreate(
            description="Full details", phase="P9c",
            summary="tasks > add summary"
        )
        assert task.summary == "tasks > add summary"

    def test_task_update_has_summary_field(self):
        """Scenario: TaskUpdate accepts optional summary."""
        from governance.models import TaskUpdate
        update = TaskUpdate(summary="updated summary")
        assert update.summary == "updated summary"

    def test_task_entity_has_summary_field(self):
        """Scenario: TypeDB Task entity has summary attribute."""
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P9c",
                    summary="test > summary")
        assert task.summary == "test > summary"

    def test_task_entity_summary_defaults_none(self):
        """Scenario: Task entity summary defaults to None."""
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P9c")
        assert task.summary is None

    def test_task_to_response_includes_summary(self):
        """Scenario: task_to_response converts summary from Task entity."""
        from governance.stores.helpers import task_to_response
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P9c",
                    summary="test > action")
        resp = task_to_response(task)
        # task_to_response returns a Pydantic model
        assert getattr(resp, "summary", None) == "test > action"

    def test_task_to_dict_includes_summary(self):
        """Scenario: _task_to_dict includes summary in output dict."""
        from governance.stores.typedb_access import _task_to_dict
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="OPEN", phase="P9c",
                    summary="test > action")
        d = _task_to_dict(task)
        assert d["summary"] == "test > action"

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks.get_all_tasks_from_typedb")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    def test_create_task_auto_generates_summary(
        self, mock_log, mock_mon, mock_audit, mock_sid, mock_get_all, mock_client
    ):
        """Scenario: Auto-generate summary from description if not provided."""
        mock_client.return_value = None  # Force fallback path
        from governance.services.tasks import create_task
        result = create_task(
            task_id="TEST-AUTO-SUM",
            description="Add specification task type to all layers",
            phase="P9c",
        )
        # Summary should be auto-generated (truncated/formatted description)
        assert result.get("summary") is not None
        assert len(result["summary"]) <= 80

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks.get_all_tasks_from_typedb")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    def test_create_task_preserves_explicit_summary(
        self, mock_log, mock_mon, mock_audit, mock_sid, mock_get_all, mock_client
    ):
        """Scenario: Explicit summary is preserved, not overwritten."""
        mock_client.return_value = None
        from governance.services.tasks import create_task
        result = create_task(
            task_id="TEST-EXPL-SUM",
            description="Add specification task type to all layers",
            phase="P9c",
            summary="tasks/types > add specification",
        )
        assert result["summary"] == "tasks/types > add specification"

    def test_insert_task_accepts_summary(self):
        """Scenario: TypeDB insert_task includes summary parameter."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        import inspect
        sig = inspect.signature(TypeCRUDOperations_insert_task := TaskCRUDOperations.insert_task)
        assert "summary" in sig.parameters

    def test_batch_fetch_includes_summary(self):
        """Scenario: Batch fetch queries include task-summary attribute."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        import inspect
        source = inspect.getsource(TaskReadQueries._batch_fetch_task_attributes)
        assert "task-summary" in source

    def test_update_task_attr_allowlist_includes_summary(self):
        """Scenario: _ALLOWED_TASK_ATTR_NAMES includes task-summary."""
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert "task-summary" in _ALLOWED_TASK_ATTR_NAMES

    def test_dashboard_headers_show_summary_column(self):
        """Scenario: Dashboard tasks table has Summary column."""
        import inspect
        from agent.governance_ui.views.tasks.list import build_tasks_list_view
        source = inspect.getsource(build_tasks_list_view)
        assert '"Summary"' in source
        assert '"summary"' in source


# ============================================================================
# Concern 3: TASK-HANDOVER-01-v1 rule
# ============================================================================

class TestTaskHandoverRule:
    """BDD: Create TASK-HANDOVER-01-v1 rule document."""

    def test_rule_document_exists(self):
        """Scenario: Rule document file exists."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "docs", "rules", "leaf", "TASK-HANDOVER-01-v1.md"
        )
        assert os.path.exists(path), f"Rule doc missing: {path}"

    def test_rule_document_has_required_sections(self):
        """Scenario: Rule document has ID, category, priority, directive."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "docs", "rules", "leaf", "TASK-HANDOVER-01-v1.md"
        )
        content = open(path).read()
        assert "TASK-HANDOVER-01-v1" in content
        assert "Directive" in content or "directive" in content
        assert "task" in content.lower() and "id" in content.lower()


# ============================================================================
# Concern 4: Default sort + whitelist
# ============================================================================

class TestDefaultSortAndFilters:
    """BDD: Default sort created_at DESC, add to whitelist."""

    def test_api_default_sort_is_created_at(self):
        """Scenario: API list tasks defaults to sort_by=created_at."""
        import inspect
        from governance.routes.tasks.crud import list_tasks
        sig = inspect.signature(list_tasks)
        assert sig.parameters["sort_by"].default.default == "created_at"

    def test_api_default_order_is_desc(self):
        """Scenario: API list tasks defaults to order=desc."""
        import inspect
        from governance.routes.tasks.crud import list_tasks
        sig = inspect.signature(list_tasks)
        assert sig.parameters["order"].default.default == "desc"

    def test_created_at_in_sort_whitelist(self):
        """Scenario: created_at is in the valid sort whitelist."""
        import inspect
        source = inspect.getsource(
            __import__("governance.routes.tasks.crud", fromlist=["list_tasks"]).list_tasks
        )
        assert "created_at" in source

    def test_service_sort_field_supports_created_at(self):
        """Scenario: Service layer sort recognizes created_at."""
        import inspect
        from governance.services.tasks import list_tasks
        source = inspect.getsource(list_tasks)
        assert "created_at" in source


# ============================================================================
# Concern 5: Priority field cleanup
# ============================================================================

class TestPriorityFieldCleanup:
    """BDD: Parse [Priority: X] from description, extract to priority field."""

    def test_extract_priority_tag_from_description(self):
        """Scenario: [Priority: HIGH] in description is extracted."""
        from governance.services.tasks import _extract_priority_tag
        desc = "Fix login bug [Priority: HIGH] immediately"
        new_desc, priority = _extract_priority_tag(desc)
        assert priority == "HIGH"
        assert "[Priority:" not in new_desc
        assert "Fix login bug" in new_desc

    def test_extract_priority_tag_case_insensitive(self):
        """Scenario: [priority: medium] works case-insensitively."""
        from governance.services.tasks import _extract_priority_tag
        desc = "[priority: medium] Update docs"
        new_desc, priority = _extract_priority_tag(desc)
        assert priority == "MEDIUM"
        assert "[priority:" not in new_desc.lower()

    def test_extract_priority_tag_no_match(self):
        """Scenario: Description without priority tag returns None."""
        from governance.services.tasks import _extract_priority_tag
        desc = "Normal task description"
        new_desc, priority = _extract_priority_tag(desc)
        assert priority is None
        assert new_desc == "Normal task description"

    def test_extract_priority_tag_invalid_value(self):
        """Scenario: [Priority: URGENT] is invalid, not extracted."""
        from governance.services.tasks import _extract_priority_tag
        desc = "[Priority: URGENT] Fix now"
        new_desc, priority = _extract_priority_tag(desc)
        assert priority is None  # URGENT is not a valid priority

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    def test_create_task_extracts_priority_from_description(
        self, mock_log, mock_mon, mock_audit, mock_sid, mock_client
    ):
        """Scenario: create_task auto-extracts [Priority: X] from description."""
        mock_client.return_value = None  # Fallback path
        from governance.services.tasks import create_task
        result = create_task(
            task_id="TEST-PRI-EXT",
            description="[Priority: CRITICAL] Fix authentication bypass",
            phase="P9c",
        )
        assert result["priority"] == "CRITICAL"
        assert "[Priority:" not in result["description"]

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    def test_create_task_explicit_priority_overrides_tag(
        self, mock_log, mock_mon, mock_audit, mock_sid, mock_client
    ):
        """Scenario: Explicit priority param overrides [Priority: X] tag."""
        mock_client.return_value = None
        from governance.services.tasks import create_task
        result = create_task(
            task_id="TEST-PRI-OVER",
            description="[Priority: LOW] Something",
            phase="P9c",
            priority="HIGH",  # Explicit takes precedence
        )
        assert result["priority"] == "HIGH"

    def test_remediation_script_exists(self):
        """Scenario: Migration script for priority cleanup exists."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "scripts", "remediate_task_data.py"
        )
        assert os.path.exists(path)

    def test_remediation_script_has_dry_run(self):
        """Scenario: Migration script supports --dry-run flag."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "scripts", "remediate_task_data.py"
        )
        content = open(path).read()
        assert "dry_run" in content or "dry-run" in content


# ============================================================================
# Concern 2+5 combined: auto-generate summary with priority extraction
# ============================================================================

class TestAutoSummaryGeneration:
    """BDD: _generate_summary produces structured summaries."""

    def test_generate_summary_basic(self):
        """Scenario: Simple description gets truncated summary."""
        from governance.services.tasks import _generate_summary
        summary = _generate_summary("Add specification task type to all layers")
        assert len(summary) <= 80
        assert summary  # Not empty

    def test_generate_summary_long_description(self):
        """Scenario: Long description is truncated to 80 chars."""
        from governance.services.tasks import _generate_summary
        desc = "A" * 200
        summary = _generate_summary(desc)
        assert len(summary) <= 80

    def test_generate_summary_strips_priority_tag(self):
        """Scenario: [Priority: X] tags are stripped from summary."""
        from governance.services.tasks import _generate_summary
        summary = _generate_summary("[Priority: HIGH] Fix login bug")
        assert "[Priority:" not in summary

    def test_generate_summary_empty_description(self):
        """Scenario: Empty description returns empty summary."""
        from governance.services.tasks import _generate_summary
        summary = _generate_summary("")
        assert summary == ""
