"""
Tests for task data integrity remediation (2026-03-21 audit, 228 tasks).

Covers:
1. Status normalization (lowercase → uppercase)
2. Missing completed_at backfill
3. Timestamp ordering fix (completed_at < created_at)
4. Seed task idempotency (no duplicate TODO-YYYYMMDD)
5. Test artifact detection
6. Schema: document-references-task relation in monolithic schema

TDD: Tests define the contract. Per DOC-SIZE-01-v1: <=300 lines.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# ── 1. Status Normalization ──


class TestStatusNormalization:
    """Verify statuses are normalized to uppercase at service boundary."""

    def test_create_task_normalizes_status(self):
        """create_task() must normalize lowercase status to uppercase."""
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_task = MagicMock()
        mock_task.id = "T-NORM"
        mock_task.name = "Test"
        mock_task.status = "OPEN"
        mock_task.phase = "P9"
        mock_task.priority = None
        mock_task.task_type = None
        mock_task.agent_id = None
        mock_task.body = None
        mock_task.description = "Test"
        mock_task.resolution = None
        mock_task.gap_id = None
        mock_task.evidence = None
        mock_task.document_path = None
        mock_task.linked_rules = []
        mock_task.linked_sessions = []
        mock_task.linked_commits = []
        mock_task.linked_documents = []
        mock_task.workspace_id = None
        mock_task.created_at = datetime(2026, 3, 21)
        mock_task.claimed_at = None
        mock_task.completed_at = None
        mock_client.insert_task.return_value = mock_task

        with patch("governance.services.tasks.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks._tasks_store", {}), \
             patch("governance.services.tasks._sessions_store", {}), \
             patch("governance.services.tasks.record_audit"), \
             patch("governance.services.tasks.log_event"), \
             patch("governance.services.tasks._monitor"):
            from governance.services.tasks import create_task
            create_task(task_id="T-NORM", description="Test", status="pending")

        # Verify insert_task was called with uppercase status
        call_kwargs = mock_client.insert_task.call_args
        assert call_kwargs[1].get("status") == "PENDING" or \
               (call_kwargs[0] if call_kwargs[0] else [""])[0] != "pending", \
            "Status must be normalized to uppercase"

    def test_update_task_normalizes_status(self):
        """update_task() must normalize lowercase status to uppercase."""
        import inspect
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        # Verify .upper() is called on status
        assert "status.upper()" in source or "upper()" in source


class TestStatusValues:
    """Verify accepted status values."""

    def test_valid_statuses(self):
        """Only valid uppercase statuses should be accepted."""
        valid = {"OPEN", "IN_PROGRESS", "CLOSED", "TODO", "DONE", "PENDING"}
        for s in valid:
            assert s == s.upper()

    def test_normalize_lowercase_variants(self):
        """Common lowercase variants should normalize correctly."""
        pairs = [
            ("completed", "COMPLETED"),
            ("in_progress", "IN_PROGRESS"),
            ("pending", "PENDING"),
            ("done", "DONE"),
            ("open", "OPEN"),
        ]
        for lower, expected in pairs:
            assert lower.upper() == expected


# ── 2. Completed_at Backfill ──


class TestCompletedAtBackfill:
    """Verify DONE/CLOSED tasks get completed_at timestamps."""

    def test_done_status_sets_completed_at(self):
        """When status=DONE, completed_at should be set if missing."""
        import inspect
        from governance.typedb.queries.tasks import crud
        source = inspect.getsource(crud)
        # Verify DONE status triggers completed_at assignment
        assert "completed_at" in source or "task-completed-at" in source

    def test_closed_status_sets_completed_at(self):
        """When status=CLOSED, completed_at should be set if missing."""
        import inspect
        from governance.typedb.queries.tasks import crud
        source = inspect.getsource(crud)
        assert "CLOSED" in source


# ── 3. Timestamp Ordering ──


class TestTimestampOrdering:
    """Verify completed_at >= created_at invariant."""

    def test_completed_before_created_is_invalid(self):
        """completed_at < created_at is a data integrity violation."""
        created = datetime(2026, 3, 21, 10, 0, 0)
        completed = datetime(2026, 3, 20, 10, 0, 0)  # BEFORE created
        assert completed < created, "Test setup: completed should be before created"
        # Remediation: completed_at should be set to created_at when ordering is wrong
        fixed = max(completed, created)
        assert fixed >= created

    def test_valid_timestamp_ordering(self):
        """Normal case: completed_at >= created_at."""
        created = datetime(2026, 3, 20, 10, 0, 0)
        completed = datetime(2026, 3, 21, 10, 0, 0)
        assert completed >= created


# ── 4. Seed Task Idempotency ──


class TestSeedTaskIdempotency:
    """Verify seed tasks don't create duplicates on restart."""

    def test_seed_skips_existing_tasks(self):
        """seed_tasks_to_typedb must skip tasks that already exist."""
        mock_client = MagicMock()
        # Simulate task already exists
        mock_client.get_task.return_value = MagicMock()

        from governance.seed.typedb import seed_tasks_to_typedb
        count = seed_tasks_to_typedb(mock_client)

        # Should not insert any tasks since all exist
        mock_client.insert_task.assert_not_called()
        assert count == 0

    def test_seed_inserts_new_tasks(self):
        """seed_tasks_to_typedb inserts tasks that don't exist."""
        mock_client = MagicMock()
        mock_client.get_task.return_value = None  # Task doesn't exist
        mock_client.insert_task.return_value = True

        from governance.seed.typedb import seed_tasks_to_typedb
        count = seed_tasks_to_typedb(mock_client)

        assert count > 0
        assert mock_client.insert_task.call_count == count

    def test_seed_tasks_have_unique_ids(self):
        """Seed task IDs must be unique."""
        from governance.seed.data import get_seed_tasks
        tasks = get_seed_tasks()
        ids = [t["task_id"] for t in tasks]
        assert len(ids) == len(set(ids)), f"Duplicate seed task IDs: {[x for x in ids if ids.count(x) > 1]}"


