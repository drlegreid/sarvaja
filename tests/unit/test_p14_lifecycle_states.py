"""
Tests for P14: DONE Gate Preload + Task Lifecycle States.

BUG-1: DONE gate preload doesn't fetch linked_documents from TypeDB
BUG-2: Status vocabulary mismatch — CANCELED missing
BUG-3: DELETE is destructive with no soft-cancel

Per TEST-FIX-01-v1: TDD — failing tests FIRST, then implement.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime


# ---- BUG-2: TaskStatus Enum — Single Source of Truth ----

class TestTaskStatusEnum:
    """TaskStatus enum is the canonical source for all status values."""

    def test_all_six_values_exist(self):
        """Enum must have OPEN, TODO, IN_PROGRESS, BLOCKED, DONE, CANCELED (CLOSED removed Session 4)."""
        from governance.task_lifecycle import TaskStatus
        expected = {"OPEN", "TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELED"}
        actual = {s.value for s in TaskStatus}
        assert actual == expected

    def test_canceled_is_a_member(self):
        """P14: CANCELED must exist as a valid TaskStatus."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.CANCELED.value == "CANCELED"

    def test_str_enum_comparison(self):
        """TaskStatus members compare equal to their string values."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.CANCELED == "CANCELED"
        assert TaskStatus.DONE == "DONE"

    def test_valid_values_returns_all(self):
        """valid_values() returns set of all status strings."""
        from governance.task_lifecycle import TaskStatus
        vals = TaskStatus.valid_values()
        assert "CANCELED" in vals
        assert "BLOCKED" in vals
        assert len(vals) == 6

    def test_ui_edit_values_excludes_closed(self):
        """ui_edit_values() returns dropdown list without CLOSED/OPEN."""
        from governance.task_lifecycle import TaskStatus
        ui = TaskStatus.ui_edit_values()
        assert ui == ["TODO", "IN_PROGRESS", "DONE", "BLOCKED", "CANCELED"]
        assert "CLOSED" not in ui
        assert "OPEN" not in ui

    def test_terminal_states(self):
        """terminal_states() includes DONE, CANCELED (CLOSED removed Session 4)."""
        from governance.task_lifecycle import TaskStatus
        terminal = TaskStatus.terminal_states()
        assert TaskStatus.DONE in terminal
        assert TaskStatus.CANCELED in terminal
        assert TaskStatus.IN_PROGRESS not in terminal

    def test_is_terminal_property(self):
        """is_terminal property works on enum members."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.CANCELED.is_terminal is True
        assert TaskStatus.DONE.is_terminal is True
        assert TaskStatus.IN_PROGRESS.is_terminal is False
        assert TaskStatus.TODO.is_terminal is False


class TestTaskStatusTransitions:
    """P14: Status transitions include CANCELED paths."""

    def test_in_progress_to_canceled(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.CANCELED) is True

    def test_todo_to_canceled(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.TODO, TaskStatus.CANCELED) is True

    def test_open_to_canceled(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.OPEN, TaskStatus.CANCELED) is True

    def test_blocked_to_canceled(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.BLOCKED, TaskStatus.CANCELED) is True

    def test_canceled_to_open(self):
        """Can re-activate a canceled task."""
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.OPEN) is True

    def test_canceled_to_todo(self):
        """Can move canceled task back to TODO."""
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.TODO) is True

    def test_canceled_to_done_invalid(self):
        """Cannot go from CANCELED directly to DONE."""
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.CANCELED, TaskStatus.DONE) is False

    def test_in_progress_to_done(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.DONE) is True

    def test_in_progress_to_blocked(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED) is True

    def test_todo_to_in_progress(self):
        from governance.task_lifecycle import TaskStatus, validate_status_transition
        assert validate_status_transition(TaskStatus.TODO, TaskStatus.IN_PROGRESS) is True


class TestTaskStatusResolutionCombo:
    """P14: CANCELED tasks must have resolution NONE."""

    def test_canceled_with_none_valid(self):
        from governance.task_lifecycle import (
            TaskStatus, TaskResolution, validate_status_resolution_combo,
        )
        valid, msg = validate_status_resolution_combo(TaskStatus.CANCELED, TaskResolution.NONE)
        assert valid is True

    def test_canceled_with_resolution_invalid(self):
        from governance.task_lifecycle import (
            TaskStatus, TaskResolution, validate_status_resolution_combo,
        )
        valid, msg = validate_status_resolution_combo(TaskStatus.CANCELED, TaskResolution.IMPLEMENTED)
        assert valid is False

    def test_blocked_with_none_valid(self):
        from governance.task_lifecycle import (
            TaskStatus, TaskResolution, validate_status_resolution_combo,
        )
        valid, msg = validate_status_resolution_combo(TaskStatus.BLOCKED, TaskResolution.NONE)
        assert valid is True

    def test_done_requires_resolution(self):
        from governance.task_lifecycle import (
            TaskStatus, TaskResolution, validate_status_resolution_combo,
        )
        valid, msg = validate_status_resolution_combo(TaskStatus.DONE, TaskResolution.NONE)
        assert valid is False


