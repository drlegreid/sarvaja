"""
Tests for EPIC-TASK-QUALITY-V3 Phase 16: Issue Triage Workflow.

Feature 1: H-TASK-STALE-001 — Stale Task Detection Heuristic
Feature 2: Duplicate Detection on Create

Per BDD specs in P16 plan.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


# ===== Feature 1: H-TASK-STALE-001 Tests =====

class TestStaleTaskHeuristic:
    """H-TASK-STALE-001: IN_PROGRESS tasks >7 days without commits are stale."""

    def _make_task(self, task_id="T-1", status="IN_PROGRESS",
                   claimed_at=None, created_at=None, linked_commits=None):
        return {
            "task_id": task_id,
            "status": status,
            "claimed_at": claimed_at,
            "created_at": created_at,
            "linked_commits": linked_commits or [],
        }

    def test_stale_task_detected(self):
        """IN_PROGRESS task claimed 10 days ago with no commits → FAIL."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        stale_task = self._make_task(claimed_at=ten_days_ago)

        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[stale_task],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "FAIL"
        assert "T-1" in result["violations"]
        assert "stale" in result["message"].lower()
        assert "7 days" in result["message"] or "7" in result["message"]

    def test_active_task_passes(self):
        """IN_PROGRESS task claimed 2 days ago → PASS."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        two_days_ago = (datetime.now() - timedelta(days=2)).isoformat()
        active_task = self._make_task(claimed_at=two_days_ago)

        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[active_task],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "PASS"
        assert not result["violations"]

    def test_done_task_exempt(self):
        """DONE tasks are not fetched (API filters by IN_PROGRESS)."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        # API query is ?status=IN_PROGRESS, so DONE tasks won't appear
        # Simulate empty response (no IN_PROGRESS tasks)
        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "SKIP"

    def test_no_claimed_at_uses_created_at(self):
        """When claimed_at is missing, fall back to created_at."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        task = self._make_task(claimed_at=None, created_at=ten_days_ago)

        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[task],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "FAIL"
        assert "T-1" in result["violations"]

    def test_no_date_at_all_skipped(self):
        """Task with no claimed_at or created_at is skipped (PASS)."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        task = self._make_task(claimed_at=None, created_at=None)

        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[task],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "PASS"
        assert not result["violations"]

    def test_task_with_commits_passes(self):
        """Old IN_PROGRESS task with linked_commits is active (PASS)."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        task = self._make_task(
            claimed_at=ten_days_ago,
            linked_commits=["abc123"],
        )

        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[task],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "PASS"

    def test_test_task_skipped(self):
        """TEST-* tasks are skipped by the heuristic."""
        from governance.routes.tests.heuristic_checks_triage import (
            check_task_stale_in_progress,
        )
        ten_days_ago = (datetime.now() - timedelta(days=10)).isoformat()
        task = self._make_task(task_id="TEST-001", claimed_at=ten_days_ago)

        with patch(
            "governance.routes.tests.heuristic_checks_triage._api_get",
            return_value=[task],
        ):
            result = check_task_stale_in_progress("http://test")

        assert result["status"] == "PASS"

    def test_registered_in_heuristic_checks(self):
        """H-TASK-STALE-001 should be registered in HEURISTIC_CHECKS."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        ids = [c["id"] for c in HEURISTIC_CHECKS]
        assert "H-TASK-STALE-001" in ids

    def test_stale_threshold_is_7_days(self):
        """Threshold should be exactly 7 days."""
        from governance.routes.tests.heuristic_checks_triage import (
            STALE_THRESHOLD_DAYS,
        )
        assert STALE_THRESHOLD_DAYS == 7


# ===== Feature 2: Duplicate Detection Tests =====

