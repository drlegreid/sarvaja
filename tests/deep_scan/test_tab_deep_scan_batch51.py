"""
Batch 51 — Deep Scan: Session stores + repair + parser observability.

Fixes verified:
- BUG-STORE-LIST-NULL-001: session_to_response() list fields use `or []`
- BUG-REPAIR-INCOMPLETE-001: apply_repair() now handles timestamp + duration fixes
- BUG-PARSER-SILENT-001: JSON decode errors logged instead of silently skipped
"""
import ast
import inspect
import textwrap
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ===========================================================================
# BUG-STORE-LIST-NULL-001: List fields in session_to_response
# ===========================================================================

class TestSessionToResponseListFields:
    """Verify session_to_response uses `or []` for list fields."""

    def test_evidence_files_uses_or_empty_list(self):
        """evidence_files field must use `or []`."""
        from governance.stores import helpers
        src = inspect.getsource(helpers.session_to_response)
        assert "evidence_files=session.evidence_files or []" in src

    def test_linked_rules_uses_or_empty_list(self):
        """linked_rules_applied field must use `or []`."""
        from governance.stores import helpers
        src = inspect.getsource(helpers.session_to_response)
        assert "linked_rules_applied=session.linked_rules_applied or []" in src

    def test_linked_decisions_uses_or_empty_list(self):
        """linked_decisions field must use `or []`."""
        from governance.stores import helpers
        src = inspect.getsource(helpers.session_to_response)
        assert "linked_decisions=session.linked_decisions or []" in src

    def _make_mock_session(self, **overrides):
        """Create a mock TypeDB session with all required fields."""
        mock = MagicMock()
        mock.id = overrides.get("id", "SESSION-2026-02-15-TEST")
        mock.started_at = overrides.get("started_at", datetime.now())
        mock.completed_at = overrides.get("completed_at", None)
        mock.status = overrides.get("status", "COMPLETED")
        mock.tasks_completed = overrides.get("tasks_completed", 0)
        mock.agent_id = overrides.get("agent_id", "code-agent")
        mock.description = overrides.get("description", "Test session")
        mock.file_path = overrides.get("file_path", None)
        mock.evidence_files = overrides.get("evidence_files", None)
        mock.linked_rules_applied = overrides.get("linked_rules_applied", None)
        mock.linked_decisions = overrides.get("linked_decisions", None)
        # CC fields must be explicit to avoid MagicMock auto-generation
        mock.cc_session_uuid = overrides.get("cc_session_uuid", None)
        mock.cc_project_slug = overrides.get("cc_project_slug", None)
        mock.cc_git_branch = overrides.get("cc_git_branch", None)
        mock.cc_tool_count = overrides.get("cc_tool_count", None)
        mock.cc_thinking_chars = overrides.get("cc_thinking_chars", None)
        mock.cc_compaction_count = overrides.get("cc_compaction_count", None)
        mock.project_id = overrides.get("project_id", None)
        return mock

    def test_none_list_fields_become_empty_list(self):
        """When TypeDB returns None for list fields, response should have []."""
        from governance.stores.helpers import session_to_response
        mock_session = self._make_mock_session(
            evidence_files=None,
            linked_rules_applied=None,
            linked_decisions=None,
        )
        result = session_to_response(mock_session)
        assert result.evidence_files == []
        assert result.linked_rules_applied == []
        assert result.linked_decisions == []

    def test_populated_list_fields_preserved(self):
        """When list fields have data, they should be preserved."""
        from governance.stores.helpers import session_to_response
        mock_session = self._make_mock_session(
            evidence_files=["file1.md", "file2.md"],
            linked_rules_applied=["RULE-001"],
            linked_decisions=["DEC-001"],
        )
        result = session_to_response(mock_session)
        assert result.evidence_files == ["file1.md", "file2.md"]
        assert result.linked_rules_applied == ["RULE-001"]
        assert result.linked_decisions == ["DEC-001"]


# ===========================================================================
# BUG-REPAIR-INCOMPLETE-001: apply_repair handles timestamps + duration
# ===========================================================================

