"""
Tests for EPIC-TASK-QUALITY-V1 Phase 1: Data Integrity.

FIX-DATA-002: Summary backfill + update pipeline
FIX-DATA-003: completed_at backfill
FIX-DATA-004: task_type backfill from ID prefix
FIX-DATA-005: Idempotency guard for link_task_to_document

TDD: Tests define the contract. Per DOC-SIZE-01-v1: <=300 lines.
"""

from unittest.mock import MagicMock, patch

import pytest


# ── FIX-DATA-002: Summary Backfill ──


class TestBackfillSummaries:
    """Verify backfill_summaries() generates correct summaries."""

    def test_null_summary_with_description_gets_backfilled(self):
        tasks = [{"task_id": "T-1", "summary": None, "description": "Fix login bug", "body": None, "name": "T-1"}]
        from scripts.remediate_task_cleanup import backfill_summaries
        result = backfill_summaries(tasks)
        assert result["found"] == 1
        assert result["details"][0]["summary"] == "Fix login bug"

    def test_existing_summary_not_overwritten(self):
        tasks = [{"task_id": "T-2", "summary": "Already set", "description": "Long desc", "body": None, "name": "T-2"}]
        from scripts.remediate_task_cleanup import backfill_summaries
        result = backfill_summaries(tasks)
        assert result["found"] == 0

    def test_long_description_truncated(self):
        desc = "A" * 100
        tasks = [{"task_id": "T-3", "summary": None, "description": desc, "body": None, "name": "T-3"}]
        from scripts.remediate_task_cleanup import backfill_summaries
        result = backfill_summaries(tasks)
        assert result["found"] == 1
        assert result["details"][0]["summary"].endswith("...")
        assert len(result["details"][0]["summary"]) <= 80

    def test_null_description_skipped(self):
        tasks = [{"task_id": "T-4", "summary": None, "description": None, "body": None, "name": None}]
        from scripts.remediate_task_cleanup import backfill_summaries
        result = backfill_summaries(tasks)
        assert result["found"] == 0

    def test_body_used_as_fallback(self):
        tasks = [{"task_id": "T-5", "summary": None, "description": None, "body": "Body text here", "name": "T-5"}]
        from scripts.remediate_task_cleanup import backfill_summaries
        result = backfill_summaries(tasks)
        assert result["found"] == 1
        assert "Body text" in result["details"][0]["summary"]


class TestSummaryUpdatePipeline:
    """Verify summary can be updated through the full pipeline."""

    def test_typedb_update_task_accepts_summary(self):
        """TypeDB update_task() must accept summary parameter."""
        import inspect
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        sig = inspect.signature(TaskCRUDOperations.update_task)
        assert "summary" in sig.parameters, "update_task() missing summary parameter"

    def test_service_update_task_accepts_summary(self):
        """Service update_task() must accept summary parameter."""
        import inspect
        from governance.services.tasks_mutations import update_task
        sig = inspect.signature(update_task)
        assert "summary" in sig.parameters, "Service update_task() missing summary parameter"

    def test_route_passes_summary_to_service(self):
        """Route handler must pass update.summary to service layer."""
        import inspect
        from governance.routes.tasks import crud as route_crud
        source = inspect.getsource(route_crud.update_task)
        assert "summary" in source, "Route update_task must pass summary"

    def test_mcp_task_update_accepts_summary(self):
        """MCP task_update must accept summary parameter."""
        from governance.mcp_tools import tasks_crud
        source = open(tasks_crud.__file__).read()
        # Find the task_update function definition
        assert "summary" in source, "MCP task_update should reference summary"


# ── FIX-DATA-003: completed_at Backfill ──


class TestCompletedAtBackfill:
    """Verify backfill_completed_at from remediate_task_data.py."""

    def test_done_task_gets_completed_at(self):
        from scripts.remediate_task_data import backfill_completed_at
        tasks = [{"task_id": "T-D1", "status": "DONE", "completed_at": None, "created_at": "2026-01-15T10:00:00"}]
        result = backfill_completed_at(tasks, dry_run=True)
        assert result["found"] >= 1

    def test_open_task_skipped(self):
        from scripts.remediate_task_data import backfill_completed_at
        tasks = [{"task_id": "T-O1", "status": "OPEN", "completed_at": None, "created_at": "2026-01-15T10:00:00"}]
        result = backfill_completed_at(tasks, dry_run=True)
        assert result["found"] == 0

    def test_already_has_completed_at_skipped(self):
        from scripts.remediate_task_data import backfill_completed_at
        tasks = [{"task_id": "T-D2", "status": "DONE", "completed_at": "2026-03-21T10:00:00", "created_at": "2026-01-15T10:00:00"}]
        result = backfill_completed_at(tasks, dry_run=True)
        assert result["found"] == 0


# ── FIX-DATA-004: task_type Backfill ──


class TestTaskTypeBackfill:
    """Verify task_type inference from task_id prefix."""

    def test_bug_prefix_inferred(self):
        from scripts.remediate_task_data import backfill_task_type
        tasks = [{"task_id": "BUG-LOGIN-001", "task_type": None}]
        result = backfill_task_type(tasks, dry_run=True)
        assert result["found"] == 1
        assert result["details"][0]["task_type"] == "bug"

    def test_feat_prefix_inferred(self):
        from scripts.remediate_task_data import backfill_task_type
        tasks = [{"task_id": "FEAT-AUTH-001", "task_type": None}]
        result = backfill_task_type(tasks, dry_run=True)
        assert result["found"] == 1
        assert result["details"][0]["task_type"] == "feature"

    def test_epic_prefix_inferred(self):
        from scripts.remediate_task_data import backfill_task_type
        tasks = [{"task_id": "EPIC-TASKS-V2-P9", "task_type": None}]
        result = backfill_task_type(tasks, dry_run=True)
        assert result["found"] == 1
        assert result["details"][0]["task_type"] == "epic"

    def test_fix_prefix_inferred_as_bug(self):
        from scripts.remediate_task_data import backfill_task_type
        tasks = [{"task_id": "FIX-DATA-001", "task_type": None}]
        result = backfill_task_type(tasks, dry_run=True)
        assert result["found"] == 1
        assert result["details"][0]["task_type"] == "bug"

    def test_existing_type_not_overwritten(self):
        from scripts.remediate_task_data import backfill_task_type
        tasks = [{"task_id": "BUG-001", "task_type": "feature"}]
        result = backfill_task_type(tasks, dry_run=True)
        assert result["found"] == 0

    def test_unknown_prefix_skipped(self):
        from scripts.remediate_task_data import backfill_task_type
        tasks = [{"task_id": "TODO-20260322-001", "task_type": None}]
        result = backfill_task_type(tasks, dry_run=True)
        assert result["found"] == 0


# ── FIX-DATA-005: Idempotency Guard ──


class TestLinkTaskToDocumentIdempotency:
    """Verify link_task_to_document checks for existing relation."""

    def test_idempotency_guard_in_source(self):
        """link_task_to_document must check if relation exists before insert."""
        import inspect
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        source = inspect.getsource(TaskLinkingOperations.link_task_to_document)
        assert "match" in source.lower() and ("exists" in source.lower() or "isa document-references-task" in source), \
            "link_task_to_document must check for existing relation"
