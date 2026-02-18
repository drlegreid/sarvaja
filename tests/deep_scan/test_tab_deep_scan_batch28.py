"""
Unit tests for Tab Deep Scan Batch 28 — Governance services layer.

Covers: BUG-SESSION-002 (CC field fallback), BUG-TASK-003 (task fallback fields),
BUG-MONITOR-SILENT-001 (7x _monitor bare except:pass → logger.warning).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import logging
from unittest.mock import patch, MagicMock


# ── BUG-SESSION-002: CC fields in session fallback ───────────────────


class TestSessionCCFieldFallback:
    """update_session() fallback path must persist all 6 CC fields."""

    def test_fallback_updates_cc_session_uuid(self):
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-1"] = {"session_id": "S-1", "status": "ACTIVE"}
            try:
                result = sessions.update_session("S-1", cc_session_uuid="uuid-123")
                assert result is not None
                assert result["cc_session_uuid"] == "uuid-123"
            finally:
                sessions._sessions_store.pop("S-1", None)

    def test_fallback_updates_cc_project_slug(self):
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-2"] = {"session_id": "S-2", "status": "ACTIVE"}
            try:
                result = sessions.update_session("S-2", cc_project_slug="my-project")
                assert result["cc_project_slug"] == "my-project"
            finally:
                sessions._sessions_store.pop("S-2", None)

    def test_fallback_updates_cc_git_branch(self):
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-3"] = {"session_id": "S-3", "status": "ACTIVE"}
            try:
                result = sessions.update_session("S-3", cc_git_branch="feature/test")
                assert result["cc_git_branch"] == "feature/test"
            finally:
                sessions._sessions_store.pop("S-3", None)

    def test_fallback_updates_cc_tool_count(self):
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-4"] = {"session_id": "S-4", "status": "ACTIVE"}
            try:
                result = sessions.update_session("S-4", cc_tool_count=42)
                assert result["cc_tool_count"] == 42
            finally:
                sessions._sessions_store.pop("S-4", None)

    def test_fallback_updates_cc_thinking_chars(self):
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-5"] = {"session_id": "S-5", "status": "ACTIVE"}
            try:
                result = sessions.update_session("S-5", cc_thinking_chars=9000)
                assert result["cc_thinking_chars"] == 9000
            finally:
                sessions._sessions_store.pop("S-5", None)

    def test_fallback_updates_cc_compaction_count(self):
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-6"] = {"session_id": "S-6", "status": "ACTIVE"}
            try:
                result = sessions.update_session("S-6", cc_compaction_count=3)
                assert result["cc_compaction_count"] == 3
            finally:
                sessions._sessions_store.pop("S-6", None)

    def test_fallback_none_cc_fields_not_overwritten(self):
        """None CC fields should NOT overwrite existing values."""
        from governance.services import sessions
        with patch.object(sessions, 'get_typedb_client', return_value=None), \
             patch.object(sessions, 'record_audit'), \
             patch.object(sessions, '_monitor'), \
             patch.object(sessions, 'log_event'):
            sessions._sessions_store["S-7"] = {
                "session_id": "S-7", "status": "ACTIVE",
                "cc_session_uuid": "existing-uuid",
            }
            try:
                result = sessions.update_session("S-7", status="ENDED")
                assert result["cc_session_uuid"] == "existing-uuid"
            finally:
                sessions._sessions_store.pop("S-7", None)

    def test_has_bugfix_marker(self):
        from governance.services import sessions
        source = inspect.getsource(sessions)
        assert "BUG-SESSION-002" in source


# ── BUG-TASK-003: Incomplete fallback task creation ──────────────────


class TestTaskFallbackFields:
    """Fallback task creation in update_task must include all fields."""

    def test_fallback_includes_priority(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        start = source.index("# BUG-TASK-003")
        fn_src = source[start:start + 1200]
        assert "priority" in fn_src

    def test_fallback_includes_task_type(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        start = source.index("# BUG-TASK-003")
        fn_src = source[start:start + 1200]
        assert "task_type" in fn_src

    def test_fallback_includes_linked_rules(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        start = source.index("# BUG-TASK-003")
        fn_src = source[start:start + 1200]
        assert "linked_rules" in fn_src

    def test_fallback_includes_linked_sessions(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        start = source.index("# BUG-TASK-003")
        fn_src = source[start:start + 1200]
        assert "linked_sessions" in fn_src

    def test_fallback_includes_linked_documents(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        start = source.index("# BUG-TASK-003")
        fn_src = source[start:start + 1200]
        assert "linked_documents" in fn_src

    def test_has_bugfix_marker(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations)
        assert "BUG-TASK-003" in source


# ── BUG-MONITOR-SILENT-001: _monitor must log, not swallow ──────────


class TestMonitorLogging:
    """All 7 _monitor() functions must use logger.warning, not bare pass."""

    MONITOR_FILES = [
        ("governance.services.sessions", "session"),
        ("governance.services.rules", "rule"),
        ("governance.services.agents", "agent"),
        ("governance.services.tasks", "task"),
        ("governance.services.sessions_lifecycle", "session"),
        ("governance.services.tasks_mutations", "task"),
        ("governance.services.rules_relations", "rule"),
    ]

    def test_sessions_monitor_logs_warning(self):
        from governance.services import sessions
        source = inspect.getsource(sessions._monitor)
        assert "logger.warning" in source
        assert "except Exception:" not in source or "as e" in source

    def test_rules_monitor_logs_warning(self):
        from governance.services import rules
        source = inspect.getsource(rules._monitor)
        assert "logger.warning" in source

    def test_agents_monitor_logs_warning(self):
        from governance.services import agents
        source = inspect.getsource(agents._monitor)
        assert "logger.warning" in source

    def test_tasks_monitor_logs_warning(self):
        from governance.services import tasks
        source = inspect.getsource(tasks._monitor)
        assert "logger.warning" in source

    def test_sessions_lifecycle_monitor_logs_warning(self):
        from governance.services import sessions_lifecycle
        source = inspect.getsource(sessions_lifecycle._monitor)
        assert "logger.warning" in source

    def test_tasks_mutations_monitor_logs_warning(self):
        from governance.services import tasks_mutations
        source = inspect.getsource(tasks_mutations._monitor)
        assert "logger.warning" in source

    def test_rules_relations_monitor_logs_warning(self):
        from governance.services import rules_relations
        source = inspect.getsource(rules_relations._monitor)
        assert "logger.warning" in source

    def test_no_bare_except_pass_in_any_monitor(self):
        """No _monitor() should have bare 'except Exception: pass'."""
        for module_path, _ in self.MONITOR_FILES:
            parts = module_path.split(".")
            module = __import__(module_path, fromlist=[parts[-1]])
            source = inspect.getsource(module._monitor)
            # Should not have bare pass after except
            lines = source.splitlines()
            for i, line in enumerate(lines):
                if "except Exception" in line:
                    # Next non-empty line should NOT be just 'pass'
                    for j in range(i + 1, min(i + 3, len(lines))):
                        stripped = lines[j].strip()
                        if stripped == "pass":
                            raise AssertionError(
                                f"{module_path}._monitor has bare 'except: pass'"
                            )
                        if stripped and not stripped.startswith("#"):
                            break

    def test_monitor_logs_on_exception(self):
        """Verify _monitor actually produces a log when the import fails."""
        from governance.services import sessions
        with patch("governance.mcp_tools.common.log_monitor_event",
                   side_effect=RuntimeError("test-fail")), \
             patch.object(sessions.logger, "warning") as mock_warn:
            sessions._monitor("test", "S-1")
            mock_warn.assert_called_once()
            assert "S-1" in mock_warn.call_args[0][0]

    def test_bugfix_marker_present(self):
        from governance.services import sessions
        source = inspect.getsource(sessions._monitor)
        assert "BUG-MONITOR-SILENT-001" in source


# ── Cross-cutting: update_session signature ──────────────────────────


class TestUpdateSessionSignature:
    """update_session must accept all CC parameters."""

    def test_accepts_all_cc_params(self):
        from governance.services.sessions import update_session
        sig = inspect.signature(update_session)
        cc_params = [
            "cc_session_uuid", "cc_project_slug", "cc_git_branch",
            "cc_tool_count", "cc_thinking_chars", "cc_compaction_count",
        ]
        for p in cc_params:
            assert p in sig.parameters, f"Missing parameter: {p}"

    def test_cc_params_default_to_none(self):
        from governance.services.sessions import update_session
        sig = inspect.signature(update_session)
        cc_params = [
            "cc_session_uuid", "cc_project_slug", "cc_git_branch",
            "cc_tool_count", "cc_thinking_chars", "cc_compaction_count",
        ]
        for p in cc_params:
            assert sig.parameters[p].default is None, \
                f"{p} should default to None"