class TestJaccardSimilarity:
    """Unit tests for _jaccard_word_similarity."""

    def test_identical_strings(self):
        from governance.services.tasks_duplicate import _jaccard_word_similarity
        assert _jaccard_word_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        from governance.services.tasks_duplicate import _jaccard_word_similarity
        assert _jaccard_word_similarity("hello world", "foo bar") == 0.0

    def test_partial_overlap(self):
        from governance.services.tasks_duplicate import _jaccard_word_similarity
        # "hello" overlaps, "world" vs "there" don't → 1/3 ≈ 0.333
        result = _jaccard_word_similarity("hello world", "hello there")
        assert 0.3 < result < 0.4

    def test_empty_string(self):
        from governance.services.tasks_duplicate import _jaccard_word_similarity
        assert _jaccard_word_similarity("", "hello") == 0.0
        assert _jaccard_word_similarity("hello", "") == 0.0

    def test_none_input(self):
        from governance.services.tasks_duplicate import _jaccard_word_similarity
        assert _jaccard_word_similarity(None, "hello") == 0.0

    def test_case_insensitive(self):
        from governance.services.tasks_duplicate import _jaccard_word_similarity
        assert _jaccard_word_similarity("Hello World", "hello world") == 1.0

    def test_high_similarity(self):
        """Strings with >80% word overlap should score above threshold."""
        from governance.services.tasks_duplicate import (
            _jaccard_word_similarity,
            DUPLICATE_SIMILARITY_THRESHOLD,
        )
        # 4/5 words match = 0.8 (identical except one word added)
        result = _jaccard_word_similarity(
            "session chip navigation broken",
            "session chip navigation broken again",
        )
        assert result >= DUPLICATE_SIMILARITY_THRESHOLD


class TestDuplicateDetection:
    """Tests for _find_duplicate_tasks and _attach_duplicate_warnings."""

    def test_duplicate_warning_on_similar_summary(self):
        """Creating task with similar summary → warning returned."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {
                "task_id": "SRVJ-BUG-013",
                "status": "IN_PROGRESS",
                # 6 words: {fix, the, session, chip, navigation, broken}
                "summary": "Fix the session chip navigation broken",
                "description": "Fix the session chip navigation broken",
            },
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            # 5/6 words overlap → Jaccard = 5/6 ≈ 0.833 > 0.8
            warnings = _find_duplicate_tasks(
                summary="fix the session chip navigation",
                description="fix the session chip navigation",
                exclude_task_id="NEW-001",
            )

        assert len(warnings) >= 1
        assert "SRVJ-BUG-013" in warnings[0]
        assert "Possible duplicate" in warnings[0]

    def test_no_warning_for_unique_summary(self):
        """Creating task with unique summary → no warnings."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {
                "task_id": "SRVJ-BUG-001",
                "status": "OPEN",
                "summary": "Fix login page CSS",
                "description": "Fix login page CSS layout",
            },
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            warnings = _find_duplicate_tasks(
                summary="Add Redis caching layer",
                description="Add Redis caching layer",
                exclude_task_id="NEW-002",
            )

        assert warnings == []

    def test_duplicate_check_case_insensitive(self):
        """Similarity check should be case-insensitive."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {
                "task_id": "BUG-001",
                "status": "OPEN",
                "summary": "FIX THE BROKEN NAVIGATION",
                "description": "Fix the broken navigation",
            },
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            warnings = _find_duplicate_tasks(
                summary="fix the broken navigation",
                description="fix the broken navigation",
                exclude_task_id="NEW-003",
            )

        assert len(warnings) >= 1

    def test_excludes_self(self):
        """Duplicate check should not match against the task being created."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {
                "task_id": "BUG-001",
                "status": "OPEN",
                "summary": "Fix the broken navigation",
            },
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            warnings = _find_duplicate_tasks(
                summary="Fix the broken navigation",
                description="",
                exclude_task_id="BUG-001",  # Same as existing
            )

        assert warnings == []

    def test_skips_test_tasks(self):
        """TEST-* tasks are excluded from duplicate detection."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {
                "task_id": "TEST-001",
                "status": "OPEN",
                "summary": "Fix the broken navigation",
            },
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            warnings = _find_duplicate_tasks(
                summary="Fix the broken navigation",
                description="",
                exclude_task_id="NEW-001",
            )

        assert warnings == []

    def test_skips_closed_tasks(self):
        """CLOSED/CANCELLED tasks are excluded from duplicate detection."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {
                "task_id": "BUG-001",
                "status": "CLOSED",
                "summary": "Fix the broken navigation",
            },
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            warnings = _find_duplicate_tasks(
                summary="Fix the broken navigation",
                description="",
                exclude_task_id="NEW-001",
            )

        assert warnings == []

    def test_short_summary_skipped(self):
        """Summaries shorter than 5 chars are skipped."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=[],
        ):
            warnings = _find_duplicate_tasks(
                summary="hi",
                description="hi",
                exclude_task_id="NEW-001",
            )

        assert warnings == []

    def test_max_3_warnings(self):
        """Should cap warnings at 3."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        existing_tasks = [
            {"task_id": f"BUG-{i}", "status": "OPEN",
             "summary": "fix the broken navigation bar"}
            for i in range(10)
        ]
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            return_value=existing_tasks,
        ):
            warnings = _find_duplicate_tasks(
                summary="fix the broken navigation bar",
                description="",
                exclude_task_id="NEW-001",
            )

        assert len(warnings) <= 3

    def test_api_failure_returns_empty(self):
        """If TypeDB is unavailable, return empty warnings (non-blocking)."""
        from governance.services.tasks_duplicate import _find_duplicate_tasks
        with patch(
            "governance.services.tasks_duplicate.get_all_tasks_from_typedb",
            side_effect=Exception("TypeDB down"),
        ):
            warnings = _find_duplicate_tasks(
                summary="Fix the broken navigation",
                description="",
                exclude_task_id="NEW-001",
            )

        assert warnings == []


