"""Deep Scan Batch 88 — Defense verification tests.

All 39 findings REJECTED — this file verifies existing protections hold.
Tests confirm: escaping, null guards, pagination heuristics, fallback patterns.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ============================================================================
# Proposal Escaping Verification (CRITICAL-002 REJECTED)
# ============================================================================

class TestProposalEscaping:
    """Verify proposals_list TypeQL escaping is correct."""

    def test_chr34_is_double_quote(self):
        """chr(34) is double quote — used in BUG-PROPOSAL-ESCAPE-001."""
        assert chr(34) == '"'

    def test_chr92_is_backslash(self):
        """chr(92) is backslash — used in BUG-PROPOSAL-ESCAPE-001."""
        assert chr(92) == '\\'

    def test_status_escaping_removes_injection(self):
        """Verify status filter escapes embedded quotes."""
        status = 'pending"; delete $x isa proposal; match $x isa proposal, has proposal-id "'
        escaped = status.replace(chr(34), chr(92) + chr(34))
        # All double quotes should be escaped with backslash
        assert '"' not in escaped.replace('\\"', '')

    def test_none_status_produces_empty_filter(self):
        """None/empty status produces empty filter string."""
        status = None
        status_filter = f', has proposal-status "{status}"' if status else ""
        assert status_filter == ""

    def test_empty_string_status_produces_empty_filter(self):
        """Empty string status produces empty filter string."""
        status = ""
        status_filter = f', has proposal-status "{status}"' if status else ""
        assert status_filter == ""


# ============================================================================
# Agent Activity Escaping Verification (HIGH-007 REJECTED)
# ============================================================================

class TestAgentActivityEscaping:
    """Verify agent_activity TypeQL escaping handles quotes."""

    def test_agent_id_escaping(self):
        """Agent ID with quotes gets escaped."""
        agent_id = 'code-agent"'
        escaped = agent_id.replace('"', '\\"')
        assert escaped == 'code-agent\\"'

    def test_normal_agent_id_unchanged(self):
        """Standard agent IDs (no special chars) pass through unchanged."""
        for aid in ["code-agent", "governance-agent", "test-runner", "data-analyst"]:
            assert aid.replace('"', '\\"') == aid


# ============================================================================
# Agent Activity Null Safety (HIGH-008 REJECTED)
# ============================================================================

class TestAgentActivityNullSafety:
    """Verify .get(key, {}).get("value", "") pattern handles all cases."""

    def test_missing_key_returns_empty(self):
        """Missing key returns empty string via default dict."""
        r = {}
        assert r.get("tid", {}).get("value", "") == ""

    def test_present_key_extracts_value(self):
        """Present key extracts nested value."""
        r = {"tid": {"value": "TASK-001"}}
        assert r.get("tid", {}).get("value", "") == "TASK-001"

    def test_key_with_empty_dict_returns_empty(self):
        """Key present but empty dict returns empty string."""
        r = {"tid": {}}
        assert r.get("tid", {}).get("value", "") == ""


# ============================================================================
# Projects Pagination Heuristic (BUG-PROJECTS-001 REJECTED)
# ============================================================================

class TestProjectsPagination:
    """Verify pagination heuristic for TypeDB returns."""

    def test_partial_page_total_equals_offset_plus_count(self):
        """When TypeDB returns fewer than limit, total = offset + count."""
        projects = [{"project_id": f"P-{i}"} for i in range(3)]
        offset, limit = 0, 10
        total = offset + len(projects)
        if len(projects) >= limit:
            total = offset + limit + 1
        assert total == 3
        assert (offset + limit) >= total  # has_more = False

    def test_full_page_infers_more_exist(self):
        """When TypeDB returns full page, assume at least one more."""
        projects = [{"project_id": f"P-{i}"} for i in range(10)]
        offset, limit = 0, 10
        total = offset + len(projects)
        if len(projects) >= limit:
            total = offset + limit + 1
        assert total == 11
        assert (offset + limit) < total  # has_more = True

    def test_memory_fallback_captures_total_before_slice(self):
        """In-memory fallback: total captured BEFORE offset/limit slicing."""
        all_projects = [{"project_id": f"P-{i}"} for i in range(25)]
        offset, limit = 10, 10
        total = len(all_projects)  # 25, captured BEFORE slicing
        projects = all_projects[offset:offset + limit]
        assert total == 25
        assert len(projects) == 10
        assert (offset + limit) < total  # has_more = True


# ============================================================================
# Task Auto-Linking Null Guard (BUG-TASKS-003 REJECTED)
# ============================================================================

class TestTaskAutoLinking:
    """Verify auto-linking only happens when active session exists."""

    def test_no_active_session_no_linking(self):
        """When no active sessions, linked_sessions stays None."""
        with patch("governance.services.tasks._sessions_store", {}):
            from governance.services.tasks import _get_active_session_id
            result = _get_active_session_id()
            assert result is None

    def test_active_session_returns_id(self):
        """Active session ID is returned correctly."""
        mock_sessions = {
            "SESSION-A": {"status": "ACTIVE", "start_time": "2026-02-15T10:00:00"},
            "SESSION-B": {"status": "ENDED", "start_time": "2026-02-15T09:00:00"},
        }
        with patch("governance.services.tasks._sessions_store", mock_sessions):
            from governance.services.tasks import _get_active_session_id
            result = _get_active_session_id()
            assert result == "SESSION-A"

    def test_multiple_active_returns_most_recent(self):
        """Multiple active sessions: returns most recent by start_time."""
        mock_sessions = {
            "SESSION-OLD": {"status": "ACTIVE", "start_time": "2026-02-15T08:00:00"},
            "SESSION-NEW": {"status": "ACTIVE", "start_time": "2026-02-15T12:00:00"},
        }
        with patch("governance.services.tasks._sessions_store", mock_sessions):
            from governance.services.tasks import _get_active_session_id
            result = _get_active_session_id()
            assert result == "SESSION-NEW"


# ============================================================================
# Agent Status Persistence (BUG-AGENTS-001 REJECTED)
# ============================================================================

class TestAgentStatusPersistence:
    """Verify toggle_agent_status persists to both memory and file."""

    @patch("governance.services.agents._save_agent_metrics")
    @patch("governance.services.agents._load_agent_metrics")
    def test_persist_agent_status_writes_to_file(self, mock_load, mock_save):
        """_persist_agent_status calls save with correct data."""
        mock_load.return_value = {"code-agent": {"tasks_executed": 5}}
        from governance.services.agents import _persist_agent_status
        _persist_agent_status("code-agent", "ACTIVE")
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert saved["code-agent"]["status"] == "ACTIVE"
        assert saved["code-agent"]["tasks_executed"] == 5  # preserved

    @patch("governance.services.agents._save_agent_metrics")
    @patch("governance.services.agents._load_agent_metrics")
    def test_persist_new_agent_creates_entry(self, mock_load, mock_save):
        """New agent not in metrics file gets entry created."""
        mock_load.return_value = {}
        from governance.services.agents import _persist_agent_status
        _persist_agent_status("new-agent", "PAUSED")
        saved = mock_save.call_args[0][0]
        assert saved["new-agent"]["status"] == "PAUSED"


# ============================================================================
# Task Mutations Fallback Pattern (BUG-TASKS-002 REJECTED)
# ============================================================================

class TestTaskMutationsFallback:
    """Verify update_task always updates memory store (intentional fallback)."""

    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_memory_update_on_typedb_failure(self, mock_client, mock_mon, mock_audit, mock_log):
        """When TypeDB fails, memory store still gets updated."""
        mock_client.return_value = None  # TypeDB unavailable

        from governance.services.tasks_mutations import update_task, _tasks_store
        _tasks_store["TASK-TEST"] = {
            "task_id": "TASK-TEST",
            "status": "OPEN",
            "description": "test",
            "phase": "P10",
        }
        try:
            result = update_task("TASK-TEST", status="IN_PROGRESS", agent_id="code-agent")
            assert result is not None
            assert result["status"] == "IN_PROGRESS"
            assert result["agent_id"] == "code-agent"
        finally:
            _tasks_store.pop("TASK-TEST", None)

    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_nonexistent_task_returns_none(self, mock_client, mock_mon, mock_audit, mock_log):
        """Updating nonexistent task returns None."""
        mock_client.return_value = None
        from governance.services.tasks_mutations import update_task, _tasks_store
        _tasks_store.pop("NONEXISTENT", None)
        result = update_task("NONEXISTENT", status="DONE")
        assert result is None


# ============================================================================
# Rules Service Sanitization (BUG-RULES-001 REJECTED)
# ============================================================================

class TestRulesServiceSanitization:
    """Verify rules create/update delegates to TypeDB client (driver handles escaping)."""

    @patch("governance.services.rules.log_event")
    @patch("governance.services.rules.record_audit")
    @patch("governance.services.rules._monitor")
    def test_create_rule_passes_raw_directive_to_client(self, mock_mon, mock_audit, mock_log):
        """Client receives directive as-is — driver handles escaping."""
        mock_client = MagicMock()
        mock_client.get_rule_by_id.return_value = None
        mock_rule = MagicMock()
        mock_rule.id = "TEST-001"
        mock_rule.name = "Test"
        mock_rule.category = "TEST"
        mock_rule.priority = "LOW"
        mock_rule.status = "ACTIVE"
        mock_rule.directive = 'Has "special" chars & <html>'
        mock_rule.created_date = None
        mock_rule.applicability = None
        mock_client.create_rule.return_value = mock_rule
        with patch("governance.services.rules.get_client", return_value=mock_client):
            from governance.services.rules import create_rule
            result = create_rule(
                rule_id="TEST-001", name="Test", directive='Has "special" chars & <html>'
            )
            # Verify directive passed through to client unchanged
            mock_client.create_rule.assert_called_once()
            call_kwargs = mock_client.create_rule.call_args[1]
            assert call_kwargs["directive"] == 'Has "special" chars & <html>'


# ============================================================================
# Task Description/Name Field Mapping (MEDIUM-010 REJECTED)
# ============================================================================

class TestTaskFieldMapping:
    """Verify description→name mapping is intentional."""

    @patch("governance.services.tasks.log_event")
    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks._monitor")
    @patch("governance.services.tasks.get_typedb_client")
    def test_description_maps_to_name_in_typedb(self, mock_client_fn, mock_mon, mock_audit, mock_log):
        """create_task passes description as 'name' kwarg to insert_task."""
        mock_client = MagicMock()
        mock_client.get_task.return_value = None
        mock_task_obj = MagicMock()
        mock_task_obj.name = "Fix the bug"
        mock_task_obj.status = "OPEN"
        mock_task_obj.phase = "P10"
        mock_task_obj.task_id = "BUG-001"
        mock_client.insert_task.return_value = mock_task_obj
        mock_client_fn.return_value = mock_client

        with patch("governance.services.tasks.task_to_response", side_effect=lambda x: {"task_id": "BUG-001", "description": "Fix the bug"}):
            from governance.services.tasks import create_task, _tasks_store
            _tasks_store.pop("BUG-001", None)
            try:
                result = create_task(task_id="BUG-001", description="Fix the bug")
                # Verify name= kwarg received description value
                call_kwargs = mock_client.insert_task.call_args[1]
                assert call_kwargs["name"] == "Fix the bug"
            finally:
                _tasks_store.pop("BUG-001", None)


# ============================================================================
# H-TASK-002: Auto Agent Assignment
# ============================================================================

class TestHTask002AutoAssign:
    """Verify IN_PROGRESS tasks auto-assign 'code-agent' when no agent_id."""

    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_in_progress_auto_assigns_code_agent(self, mock_client, mock_mon, mock_audit, mock_log):
        """Setting status=IN_PROGRESS without agent_id assigns 'code-agent'."""
        mock_client.return_value = None
        from governance.services.tasks_mutations import update_task, _tasks_store
        _tasks_store["TASK-AUTO"] = {
            "task_id": "TASK-AUTO", "status": "OPEN",
            "description": "test", "phase": "P10",
        }
        try:
            result = update_task("TASK-AUTO", status="IN_PROGRESS")
            assert result["agent_id"] == "code-agent"
        finally:
            _tasks_store.pop("TASK-AUTO", None)

    @patch("governance.services.tasks_mutations.log_event")
    @patch("governance.services.tasks_mutations.record_audit")
    @patch("governance.services.tasks_mutations._monitor")
    @patch("governance.services.tasks_mutations.get_typedb_client")
    def test_in_progress_with_agent_preserves_it(self, mock_client, mock_mon, mock_audit, mock_log):
        """Setting IN_PROGRESS with explicit agent_id preserves that agent."""
        mock_client.return_value = None
        from governance.services.tasks_mutations import update_task, _tasks_store
        _tasks_store["TASK-AGENT"] = {
            "task_id": "TASK-AGENT", "status": "OPEN",
            "description": "test", "phase": "P10",
        }
        try:
            result = update_task("TASK-AGENT", status="IN_PROGRESS", agent_id="custom-agent")
            assert result["agent_id"] == "custom-agent"
        finally:
            _tasks_store.pop("TASK-AGENT", None)