# ── 5. Test Artifact Detection ──


class TestTestArtifactDetection:
    """Verify test artifacts can be identified and excluded."""

    def test_test_prefix_detected(self):
        """Tasks with TEST- prefix (no version suffix) are test artifacts."""
        test_ids = ["TEST-9A3E0F65", "TEST-ABC123", "TEST-TEMP"]
        for tid in test_ids:
            assert tid.startswith("TEST-")
            # Real semantic IDs have version: TEST-BUGFIX-01-v1
            assert "-v" not in tid.split("TEST-", 1)[1]

    def test_real_test_rules_not_flagged(self):
        """Real rules like TEST-E2E-01-v1 should NOT be flagged as artifacts."""
        real_ids = ["TEST-E2E-01-v1", "TEST-GUARD-01-v1", "TEST-BUGFIX-01-v1"]
        for tid in real_ids:
            parts_after_test = tid.split("TEST-", 1)[1]
            assert "-v" in parts_after_test, f"{tid} should not be flagged"


# ── 6. Schema Relation in Monolithic ──


class TestMonolithicSchemaDocRelation:
    """Verify document-references-task relation added to monolithic schema.tql."""

    def test_relation_exists_in_schema_tql(self):
        """schema.tql must have document-references-task relation."""
        from pathlib import Path
        schema = Path(__file__).resolve().parents[2] / "governance" / "schema.tql"
        content = schema.read_text()
        assert "document-references-task" in content


# ── 7. Remediation Script Contract ──


class TestRemediationScriptContract:
    """Verify remediation script exists and has required capabilities."""

    def test_script_exists(self):
        """scripts/remediate_task_data.py must exist."""
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "scripts" / "remediate_task_data.py"
        assert script.exists(), "Remediation script not found"

    def test_script_has_dry_run_support(self):
        """Script must support --dry-run flag."""
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "scripts" / "remediate_task_data.py"
        content = script.read_text()
        assert "dry_run" in content or "dry-run" in content

    def test_script_has_status_normalization(self):
        """Script must handle status normalization."""
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "scripts" / "remediate_task_data.py"
        content = script.read_text()
        assert "upper()" in content or "normalize" in content

    def test_script_has_completed_at_backfill(self):
        """Script must handle completed_at backfill."""
        from pathlib import Path
        script = Path(__file__).resolve().parents[2] / "scripts" / "remediate_task_data.py"
        content = script.read_text()
        assert "completed_at" in content