class TestAttachDuplicateWarnings:
    """Tests for _attach_duplicate_warnings."""

    def test_attach_to_dict(self):
        """Warnings should be attached to dict response."""
        from governance.services.tasks_duplicate import _attach_duplicate_warnings
        response = {"task_id": "NEW-001", "description": "test"}
        with patch(
            "governance.services.tasks_duplicate._find_duplicate_tasks",
            return_value=["Possible duplicate of BUG-001"],
        ):
            result = _attach_duplicate_warnings(
                response, "test summary", "test desc", "NEW-001",
            )

        assert result["warnings"] == ["Possible duplicate of BUG-001"]

    def test_attach_to_pydantic(self):
        """Warnings should be attached to Pydantic model."""
        from governance.services.tasks_duplicate import _attach_duplicate_warnings
        from governance.models import TaskResponse
        response = TaskResponse(
            task_id="NEW-001", description="test",
            phase="P16", status="TODO",
        )
        with patch(
            "governance.services.tasks_duplicate._find_duplicate_tasks",
            return_value=["Possible duplicate of BUG-001"],
        ):
            result = _attach_duplicate_warnings(
                response, "test summary", "test desc", "NEW-001",
            )

        assert result.warnings == ["Possible duplicate of BUG-001"]

    def test_no_warnings_unchanged(self):
        """No warnings → response returned unchanged."""
        from governance.services.tasks_duplicate import _attach_duplicate_warnings
        response = {"task_id": "NEW-001"}
        with patch(
            "governance.services.tasks_duplicate._find_duplicate_tasks",
            return_value=[],
        ):
            result = _attach_duplicate_warnings(
                response, "unique", "unique", "NEW-001",
            )

        assert "warnings" not in result

    def test_detection_failure_non_blocking(self):
        """If duplicate detection fails, response returned without warnings."""
        from governance.services.tasks_duplicate import _attach_duplicate_warnings
        response = {"task_id": "NEW-001"}
        with patch(
            "governance.services.tasks_duplicate._find_duplicate_tasks",
            side_effect=Exception("boom"),
        ):
            result = _attach_duplicate_warnings(
                response, "test", "test", "NEW-001",
            )

        assert "warnings" not in result


class TestWarningsInTaskResponse:
    """Tests for warnings field in TaskResponse model."""

    def test_task_response_has_warnings_field(self):
        """TaskResponse model should accept warnings list."""
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="T-1", description="test", phase="P16", status="TODO",
            warnings=["Possible duplicate of BUG-001"],
        )
        assert resp.warnings == ["Possible duplicate of BUG-001"]

    def test_task_response_warnings_default_none(self):
        """TaskResponse warnings should default to None."""
        from governance.models import TaskResponse
        resp = TaskResponse(
            task_id="T-1", description="test", phase="P16", status="TODO",
        )
        assert resp.warnings is None