class TestTypeDBValidStatuses:
    """P14: TypeDB _VALID_STATUSES must include CANCELED."""

    def test_canceled_in_typedb_valid_statuses(self):
        """TypeDB status.py must accept CANCELED (CLOSED removed Session 4)."""
        from governance.task_lifecycle import TaskStatus
        typedb_expected = {"OPEN", "IN_PROGRESS", "DONE", "TODO", "BLOCKED", "CANCELED"}
        assert TaskStatus.valid_values() == typedb_expected


class TestStatusMigrationMap:
    """P14: Migration map updated for all canonical states."""

    def test_canceled_in_migration_map(self):
        from governance.task_lifecycle import STATUS_MIGRATION_MAP, TaskStatus
        assert STATUS_MIGRATION_MAP["CANCELED"] == TaskStatus.CANCELED

    def test_todo_maps_to_todo(self):
        """P14: TODO now maps to TODO (not OPEN)."""
        from governance.task_lifecycle import STATUS_MIGRATION_MAP, TaskStatus
        assert STATUS_MIGRATION_MAP["TODO"] == TaskStatus.TODO

    def test_done_maps_to_done(self):
        """P14: DONE now maps to DONE (not CLOSED)."""
        from governance.task_lifecycle import STATUS_MIGRATION_MAP, TaskStatus
        assert STATUS_MIGRATION_MAP["DONE"] == TaskStatus.DONE

    def test_blocked_maps_to_blocked(self):
        """P14: BLOCKED now maps to BLOCKED (not IN_PROGRESS)."""
        from governance.task_lifecycle import STATUS_MIGRATION_MAP, TaskStatus
        assert STATUS_MIGRATION_MAP["BLOCKED"] == TaskStatus.BLOCKED


# ---- BUG-1: DONE Gate Preload ----

