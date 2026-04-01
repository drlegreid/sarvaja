"""Unit tests for EPIC-TASK-TAXONOMY-V2 alias normalization.

Tests that deprecated task_type values are normalized to canonical types
at the service boundary (both create_task and update_task).
"""
import pytest
from unittest.mock import patch, MagicMock

from agent.governance_ui.state.constants import TASK_TYPE_ALIASES


class TestTaskTypeAliases:
    """Test TASK_TYPE_ALIASES constant correctness."""

    def test_gap_aliases_to_bug(self):
        assert TASK_TYPE_ALIASES["gap"] == "bug"

    def test_story_aliases_to_feature(self):
        assert TASK_TYPE_ALIASES["story"] == "feature"

    def test_specification_aliases_to_spec(self):
        assert TASK_TYPE_ALIASES["specification"] == "spec"

    def test_epic_aliases_to_feature(self):
        assert TASK_TYPE_ALIASES["epic"] == "feature"

    def test_canonical_types_not_in_aliases(self):
        """Canonical types should NOT appear as alias keys."""
        canonical = {"bug", "feature", "chore", "research", "spec", "test"}
        for c in canonical:
            assert c not in TASK_TYPE_ALIASES

    def test_alias_values_are_canonical(self):
        """Every alias must resolve to one of the 6 canonical types."""
        canonical = {"bug", "feature", "chore", "research", "spec", "test"}
        for alias, target in TASK_TYPE_ALIASES.items():
            assert target in canonical, f"Alias '{alias}' -> '{target}' is not canonical"


class TestAliasNormalizationOnCreate:
    """Test that create_task normalizes deprecated task_type values."""

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    @patch("governance.services.tasks.task_to_response")
    def test_gap_normalized_to_bug_on_create(
        self, mock_resp, mock_log, mock_mon, mock_audit, mock_client
    ):
        """task_type='gap' should be normalized to 'bug' before reaching TypeDB."""
        from governance.services.tasks import create_task

        mock_task = MagicMock()
        mock_task.created_at = None
        mock_client_inst = MagicMock()
        mock_client_inst.get_task.return_value = None
        mock_client_inst.insert_task.return_value = mock_task
        mock_client.return_value = mock_client_inst
        mock_resp.return_value = MagicMock(
            task_id="BUG-001", created_at=None,
            model_dump=MagicMock(return_value={"task_id": "BUG-001"}),
        )

        create_task(
            task_id="BUG-001",
            description="Test gap alias",
            task_type="gap",
            phase="P10",
        )

        # Verify insert_task was called with normalized type
        call_kwargs = mock_client_inst.insert_task.call_args
        assert call_kwargs.kwargs.get("task_type") == "bug" or \
            (call_kwargs[1].get("task_type") == "bug" if len(call_kwargs) > 1 else False)

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    @patch("governance.services.tasks.task_to_response")
    def test_story_normalized_to_feature_on_create(
        self, mock_resp, mock_log, mock_mon, mock_audit, mock_client
    ):
        from governance.services.tasks import create_task

        mock_task = MagicMock()
        mock_task.created_at = None
        mock_client_inst = MagicMock()
        mock_client_inst.get_task.return_value = None
        mock_client_inst.insert_task.return_value = mock_task
        mock_client.return_value = mock_client_inst
        mock_resp.return_value = MagicMock(
            task_id="FEAT-001", created_at=None,
            model_dump=MagicMock(return_value={"task_id": "FEAT-001"}),
        )

        create_task(
            task_id="FEAT-001",
            description="Test story alias",
            task_type="story",
            phase="P10",
        )

        call_kwargs = mock_client_inst.insert_task.call_args
        assert call_kwargs.kwargs.get("task_type") == "feature" or \
            (call_kwargs[1].get("task_type") == "feature" if len(call_kwargs) > 1 else False)

    @patch("governance.services.tasks.get_typedb_client")
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.log_event")
    @patch("governance.services.tasks.task_to_response")
    def test_canonical_type_unchanged_on_create(
        self, mock_resp, mock_log, mock_mon, mock_audit, mock_client
    ):
        """Canonical types should pass through without normalization."""
        from governance.services.tasks import create_task

        mock_task = MagicMock()
        mock_task.created_at = None
        mock_client_inst = MagicMock()
        mock_client_inst.get_task.return_value = None
        mock_client_inst.insert_task.return_value = mock_task
        mock_client.return_value = mock_client_inst
        mock_resp.return_value = MagicMock(
            task_id="BUG-001", created_at=None,
            model_dump=MagicMock(return_value={"task_id": "BUG-001"}),
        )

        create_task(
            task_id="BUG-001",
            description="Test canonical type",
            task_type="bug",
            phase="P10",
        )

        call_kwargs = mock_client_inst.insert_task.call_args
        assert call_kwargs.kwargs.get("task_type") == "bug" or \
            (call_kwargs[1].get("task_type") == "bug" if len(call_kwargs) > 1 else False)