class TestRepairApplyTimestampFixes:
    """Verify apply_repair() now handles timestamp and duration fixes."""

    def test_source_handles_timestamp_fixes(self):
        """apply_repair must check for 'timestamp' in fixes."""
        from governance.services import session_repair
        src = inspect.getsource(session_repair.apply_repair)
        assert '"timestamp" in fixes' in src

    def test_source_handles_duration_fixes(self):
        """apply_repair must check for 'duration' in fixes."""
        from governance.services import session_repair
        src = inspect.getsource(session_repair.apply_repair)
        assert '"duration" in fixes' in src

    def test_timestamp_fix_passes_start_end_to_update(self):
        """Timestamp fixes should pass start_time and end_time to update_session."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "SESSION-2026-01-01-TEST",
            "fixes": {
                "timestamp": {
                    "start": "2026-01-01T10:00:00",
                    "end": "2026-01-01T11:00:00",
                }
            }
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(plan_item, dry_run=False)
            mock_update.assert_called_once_with(
                "SESSION-2026-01-01-TEST",
                start_time="2026-01-01T10:00:00",
                end_time="2026-01-01T11:00:00",
            )
            assert result["applied"] is True

    def test_duration_fix_passes_end_time_to_update(self):
        """Duration fixes should pass capped end_time to update_session."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "SESSION-2026-01-01-LONG",
            "fixes": {
                "duration": {
                    "end_time": "2026-01-02T10:00:00",
                }
            }
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(plan_item, dry_run=False)
            mock_update.assert_called_once_with(
                "SESSION-2026-01-01-LONG",
                end_time="2026-01-02T10:00:00",
            )
            assert result["applied"] is True

    def test_combined_agent_and_timestamp_fix(self):
        """Both agent_id and timestamp fixes should be applied together."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "SESSION-2026-01-01-COMBO",
            "fixes": {
                "agent_id": "code-agent",
                "timestamp": {
                    "start": "2026-01-01T09:00:00",
                    "end": "2026-01-01T10:00:00",
                }
            }
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(plan_item, dry_run=False)
            mock_update.assert_called_once_with(
                "SESSION-2026-01-01-COMBO",
                agent_id="code-agent",
                start_time="2026-01-01T09:00:00",
                end_time="2026-01-01T10:00:00",
            )
            assert result["applied"] is True

    def test_dry_run_skips_application(self):
        """dry_run=True should not call update_session."""
        from governance.services.session_repair import apply_repair
        plan_item = {
            "session_id": "SESSION-2026-01-01-DRY",
            "fixes": {"agent_id": "code-agent", "timestamp": {"start": "x", "end": "y"}}
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(plan_item, dry_run=True)
            mock_update.assert_not_called()
            assert result["dry_run"] is True

    def test_empty_fixes_returns_no_changes(self):
        """Empty fixes dict should return no_changes=True."""
        from governance.services.session_repair import apply_repair
        plan_item = {"session_id": "SESSION-2026-01-01-EMPTY", "fixes": {}}
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(plan_item, dry_run=False)
            mock_update.assert_not_called()
            assert result.get("no_changes") is True


# ===========================================================================
# BUG-PARSER-SILENT-001: JSON decode logging
# ===========================================================================

class TestParserJsonDecodeLogging:
    """Verify parser logs malformed JSON lines instead of silently skipping."""

    def test_parse_log_file_has_logger_import(self):
        """parser.py must import logging module."""
        from governance.session_metrics import parser
        assert hasattr(parser, 'logger'), "parser.py must have a logger attribute"

    def test_parse_log_file_logs_json_errors(self):
        """parse_log_file should call logger.debug on JSONDecodeError."""
        from governance.session_metrics import parser
        src = inspect.getsource(parser.parse_log_file)
        assert "logger.debug" in src, "Must log malformed JSON lines"
        assert "JSONDecodeError" in src or "json.JSONDecodeError" in src

    def test_parse_log_file_extended_logs_json_errors(self):
        """parse_log_file_extended should also log JSONDecodeError."""
        from governance.session_metrics import parser
        src = inspect.getsource(parser.parse_log_file_extended)
        assert "logger.debug" in src, "Extended parser must also log malformed JSON"

    def test_malformed_line_logged_and_skipped(self):
        """Malformed JSON line should be logged and skipped, not crash."""
        import tempfile, os
        from governance.session_metrics.parser import parse_log_file

        # Create a temp JSONL with one bad line and one good line
        content = 'NOT VALID JSON\n{"timestamp": "2026-02-15T10:00:00Z", "type": "assistant", "message": {"content": []}}\n'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(content)
            tmp_path = f.name

        try:
            with patch("governance.session_metrics.parser.logger") as mock_logger:
                entries = list(parse_log_file(tmp_path))
                # Should have logged the bad line
                mock_logger.debug.assert_called()
                # Should still parse the good line (1 entry)
                assert len(entries) == 1
        finally:
            os.unlink(tmp_path)


# ===========================================================================
# Cross-layer consistency: dual conversion sync
# ===========================================================================

class TestDualConversionConsistency:
    """Verify session_to_response and _session_to_dict handle list fields identically."""

    def test_both_functions_use_or_empty_for_evidence(self):
        """Both conversion functions must use `or []` for evidence_files."""
        from governance.stores import helpers
        from governance.stores import typedb_access
        helpers_src = inspect.getsource(helpers.session_to_response)
        typedb_src = inspect.getsource(typedb_access._session_to_dict)
        assert "or []" in helpers_src, "helpers must use or [] for list fields"
        assert "or []" in typedb_src, "typedb_access must use or [] for list fields"

    def test_repair_uses_module_level_logger(self):
        """apply_repair should use module-level logger, not inline import."""
        from governance.services import session_repair
        src = inspect.getsource(session_repair.apply_repair)
        # Should NOT have inline `import logging as _log`
        assert "import logging as _log" not in src, "Should use module-level logger"
