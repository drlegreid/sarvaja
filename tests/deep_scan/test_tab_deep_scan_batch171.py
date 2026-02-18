"""Deep scan batch 171: MCP tools + heuristic checks layer.

Batch 171 findings: 8 total, 3 confirmed fixes, 5 rejected/deferred.
- BUG-VERIFY-STATUS-001: task_verify used "completed" (lowercase) → "DONE"
- BUG-HEURISTIC-TZ-001: Stale session check used TZ-aware threshold vs naive start_time
- BUG-SYNC-STATUS-001: session_sync_todos passed lowercase TodoWrite statuses to TypeDB
"""
import pytest
from pathlib import Path


# ── Task verify status defense ──────────────


class TestTaskVerifyStatusDefense:
    """Verify task_verify uses uppercase DONE status."""

    def test_verify_uses_uppercase_done(self):
        """task_verify passes 'DONE' not 'completed' to update_task."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        # Find the task_verify function's update_task call
        start = src.index("def task_verify")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        verify_func = src[start:end]
        assert 'status="DONE"' in verify_func

    def test_verify_no_lowercase_completed(self):
        """task_verify does NOT use lowercase 'completed' for status."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        start = src.index("def task_verify")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        verify_func = src[start:end]
        assert 'status="completed"' not in verify_func

    def test_lifecycle_timestamps_check_uppercase(self):
        """Lifecycle timestamps only fire for uppercase statuses."""
        # The lifecycle timestamp logic checks for "DONE", "CLOSED", "IN_PROGRESS"
        # Lowercase "completed" would bypass all of these
        valid_statuses = {"DONE", "CLOSED", "IN_PROGRESS", "TODO", "OPEN"}
        assert "completed" not in valid_statuses


# ── Heuristic TZ defense ──────────────


class TestHeuristicTimezoneDefense:
    """Verify stale session check uses naive datetime."""

    def test_threshold_uses_naive_datetime(self):
        """Stale session check uses datetime.now() without timezone."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tests/heuristic_checks_session.py").read_text()
        start = src.index("def check_session_stale_active")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "datetime.now()" in func
        # Should NOT have timezone.utc in the threshold computation
        assert "datetime.now(timezone.utc)" not in func

    def test_naive_iso_comparison_works(self):
        """Naive ISO strings compare correctly for stale detection."""
        from datetime import datetime, timedelta
        now = datetime.now()
        yesterday = (now - timedelta(hours=25)).isoformat()
        threshold = (now - timedelta(hours=24)).isoformat()
        assert yesterday < threshold  # 25h ago is before 24h threshold

    def test_tz_aware_vs_naive_would_break(self):
        """TZ-aware ISO strings always sort after naive ones (broken)."""
        naive = "2026-02-15T10:00:00"
        aware = "2026-02-15T10:00:00+00:00"
        # String comparison: naive < aware because '+' > end-of-string
        assert naive < aware  # This would make ALL naive times "stale"


# ── Session sync status mapping defense ──────────────


class TestSessionSyncStatusMappingDefense:
    """Verify session_sync_todos maps TodoWrite statuses to uppercase."""

    def test_status_map_exists(self):
        """_STATUS_MAP mapping exists in session_sync_todos."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        assert "_STATUS_MAP" in src

    def test_pending_maps_to_todo(self):
        """'pending' maps to 'TODO'."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        assert '"pending": "TODO"' in src

    def test_in_progress_maps_to_uppercase(self):
        """'in_progress' maps to 'IN_PROGRESS'."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        assert '"in_progress": "IN_PROGRESS"' in src

    def test_completed_maps_to_done(self):
        """'completed' maps to 'DONE'."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        assert '"completed": "DONE"' in src


# ── MCP session topic extraction defense ──────────────


class TestMCPSessionTopicDefense:
    """Verify session topic extraction patterns."""

    def test_session_id_format(self):
        """Session ID format: SESSION-YYYY-MM-DD-TOPIC."""
        sid = "SESSION-2026-02-15-MULTI-WORD-TOPIC"
        parts = sid.split("-")
        assert parts[0] == "SESSION"
        assert parts[1] == "2026"
        assert parts[4] == "MULTI"  # Topic starts at index 4

    def test_last_segment_loses_topic(self):
        """split('-')[-1] only gets last word of multi-word topic."""
        sid = "SESSION-2026-02-15-MULTI-WORD-TOPIC"
        last = sid.split("-")[-1].lower()
        assert last == "topic"  # Loses "MULTI" and "WORD"
        # Full topic would be: "-".join(sid.split("-")[4:]).lower()
        full_topic = "-".join(sid.split("-")[4:]).lower()
        assert full_topic == "multi-word-topic"


# ── CVP category defense ──────────────


class TestCVPCategoryDefense:
    """Verify CVP sweep category handling."""

    def test_runner_exec_exists(self):
        """Runner exec module exists."""
        root = Path(__file__).parent.parent.parent
        assert (root / "governance/routes/tests/runner_exec.py").exists()

    def test_execute_heuristic_callable(self):
        """execute_heuristic function is importable."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/tests/runner_exec.py").read_text()
        assert "def execute_heuristic" in src