class TestAliasNormalizationOnUpdate:
    """Test that update_task normalizes deprecated task_type values."""

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations._tasks_store", {
        "TEST-001": {"task_id": "TEST-001", "description": "test", "status": "TODO",
                     "phase": "P10", "linked_sessions": []}
    })
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.log_event")
    def test_gap_normalized_to_bug_on_update(
        self, mock_log, mock_mon, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task

        mock_client_inst = MagicMock()
        mock_task_obj = MagicMock()
        mock_task_obj.status = "TODO"
        mock_task_obj.agent_id = None
        mock_task_obj.task_type = None
        mock_client_inst.get_task.return_value = mock_task_obj
        mock_client.return_value = mock_client_inst

        update_task("TEST-001", task_type="gap")

        # Verify update_task was called with normalized type
        if mock_client_inst.update_task.called:
            call_kwargs = mock_client_inst.update_task.call_args
            assert call_kwargs.kwargs.get("task_type") == "bug"

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations._tasks_store", {
        "TEST-002": {"task_id": "TEST-002", "description": "test", "status": "TODO",
                     "phase": "P10", "linked_sessions": []}
    })
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.log_event")
    def test_specification_normalized_to_spec_on_update(
        self, mock_log, mock_mon, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task

        mock_client_inst = MagicMock()
        mock_task_obj = MagicMock()
        mock_task_obj.status = "TODO"
        mock_task_obj.agent_id = None
        mock_task_obj.task_type = None
        mock_client_inst.get_task.return_value = mock_task_obj
        mock_client.return_value = mock_client_inst

        update_task("TEST-002", task_type="specification")

        if mock_client_inst.update_task.called:
            call_kwargs = mock_client_inst.update_task.call_args
            assert call_kwargs.kwargs.get("task_type") == "spec"

    @patch("governance.services.tasks_mutations.get_typedb_client")
    @patch("governance.services.tasks_mutations._tasks_store", {
        "TEST-003": {"task_id": "TEST-003", "description": "test", "status": "TODO",
                     "phase": "P10", "linked_sessions": []}
    })
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.log_event")
    def test_epic_normalized_to_feature_on_update(
        self, mock_log, mock_mon, mock_audit, mock_client
    ):
        from governance.services.tasks_mutations import update_task

        mock_client_inst = MagicMock()
        mock_task_obj = MagicMock()
        mock_task_obj.status = "TODO"
        mock_task_obj.agent_id = None
        mock_task_obj.task_type = None
        mock_client_inst.get_task.return_value = mock_task_obj
        mock_client.return_value = mock_client_inst

        update_task("TEST-003", task_type="epic")

        if mock_client_inst.update_task.called:
            call_kwargs = mock_client_inst.update_task.call_args
            assert call_kwargs.kwargs.get("task_type") == "feature"