class TestPreloadTaskFromTypeDB:
    """_preload_task_from_typedb() always refreshes from TypeDB."""

    def _make_task_obj(self, **overrides):
        """Create a mock TypeDB task object."""
        task = MagicMock()
        task.name = overrides.get("name", "Test Task")
        task.phase = overrides.get("phase", "P14")
        task.status = overrides.get("status", "IN_PROGRESS")
        task.agent_id = overrides.get("agent_id", "code-agent")
        task.created_at = overrides.get("created_at", datetime(2026, 3, 24))
        task.claimed_at = overrides.get("claimed_at", None)
        task.completed_at = overrides.get("completed_at", None)
        task.body = overrides.get("body", None)
        task.gap_id = overrides.get("gap_id", None)
        task.priority = overrides.get("priority", "HIGH")
        task.task_type = overrides.get("task_type", "bug")
        task.evidence = overrides.get("evidence", None)
        task.resolution = overrides.get("resolution", None)
        task.document_path = overrides.get("document_path", None)
        task.linked_rules = overrides.get("linked_rules", [])
        task.linked_sessions = overrides.get("linked_sessions", ["SES-001"])
        task.linked_commits = overrides.get("linked_commits", [])
        task.linked_documents = overrides.get("linked_documents", ["docs/plan.md"])
        task.summary = overrides.get("summary", "Test summary")
        task.workspace_id = overrides.get("workspace_id", None)
        return task

    @patch("governance.services.tasks_preload.get_typedb_client")
    def test_preload_populates_tasks_store(self, mock_get_client):
        """Preload creates _tasks_store entry with all fields."""
        from governance.services.tasks_preload import _preload_task_from_typedb
        from governance.stores import _tasks_store

        mock_client = MagicMock()
        task_obj = self._make_task_obj(linked_documents=["docs/plan.md"])
        mock_client.get_task.return_value = task_obj
        mock_get_client.return_value = mock_client

        # Clear any existing entry
        _tasks_store.pop("T-PRELOAD-001", None)

        result = _preload_task_from_typedb("T-PRELOAD-001")
        assert result is True
        assert "T-PRELOAD-001" in _tasks_store
        assert _tasks_store["T-PRELOAD-001"]["linked_documents"] == ["docs/plan.md"]
        assert _tasks_store["T-PRELOAD-001"]["linked_sessions"] == ["SES-001"]

        # Cleanup
        _tasks_store.pop("T-PRELOAD-001", None)

    @patch("governance.services.tasks_preload.get_typedb_client")
    def test_preload_refreshes_stale_data(self, mock_get_client):
        """P14 BUG-1: Even if task IS in _tasks_store, preload refreshes from TypeDB."""
        from governance.services.tasks_preload import _preload_task_from_typedb
        from governance.stores import _tasks_store

        # Pre-populate with STALE data (empty linked_documents)
        _tasks_store["T-STALE-001"] = {
            "task_id": "T-STALE-001",
            "linked_documents": [],  # Stale — MCP added docs after creation
            "linked_sessions": [],
        }

        mock_client = MagicMock()
        task_obj = self._make_task_obj(linked_documents=["docs/fresh.md"])
        mock_client.get_task.return_value = task_obj
        mock_get_client.return_value = mock_client

        result = _preload_task_from_typedb("T-STALE-001")
        assert result is True
        # Verify stale data was replaced with fresh TypeDB data
        assert _tasks_store["T-STALE-001"]["linked_documents"] == ["docs/fresh.md"]

        # Cleanup
        _tasks_store.pop("T-STALE-001", None)

    @patch("governance.services.tasks_preload.get_typedb_client")
    def test_preload_returns_false_no_client(self, mock_get_client):
        """Preload returns False when TypeDB client unavailable."""
        from governance.services.tasks_preload import _preload_task_from_typedb
        mock_get_client.return_value = None
        assert _preload_task_from_typedb("T-NO-CLIENT") is False

    @patch("governance.services.tasks_preload.get_typedb_client")
    def test_preload_returns_false_task_not_found(self, mock_get_client):
        """Preload returns False when task doesn't exist in TypeDB."""
        from governance.services.tasks_preload import _preload_task_from_typedb
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_get_client.return_value = mock_client
        assert _preload_task_from_typedb("T-MISSING") is False


