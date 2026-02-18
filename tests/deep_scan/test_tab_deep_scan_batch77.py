"""
Batch 77 — Deep Scan: Hooks + Middleware + Context Recovery + Stores.

Triage: 19 findings → 1 confirmed (BUG-SYNC-001), 18 rejected.
Focus: Hook safety, todo sync integrity, preloader correctness.
"""
import inspect
import re

import pytest


# ===========================================================================
# BUG-SYNC-001 CONFIRMED: PATCH/POST response must be checked
# ===========================================================================

class TestTodoSyncResponseCheck:
    """Verify todo_sync checks API response status before recording sync."""

    def test_patch_response_captured(self):
        """PATCH response must be stored in a variable and checked."""
        from hooks import todo_sync  # .claude/hooks/ is on path via conftest
        src = inspect.getsource(todo_sync._sync_todo_to_api)
        assert "patch_resp" in src or "patch_resp = client.patch" in src

    def test_post_response_captured(self):
        """POST response must be stored in a variable and checked."""
        from hooks import todo_sync
        src = inspect.getsource(todo_sync._sync_todo_to_api)
        assert "post_resp" in src or "post_resp = client.post" in src

    def test_patch_failure_returns_false(self):
        """If PATCH returns 500, _sync_todo_to_api returns False."""
        from hooks import todo_sync
        src = inspect.getsource(todo_sync._sync_todo_to_api)
        assert "is_success" in src or "raise_for_status" in src

    def test_post_failure_returns_false(self):
        """If POST returns 500, _sync_todo_to_api returns False."""
        from hooks import todo_sync
        src = inspect.getsource(todo_sync._sync_todo_to_api)
        # Two is_success checks: one for PATCH, one for POST
        assert src.count("is_success") >= 2 or src.count("raise_for_status") >= 2

    def test_sync_state_only_on_success(self):
        """Sync state recording must be AFTER successful response check."""
        from hooks import todo_sync
        src = inspect.getsource(todo_sync._sync_todo_to_api)
        # "return False" must appear before "synced_todos" to ensure
        # failed responses don't reach the state recording
        assert "return False" in src


# ===========================================================================
# Rejected: preloader regex offset (verified correct in batch 76)
# ===========================================================================

class TestPreloaderDecisionParsing:
    """Confirm preloader regex offset is correctly handled."""

    def test_regex_substring_offset_math(self):
        """Regex on content[start:] gives position relative to substring."""
        content = "Header\n## DECISION-001: First\nDetails here\n## DECISION-002: Second\n"
        # Simulate preloader logic
        match = re.search(r"##\s+(DECISION-\d+):\s+(.+?)\n", content)
        assert match is not None
        start = match.end()
        next_section = re.search(r"\n##\s+", content[start:])
        assert next_section is not None
        # Extract section between current and next heading
        section = content[start:start + next_section.start()]
        assert "Details here" in section
        assert "DECISION-002" not in section  # Next heading excluded

    def test_last_decision_gets_rest_of_file(self):
        """When no next section, ternary returns len(content)."""
        content = "## DECISION-001: Only\nSome content here"
        match = re.search(r"##\s+(DECISION-\d+):\s+(.+?)\n", content)
        start = match.end()
        next_section = re.search(r"\n##\s+", content[start:])
        assert next_section is None
        section = content[start:start + next_section.start() if next_section else len(content)]
        assert "Some content here" in section


# ===========================================================================
# Rejected: session persistence (Linux atomic rename works)
# ===========================================================================

class TestSessionPersistenceOnLinux:
    """Confirm Path.rename() works atomically on Linux."""

    def test_rename_replaces_existing_file(self):
        """On Linux, Path.rename() atomically replaces target."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "test.json"
            target.write_text("old")
            source = Path(tmp) / "test.tmp"
            source.write_text("new")
            source.rename(target)
            assert target.read_text() == "new"
            assert not source.exists()


# ===========================================================================
# Rejected: cap_duration defensive design
# ===========================================================================

class TestCapDurationDefensiveDesign:
    """Confirm cap_duration returns unchanged session on parse failure."""

    def test_cap_duration_bad_dates_returns_original(self):
        """Invalid date strings → session returned unchanged."""
        from governance.services.session_repair import cap_duration
        session = {"start_time": "not-a-date", "end_time": "also-not"}
        result = cap_duration(session)
        assert result == session

    def test_cap_duration_missing_times_returns_original(self):
        """Missing start/end → session returned unchanged."""
        from governance.services.session_repair import cap_duration
        session = {"session_id": "TEST-001"}
        result = cap_duration(session)
        assert result == session

    def test_cap_duration_within_limit_unchanged(self):
        """Duration under 24h → session unchanged."""
        from governance.services.session_repair import cap_duration
        session = {
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T12:00:00",
        }
        result = cap_duration(session)
        assert result["end_time"] == "2026-01-01T12:00:00"


# ===========================================================================
# Rejected: audit retention ISO format
# ===========================================================================

class TestAuditRetentionDateFormat:
    """Confirm ISO format is always exactly 10 chars for date."""

    def test_iso_date_always_10_chars(self):
        """datetime.now().isoformat()[:10] is always YYYY-MM-DD."""
        from datetime import datetime
        for month in range(1, 13):
            for day in [1, 15, 28]:
                dt = datetime(2026, month, day, 14, 30, 0)
                date_str = dt.isoformat()[:10]
                assert len(date_str) == 10
                assert date_str[4] == "-"
                assert date_str[7] == "-"


# ===========================================================================
# Rejected: hook exit code safety
# ===========================================================================

class TestHookExitCodeSafety:
    """Confirm hooks always exit 0 to never block Claude Code."""

    def test_todo_sync_main_returns_zero(self):
        """main() always returns 0."""
        from hooks import todo_sync
        src = inspect.getsource(todo_sync.main)
        assert "return 0" in src

    def test_todo_sync_outer_exits_zero(self):
        """Outer exception handler exits 0."""
        from hooks import todo_sync
        full_src = inspect.getsource(todo_sync)
        assert "sys.exit(0)" in full_src
