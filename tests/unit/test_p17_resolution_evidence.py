"""
P17: Issue Resolution Evidence Trail — Unit Tests.

Per EPIC-TASK-QUALITY-V3 Phase 17.
Tests: resolution_notes field, auto-populate on DONE, UI visibility, collator.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ============================================================================
# 1. resolution_notes in Task Models
# ============================================================================

class TestResolutionNotesInModels:
    """Test resolution_notes field exists and works in Pydantic models."""

    def test_task_response_has_resolution_notes(self):
        """TaskResponse includes resolution_notes field."""
        from governance.models.task import TaskResponse
        resp = TaskResponse(
            task_id="T-1",
            description="Test",
            phase="P17",
            status="DONE",
            resolution_notes="## Root cause\nRace condition in flush",
        )
        assert resp.resolution_notes == "## Root cause\nRace condition in flush"

    def test_task_response_resolution_notes_default_none(self):
        """TaskResponse.resolution_notes defaults to None."""
        from governance.models.task import TaskResponse
        resp = TaskResponse(
            task_id="T-1",
            description="Test",
            phase="P17",
            status="TODO",
        )
        assert resp.resolution_notes is None

    def test_task_update_has_resolution_notes(self):
        """TaskUpdate includes resolution_notes field."""
        from governance.models.task import TaskUpdate
        update = TaskUpdate(resolution_notes="Fixed by adding null check")
        assert update.resolution_notes == "Fixed by adding null check"

    def test_task_update_resolution_notes_default_none(self):
        """TaskUpdate.resolution_notes defaults to None."""
        from governance.models.task import TaskUpdate
        update = TaskUpdate()
        assert update.resolution_notes is None


# ============================================================================
# 2. resolution_notes in TypeDB Entity
# ============================================================================

class TestResolutionNotesInEntity:
    """Test resolution_notes field on TypeDB Task dataclass."""

    def test_task_entity_has_resolution_notes(self):
        """Task entity includes resolution_notes field."""
        from governance.typedb.entities import Task
        task = Task(
            id="T-1", name="Test", status="DONE", phase="P17",
            resolution_notes="Root cause identified",
        )
        assert task.resolution_notes == "Root cause identified"

    def test_task_entity_resolution_notes_default_none(self):
        """Task entity resolution_notes defaults to None."""
        from governance.typedb.entities import Task
        task = Task(id="T-1", name="Test", status="TODO", phase="P17")
        assert task.resolution_notes is None


# ============================================================================
# 3. task_to_response includes resolution_notes
# ============================================================================

class TestTaskToResponse:
    """Test that helpers.task_to_response includes resolution_notes."""

    def test_task_to_response_includes_resolution_notes(self):
        """task_to_response maps resolution_notes from entity to response."""
        from governance.stores.helpers import task_to_response
        from governance.typedb.entities import Task

        task = Task(
            id="T-1", name="Test task", status="DONE", phase="P17",
            resolution_notes="## Summary\nFixed race condition",
        )
        response = task_to_response(task)
        assert response.resolution_notes == "## Summary\nFixed race condition"

    def test_task_to_response_resolution_notes_none(self):
        """task_to_response handles None resolution_notes gracefully."""
        from governance.stores.helpers import task_to_response
        from governance.typedb.entities import Task

        task = Task(id="T-1", name="Test", status="TODO", phase="P17")
        response = task_to_response(task)
        assert response.resolution_notes is None


# ============================================================================
# 4. Resolution Collator
# ============================================================================

class TestResolutionCollator:
    """Test resolution summary auto-generation."""

    def test_build_resolution_summary_with_sessions(self):
        """Summary includes session descriptions."""
        from governance.services.resolution_collator import build_resolution_summary

        task_data = {
            "linked_sessions": ["SESSION-2026-03-24-P17"],
            "linked_documents": ["docs/EPIC-ISSUE-EVIDENCE-RD.md"],
            "linked_commits": ["abc1234"],
            "evidence": "[Verification: L1] All tests pass",
        }
        session_meta = [
            {
                "session_id": "SESSION-2026-03-24-P17",
                "description": "Resolution evidence trail",
                "duration": "45m",
            }
        ]
        result = build_resolution_summary(task_data, session_meta)

        assert "## Resolution Summary" in result
        assert "SESSION-2026-03-24-P17" in result
        assert "Resolution evidence trail" in result
        assert "45m" in result
        assert "docs/EPIC-ISSUE-EVIDENCE-RD.md" in result
        assert "abc1234" in result
        assert "[Verification: L1]" in result

    def test_build_resolution_summary_no_sessions(self):
        """Summary is minimal when no linked data exists."""
        from governance.services.resolution_collator import build_resolution_summary

        task_data = {}
        result = build_resolution_summary(task_data)
        assert result == "Task completed."

    def test_build_resolution_summary_sessions_without_metadata(self):
        """Summary lists session IDs when no metadata available."""
        from governance.services.resolution_collator import build_resolution_summary

        task_data = {"linked_sessions": ["SESSION-X"]}
        result = build_resolution_summary(task_data, session_metadata=None)
        assert "SESSION-X" in result
        assert "### Sessions" in result

    def test_build_resolution_summary_only_evidence(self):
        """Summary with only evidence field."""
        from governance.services.resolution_collator import build_resolution_summary

        task_data = {"evidence": "Manual verification completed"}
        result = build_resolution_summary(task_data)
        assert "### Evidence" in result
        assert "Manual verification completed" in result

    def test_build_resolution_summary_documents_only(self):
        """Summary with only linked documents."""
        from governance.services.resolution_collator import build_resolution_summary

        task_data = {"linked_documents": ["file1.py", "file2.py"]}
        result = build_resolution_summary(task_data)
        assert "### Linked Documents" in result
        assert "file1.py" in result
        assert "file2.py" in result

    def test_fetch_session_metadata_from_store(self):
        """fetch_session_metadata reads from _sessions_store."""
        from governance.services.resolution_collator import fetch_session_metadata
        from governance.stores import _sessions_store

        _sessions_store["S-TEST-META"] = {
            "description": "Meta test",
            "duration": "5m",
            "agent_id": "test-agent",
        }
        try:
            result = fetch_session_metadata(["S-TEST-META", "S-MISSING"])
            assert len(result) == 2
            assert result[0]["description"] == "Meta test"
            assert result[0]["duration"] == "5m"
            assert result[1] == {"session_id": "S-MISSING"}
        finally:
            _sessions_store.pop("S-TEST-META", None)


# ============================================================================
# 5. Auto-populate on DONE transition
# ============================================================================

class TestAutoPopulateOnDone:
    """Test that DONE transition auto-populates resolution_notes."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_auto_populate_on_done_transition(self, mock_get_client):
        """Transitioning to DONE auto-populates resolution_notes when empty."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Set up task entity
        mock_task = MagicMock()
        mock_task.id = "T-AUTO-DONE"
        mock_task.name = "Test auto-done"
        mock_task.status = "IN_PROGRESS"
        mock_task.phase = "P17"
        mock_task.agent_id = "code-agent"
        mock_task.resolution = "NONE"
        mock_task.body = None
        mock_task.gap_id = None
        mock_task.priority = "HIGH"
        mock_task.task_type = "bug"
        mock_task.evidence = "Tests pass"
        mock_task.summary = "Fix race condition"
        mock_task.created_at = datetime(2026, 3, 24, 10, 0)
        mock_task.claimed_at = datetime(2026, 3, 24, 10, 5)
        mock_task.completed_at = None
        mock_task.document_path = None
        mock_task.workspace_id = None
        mock_task.linked_rules = []
        mock_task.linked_sessions = ["SESSION-P17"]
        mock_task.linked_commits = []
        mock_task.linked_documents = ["docs/RD.md"]
        mock_task.resolution_notes = None
        mock_client.get_task.return_value = mock_task
        mock_client.update_task_status.return_value = mock_task

        # Pre-populate store for DONE gate
        _tasks_store["T-AUTO-DONE"] = {
            "task_id": "T-AUTO-DONE",
            "description": "Test auto-done",
            "phase": "P17",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "Fix race condition",
            "created_at": "2026-03-24T10:00:00",
            "claimed_at": "2026-03-24T10:05:00",
            "completed_at": None,
            "body": None,
            "gap_id": None,
            "priority": "HIGH",
            "task_type": "bug",
            "evidence": "Tests pass",
            "resolution": "NONE",
            "document_path": None,
            "linked_rules": [],
            "linked_sessions": ["SESSION-P17"],
            "linked_commits": [],
            "linked_documents": ["docs/RD.md"],
            "workspace_id": None,
            "resolution_notes": None,
        }

        try:
            result = update_task(
                "T-AUTO-DONE",
                status="DONE",
            )
            assert result is not None
            # Resolution notes should be auto-populated
            rn = result.get("resolution_notes", "")
            assert rn is not None
            assert len(rn) > 0
            assert "## Resolution Summary" in rn
        finally:
            _tasks_store.pop("T-AUTO-DONE", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_no_auto_populate_when_resolution_notes_provided(self, mock_get_client):
        """DONE transition with explicit resolution_notes does NOT auto-populate."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_task = MagicMock()
        mock_task.id = "T-NO-AUTO"
        mock_task.name = "No auto"
        mock_task.status = "IN_PROGRESS"
        mock_task.phase = "P17"
        mock_task.agent_id = "code-agent"
        mock_task.resolution = "NONE"
        mock_task.body = None
        mock_task.gap_id = None
        mock_task.priority = None
        mock_task.task_type = None
        mock_task.evidence = None
        mock_task.summary = "Test"
        mock_task.created_at = datetime(2026, 3, 24)
        mock_task.claimed_at = datetime(2026, 3, 24)
        mock_task.completed_at = None
        mock_task.document_path = None
        mock_task.workspace_id = None
        mock_task.linked_rules = []
        mock_task.linked_sessions = ["S-1"]
        mock_task.linked_commits = []
        mock_task.linked_documents = ["doc.md"]
        mock_task.resolution_notes = None
        mock_client.get_task.return_value = mock_task
        mock_client.update_task_status.return_value = mock_task

        _tasks_store["T-NO-AUTO"] = {
            "task_id": "T-NO-AUTO",
            "description": "No auto",
            "phase": "P17",
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
            "summary": "Test",
            "created_at": "2026-03-24T10:00:00",
            "claimed_at": "2026-03-24T10:00:00",
            "completed_at": None,
            "body": None,
            "gap_id": None,
            "priority": None,
            "task_type": None,
            "evidence": None,
            "resolution": "NONE",
            "document_path": None,
            "linked_rules": [],
            "linked_sessions": ["S-1"],
            "linked_commits": [],
            "linked_documents": ["doc.md"],
            "workspace_id": None,
            "resolution_notes": None,
        }

        try:
            result = update_task(
                "T-NO-AUTO",
                status="DONE",
                resolution_notes="Manually written resolution",
            )
            assert result is not None
            assert result["resolution_notes"] == "Manually written resolution"
        finally:
            _tasks_store.pop("T-NO-AUTO", None)