class TestDoneGateWithPreload:
    """DONE gate validation uses preloaded TypeDB data including linked_documents."""

    def _make_task_obj(self, **overrides):
        task = MagicMock()
        task.name = overrides.get("name", "Test Task")
        task.phase = "P14"
        task.status = "IN_PROGRESS"
        task.agent_id = overrides.get("agent_id", "code-agent")
        task.created_at = datetime(2026, 3, 24)
        task.claimed_at = None
        task.completed_at = None
        task.body = None
        task.gap_id = None
        task.priority = "HIGH"
        task.task_type = "bug"
        task.evidence = None
        task.resolution = None
        task.document_path = None
        task.linked_rules = []
        task.linked_sessions = overrides.get("linked_sessions", ["SES-001"])
        task.linked_commits = []
        task.linked_documents = overrides.get("linked_documents", ["docs/plan.md"])
        task.summary = overrides.get("summary", "Test summary")
        task.workspace_id = None
        return task

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_gate_passes_with_preloaded_documents(self, mock_get_client):
        """P14 BUG-1: DONE gate must pass when linked_documents exist in TypeDB."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        task_obj = self._make_task_obj(
            linked_documents=["docs/plan.md"],
            linked_sessions=["SES-001"],
            summary="Has everything",
            agent_id="code-agent",
        )
        mock_client = MagicMock()
        mock_client.get_task.return_value = task_obj
        mock_client.update_task_status.return_value = task_obj
        mock_get_client.return_value = mock_client

        # Pre-populate with stale data that would fail DONE gate
        _tasks_store["T-DONE-001"] = {
            "task_id": "T-DONE-001",
            "description": "Test",
            "status": "IN_PROGRESS",
            "linked_documents": [],  # Stale!
            "linked_sessions": [],
            "summary": "",
            "agent_id": "",
        }

        # This should NOT raise because preload refreshes from TypeDB
        result = update_task(
            "T-DONE-001",
            status="DONE",
            summary="Has everything",
            agent_id="code-agent",
            linked_sessions=["SES-001"],
            linked_documents=["docs/plan.md"],
        )
        assert result is not None
        assert result["status"] == "DONE"

        # Cleanup
        _tasks_store.pop("T-DONE-001", None)

    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_done_gate_fails_without_documents(self, mock_get_client):
        """DONE gate must fail when no linked_documents exist (feature type)."""
        from governance.services.tasks_mutations import update_task, _tasks_store

        task_obj = self._make_task_obj(
            linked_documents=[],
            linked_sessions=["SES-001"],
            summary="No docs",
            agent_id="code-agent",
        )
        # EPIC-TASK-TAXONOMY-V2: feature type requires linked_documents
        task_obj.task_type = "feature"
        mock_client = MagicMock()
        mock_client.get_task.return_value = task_obj
        mock_get_client.return_value = mock_client

        # Seed _tasks_store so DONE gate can read task_type
        _tasks_store["T-DONE-002"] = {
            "task_id": "T-DONE-002",
            "description": "No docs",
            "status": "IN_PROGRESS",
            "task_type": "feature",
            "linked_documents": [],
            "linked_sessions": ["SES-001"],
            "summary": "No docs",
            "agent_id": "code-agent",
        }

        with pytest.raises(ValueError, match="DONE gate validation failed"):
            update_task(
                "T-DONE-002",
                status="DONE",
                summary="No docs",
                agent_id="code-agent",
                linked_sessions=["SES-001"],
            )

        # Cleanup
        _tasks_store.pop("T-DONE-002", None)


# ---- BUG-3: Cancel Replaces Delete for Active Tasks ----

class TestCancelSelectedTask:
    """cancel_selected_task controller trigger sets CANCELED status."""

    def _make_controller_state(self, task_status="IN_PROGRESS"):
        """Create mock state + ctrl for controller registration."""
        state = MagicMock()
        state.selected_task = {
            "task_id": "T-CANCEL-001",
            "id": "T-CANCEL-001",
            "status": task_status,
        }
        state.is_loading = False
        state.has_error = False
        ctrl = MagicMock()
        triggers = {}

        def mock_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = mock_trigger
        return state, ctrl, triggers

    @patch("httpx.Client")
    def test_cancel_sets_canceled_status(self, mock_client_cls):
        """Cancel button sends PUT with status=CANCELED."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        canceled_response = MagicMock()
        canceled_response.status_code = 200
        canceled_response.json.return_value = {
            "task_id": "T-CANCEL-001",
            "status": "CANCELED",
        }
        mock_client.put.return_value = canceled_response
        mock_client_cls.return_value = mock_client

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        assert "cancel_selected_task" in triggers
        triggers["cancel_selected_task"]()

        # Verify PUT was called with status=CANCELED
        mock_client.put.assert_called_once()
        call_args = mock_client.put.call_args
        assert call_args[1]["json"] == {"status": "CANCELED"}

        # Verify state updated
        assert state.selected_task == {"task_id": "T-CANCEL-001", "status": "CANCELED"}
        assert state.status_message == "Task T-CANCEL-001 canceled"

    @patch("httpx.Client")
    def test_cancel_trigger_exists(self, mock_client_cls):
        """cancel_selected_task trigger is registered."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state, ctrl, triggers = self._make_controller_state()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        assert "cancel_selected_task" in triggers


class TestDeleteButtonVisibility:
    """P14: Delete button only visible for terminal tasks."""

    def test_terminal_states_include_canceled(self):
        """CANCELED is a terminal state — Delete should be visible."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.CANCELED.is_terminal is True

    def test_in_progress_not_terminal(self):
        """IN_PROGRESS is not terminal — Delete should be hidden."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.IN_PROGRESS.is_terminal is False

    def test_todo_not_terminal(self):
        """TODO is not terminal — Delete should be hidden."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.TODO.is_terminal is False

    def test_blocked_not_terminal(self):
        """BLOCKED is not terminal — Delete should be hidden."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.BLOCKED.is_terminal is False

    def test_done_is_terminal(self):
        """DONE is terminal — Delete should be visible."""
        from governance.task_lifecycle import TaskStatus
        assert TaskStatus.DONE.is_terminal is True


class TestUIStatusOptions:
    """P14: UI state includes CANCELED in status options."""

    def test_initial_state_has_canceled(self):
        """initial.py task_status_options must include CANCELED."""
        from agent.governance_ui.state.initial import get_initial_state
        initial = get_initial_state()
        assert "CANCELED" in initial["task_status_options"]

    def test_initial_state_has_five_statuses(self):
        """Edit dropdown shows exactly 5 statuses."""
        from agent.governance_ui.state.initial import get_initial_state
        initial = get_initial_state()
        expected = ["TODO", "IN_PROGRESS", "DONE", "BLOCKED", "CANCELED"]
        assert initial["task_status_options"] == expected