# ============================================================================
# 6. Resolution Section UI Visibility
# ============================================================================

class TestResolutionSectionUI:
    """Test resolution section component structure."""

    def test_resolution_module_imports(self):
        """resolution.py module can be imported."""
        from agent.governance_ui.views.tasks.resolution import (
            build_task_resolution_section,
        )
        assert callable(build_task_resolution_section)

    def test_detail_imports_resolution(self):
        """detail.py imports build_task_resolution_section."""
        from agent.governance_ui.views.tasks.detail import (
            build_task_resolution_section,
        )
        assert callable(build_task_resolution_section)


# ============================================================================
# 7. Edit Form includes resolution_notes
# ============================================================================

class TestEditFormResolutionNotes:
    """Test edit form wiring for resolution_notes."""

    def test_initial_state_has_edit_task_resolution_notes(self):
        """Initial state includes edit_task_resolution_notes."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "edit_task_resolution_notes" in state
        assert state["edit_task_resolution_notes"] == ""

    def test_forms_edit_module_imports(self):
        """forms_edit.py module can be imported without errors."""
        from agent.governance_ui.views.tasks.forms_edit import (
            build_task_edit_form,
        )
        assert callable(build_task_edit_form)


# ============================================================================
# 8. TypeDB Read Queries
# ============================================================================

class TestTypeDBReadQueries:
    """Test resolution_notes is read from TypeDB."""

    def test_batch_fetch_includes_resolution_notes(self):
        """_batch_fetch_task_attributes queries resolution-notes."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        import inspect

        source = inspect.getsource(TaskReadQueries._batch_fetch_task_attributes)
        assert "resolution-notes" in source
        assert "resolution_notes" in source

    def test_build_task_from_id_includes_resolution_notes(self):
        """_build_task_from_id fetches resolution-notes attribute."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        import inspect

        source = inspect.getsource(TaskReadQueries._build_task_from_id)
        assert "resolution-notes" in source
        assert "resolution_notes" in source


# ============================================================================
# 9. TypeDB CRUD Write Operations
# ============================================================================

class TestTypeDBCrudWriteOps:
    """Test resolution_notes is written via TypeDB CRUD."""

    def test_insert_task_accepts_resolution_notes(self):
        """insert_task function signature includes resolution_notes."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        import inspect

        sig = inspect.signature(TaskCRUDOperations.insert_task)
        assert "resolution_notes" in sig.parameters

    def test_update_task_accepts_resolution_notes(self):
        """update_task function signature includes resolution_notes."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        import inspect

        sig = inspect.signature(TaskCRUDOperations.update_task)
        assert "resolution_notes" in sig.parameters

    def test_resolution_notes_in_allowed_attr_names(self):
        """resolution-notes is in the CRUD attribute allowlist."""
        from governance.typedb.queries.tasks.crud import _ALLOWED_TASK_ATTR_NAMES
        assert "resolution-notes" in _ALLOWED_TASK_ATTR_NAMES


# ============================================================================
# 10. Service Layer
# ============================================================================

class TestServiceLayerResolutionNotes:
    """Test resolution_notes flows through the service layer."""

    def test_update_task_signature_has_resolution_notes(self):
        """update_task in tasks_mutations.py accepts resolution_notes."""
        from governance.services.tasks_mutations import update_task
        import inspect

        sig = inspect.signature(update_task)
        assert "resolution_notes" in sig.parameters

    def test_mcp_task_update_signature_has_resolution_notes(self):
        """MCP task_update tool accepts resolution_notes."""
        from governance.mcp_tools.tasks_crud import register_task_crud_tools
        import inspect

        # We need to check the decorated function — inspect the source
        source = inspect.getsource(register_task_crud_tools)
        assert "resolution_notes" in source


# ============================================================================
# 11. REST Routes
# ============================================================================

class TestRestRoutesResolutionNotes:
    """Test resolution_notes flows through REST routes."""

    def test_task_update_model_has_resolution_notes(self):
        """TaskUpdate model used by PUT /tasks/{id} includes resolution_notes."""
        from governance.models.task import TaskUpdate
        update = TaskUpdate(resolution_notes="Test notes")
        assert update.resolution_notes == "Test notes"

    def test_task_update_route_passes_resolution_notes(self):
        """PUT /tasks/{id} route passes resolution_notes to service."""
        from governance.routes.tasks.crud import update_task
        import inspect

        source = inspect.getsource(update_task)
        assert "resolution_notes" in source


# ============================================================================
# 12. Controller Wiring
# ============================================================================

class TestControllerWiring:
    """Test UI controller sends resolution_notes on edit submit."""

    def test_submit_task_edit_sends_resolution_notes(self):
        """submit_task_edit includes resolution_notes in update payload."""
        from agent.governance_ui.controllers.tasks_crud import register_tasks_crud
        import inspect

        source = inspect.getsource(register_tasks_crud)
        assert "resolution_notes" in source
        assert "edit_task_resolution_notes" in source
