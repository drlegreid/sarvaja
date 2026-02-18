"""
Batch 294-297 — Deep Scan: Routes, Services, MCP Tools, TypeDB Queries, DSM Nodes.

Fixes verified:
- BUG-294-OBS-001: Path traversal guard on lock resource parameter
- BUG-294-OBS-002: Lock timeout upper bound (1-60s)
- BUG-294-OBS-003: Heartbeat status/agent_type whitelist + current_task cap
- BUG-294-SES-001: Date validation for date_from/date_to filters
- BUG-294-SES-002: _ensure_response uses sentinel, not datetime.now(); no source mutation
- BUG-295-SES-001: Service-layer bounds on limit/offset
- BUG-295-SES-002: Search string length cap
- BUG-296-SL-001: TypeQL newline escaping in sessions_linking
- BUG-296-RQ-001: Consistent response schema (dict not bare array)
- BUG-297-REL-001: Self-linking guard (parent + blocking)
- BUG-297-STS-001: Status/resolution enum validation
- BUG-297-STS-002: Guard None current.status to prevent dual attributes
- BUG-297-NOD-001: state.get() prevents KeyError on missing keys

Triage summary: 71 findings → 12 confirmed HIGH, 59 rejected/deferred.
"""
import inspect
import re
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# BUG-294-OBS-001: Path traversal guard on lock resource
# ===========================================================================

class TestLockResourceValidation:
    """Verify lock acquire validates resource name."""

    def test_source_has_regex_check(self):
        """acquire_lock must validate resource with regex."""
        from governance.routes.agents.observability import acquire_lock
        src = inspect.getsource(acquire_lock)
        assert "re.match" in src or "_re.match" in src

    def test_source_rejects_path_traversal(self):
        """Must reject resource names with path traversal chars."""
        from governance.routes.agents.observability import acquire_lock
        src = inspect.getsource(acquire_lock)
        assert "Invalid resource name" in src

    def test_timeout_capped(self):
        """Timeout must be capped to prevent blocking."""
        from governance.routes.agents.observability import acquire_lock
        src = inspect.getsource(acquire_lock)
        # BUG-294-OBS-002: Cap timeout
        assert "min(60" in src


# ===========================================================================
# BUG-294-OBS-003: Heartbeat input validation
# ===========================================================================

class TestHeartbeatValidation:
    """Verify heartbeat validates status and agent_type."""

    def test_status_whitelist(self):
        """Heartbeat must whitelist valid statuses."""
        from governance.routes.agents.observability import agent_heartbeat
        src = inspect.getsource(agent_heartbeat)
        assert "_valid_statuses" in src
        assert '"active"' in src

    def test_agent_type_fallback(self):
        """Invalid agent_type must fall back to 'unknown'."""
        from governance.routes.agents.observability import agent_heartbeat
        src = inspect.getsource(agent_heartbeat)
        assert "_valid_types" in src
        assert 'agent_type = "unknown"' in src

    def test_current_task_length_cap(self):
        """current_task must be capped at 512 chars."""
        from governance.routes.agents.observability import agent_heartbeat
        src = inspect.getsource(agent_heartbeat)
        assert "512" in src


# ===========================================================================
# BUG-294-SES-001: Date validation in sessions route
# ===========================================================================

class TestSessionDateValidation:
    """Verify date_from/date_to are validated."""

    def test_source_validates_dates(self):
        """list_sessions must validate date format."""
        from governance.routes.sessions.crud import list_sessions
        src = inspect.getsource(list_sessions)
        assert "fromisoformat" in src

    def test_source_checks_date_order(self):
        """Must check date_from <= date_to."""
        from governance.routes.sessions.crud import list_sessions
        src = inspect.getsource(list_sessions)
        assert "date_from > date_to" in src or "date_from must not be after" in src

    def test_invalid_date_format_message(self):
        """Error message must mention YYYY-MM-DD."""
        from governance.routes.sessions.crud import list_sessions
        src = inspect.getsource(list_sessions)
        assert "YYYY-MM-DD" in src


# ===========================================================================
# BUG-294-SES-002: _ensure_response no source mutation
# ===========================================================================

class TestEnsureResponseSafety:
    """Verify _ensure_response does not mutate source or fabricate timestamps."""

    def test_uses_sentinel_not_now(self):
        """Must use sentinel timestamp, not datetime.now()."""
        from governance.routes.sessions.crud import _ensure_response
        src = inspect.getsource(_ensure_response)
        assert "1970-01-01T00:00:00" in src

    def test_copies_dict(self):
        """Must copy dict before modifying."""
        from governance.routes.sessions.crud import _ensure_response
        src = inspect.getsource(_ensure_response)
        assert "dict(result)" in src

    def test_no_datetime_now_call(self):
        """Must not call datetime.now() for start_time (comments ok)."""
        from governance.routes.sessions.crud import _ensure_response
        src = inspect.getsource(_ensure_response)
        # Check that datetime.now() is NOT used as actual code (only in comments)
        for line in src.split('\n'):
            stripped = line.split('#')[0]  # Remove comments
            assert "datetime.now()" not in stripped, f"Found datetime.now() in code: {line.strip()}"


# ===========================================================================
# BUG-295-SES-001: Service-layer bounds on limit/offset
# ===========================================================================

class TestServiceLayerBounds:
    """Verify sessions service enforces bounds."""

    def test_offset_clamped(self):
        """offset must be >= 0 at service layer."""
        from governance.services.sessions import list_sessions
        src = inspect.getsource(list_sessions)
        assert "max(0, offset)" in src

    def test_limit_capped(self):
        """limit must be capped at 500 at service layer."""
        from governance.services.sessions import list_sessions
        src = inspect.getsource(list_sessions)
        assert "min(limit, 500)" in src

    def test_search_capped(self):
        """Search string must be capped at 500 chars."""
        from governance.services.sessions import list_sessions
        src = inspect.getsource(list_sessions)
        assert "search[:500]" in src


# ===========================================================================
# BUG-296-SL-001: TypeQL newline escaping in sessions_linking
# ===========================================================================

class TestSessionLinkingEscaping:
    """Verify sessions_linking escapes newlines in TypeQL."""

    def test_newline_escape(self):
        """session_get_tasks must escape \\n in session_id."""
        from governance.mcp_tools.sessions_linking import register_session_linking_tools
        src = inspect.getsource(register_session_linking_tools)
        assert "replace('\\n'" in src

    def test_carriage_return_escape(self):
        """Must also escape \\r."""
        from governance.mcp_tools.sessions_linking import register_session_linking_tools
        src = inspect.getsource(register_session_linking_tools)
        assert "replace('\\r'" in src

    def test_tab_escape(self):
        """Must also escape \\t."""
        from governance.mcp_tools.sessions_linking import register_session_linking_tools
        src = inspect.getsource(register_session_linking_tools)
        assert "replace('\\t'" in src


# ===========================================================================
# BUG-296-RQ-001: Consistent response schema
# ===========================================================================

class TestRulesQueryResponseSchema:
    """Verify rules_query returns consistent dict format."""

    def test_typedb_path_returns_dict(self):
        """TypeDB success path must return dict with 'rules' key, not bare array."""
        from governance.mcp_tools.rules_query import register_rule_query_tools
        src = inspect.getsource(register_rule_query_tools)
        # Find the TypeDB success return
        assert '"rules":' in src
        assert '"count":' in src
        assert '"source": "typedb"' in src

    def test_no_bare_array_return(self):
        """Must not return format_mcp_result([...]) bare array."""
        from governance.mcp_tools.rules_query import register_rule_query_tools
        src = inspect.getsource(register_rule_query_tools)
        # The old pattern was: format_mcp_result([asdict(r) for r in rules])
        # New: format_mcp_result({"rules": [...], "count": ..., "source": "typedb"})
        lines = src.split('\n')
        for line in lines:
            if 'format_mcp_result([asdict' in line and '#' not in line.split('format_mcp_result')[0]:
                pytest.fail(f"Found bare array return: {line.strip()}")


# ===========================================================================
# BUG-297-REL-001: Self-linking guard
# ===========================================================================

class TestSelfLinkingGuard:
    """Verify task relationship operations prevent self-linking."""

    def test_parent_self_link_guard(self):
        """link_parent_task must reject child == parent."""
        from governance.typedb.queries.tasks.relationships import TaskRelationshipOperations
        src = inspect.getsource(TaskRelationshipOperations.link_parent_task)
        assert "child_task_id == parent_task_id" in src
        assert "return False" in src

    def test_blocking_self_link_guard(self):
        """link_blocking_task must reject blocker == blocked."""
        from governance.typedb.queries.tasks.relationships import TaskRelationshipOperations
        src = inspect.getsource(TaskRelationshipOperations.link_blocking_task)
        assert "blocking_task_id == blocked_task_id" in src
        assert "return False" in src

    def test_guard_comes_before_typedb(self):
        """Self-link guard must come before TypeDB transaction."""
        from governance.typedb.queries.tasks.relationships import TaskRelationshipOperations
        src = inspect.getsource(TaskRelationshipOperations.link_parent_task)
        guard_pos = src.find("child_task_id == parent_task_id")
        typedb_pos = src.find("TransactionType.WRITE")
        assert guard_pos > 0 and guard_pos < typedb_pos


# ===========================================================================
# BUG-297-STS-001: Status/resolution enum validation
# ===========================================================================

class TestStatusEnumValidation:
    """Verify update_task_status validates status and resolution."""

    def test_valid_statuses_defined(self):
        """Must have _VALID_STATUSES allowlist."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "_VALID_STATUSES" in src
        assert '"OPEN"' in src
        assert '"IN_PROGRESS"' in src
        assert '"DONE"' in src
        assert '"CLOSED"' in src

    def test_valid_resolutions_defined(self):
        """Must have _VALID_RESOLUTIONS allowlist."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "_VALID_RESOLUTIONS" in src
        assert '"NONE"' in src
        assert '"IMPLEMENTED"' in src
        assert '"VALIDATED"' in src

    def test_invalid_status_returns_none(self):
        """Invalid status must return None without hitting TypeDB."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        # Find the validation block
        idx = src.index("_VALID_STATUSES")
        block = src[idx:idx + 200]
        assert "return None" in block

    def test_invalid_resolution_returns_none(self):
        """Invalid resolution must return None."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        idx = src.index("_VALID_RESOLUTIONS")
        block = src[idx:idx + 300]
        assert "return None" in block


# ===========================================================================
# BUG-297-STS-002: Guard None current.status
# ===========================================================================

class TestNoneStatusGuard:
    """Verify status delete is skipped when current.status is None."""

    def test_status_delete_guarded(self):
        """Delete of old status must be guarded by 'if current.status'."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        assert "if current.status:" in src

    def test_no_empty_string_delete(self):
        """Must not delete status with empty-string match."""
        from governance.typedb.queries.tasks.status import update_task_status
        src = inspect.getsource(update_task_status)
        # The old pattern was: (current.status or "").replace(...)
        assert '(current.status or "")' not in src


# ===========================================================================
# BUG-297-NOD-001: state.get() prevents KeyError
# ===========================================================================

class TestNodeKeyErrorPrevention:
    """Verify DSP nodes use state.get() instead of state['key']."""

    def _get_all_node_source(self):
        from governance.dsm.langgraph.nodes_execution import (
            optimize_node, validate_node, dream_node, report_node
        )
        return (
            inspect.getsource(optimize_node)
            + inspect.getsource(validate_node)
            + inspect.getsource(dream_node)
            + inspect.getsource(report_node)
        )

    def test_no_bare_cycle_id_access(self):
        """Must not have state['cycle_id'] (bare dict access)."""
        src = self._get_all_node_source()
        # Should use state.get('cycle_id', ...) not state['cycle_id']
        assert "state['cycle_id']" not in src
        assert 'state["cycle_id"]' not in src

    def test_no_bare_phases_completed_access(self):
        """Must not have state['phases_completed'] (bare dict access)."""
        src = self._get_all_node_source()
        assert "state['phases_completed']" not in src
        assert 'state["phases_completed"]' not in src

    def test_uses_get_with_default(self):
        """Must use state.get('cycle_id', 'UNKNOWN')."""
        src = self._get_all_node_source()
        assert "state.get('cycle_id', 'UNKNOWN')" in src or 'state.get("cycle_id", "UNKNOWN")' in src


# ===========================================================================
# Cross-batch: Import verification
# ===========================================================================

class TestBatch294Imports:
    """Verify all fixed modules import cleanly."""

    def test_observability_routes(self):
        from governance.routes.agents.observability import acquire_lock, agent_heartbeat
        assert callable(acquire_lock)
        assert callable(agent_heartbeat)

    def test_session_crud_routes(self):
        from governance.routes.sessions.crud import list_sessions, _ensure_response
        assert callable(list_sessions)
        assert callable(_ensure_response)

    def test_sessions_service(self):
        from governance.services.sessions import list_sessions
        assert callable(list_sessions)

    def test_sessions_linking(self):
        from governance.mcp_tools.sessions_linking import register_session_linking_tools
        assert callable(register_session_linking_tools)

    def test_rules_query(self):
        from governance.mcp_tools.rules_query import register_rule_query_tools
        assert callable(register_rule_query_tools)

    def test_task_relationships(self):
        from governance.typedb.queries.tasks.relationships import TaskRelationshipOperations
        assert hasattr(TaskRelationshipOperations, 'link_parent_task')
        assert hasattr(TaskRelationshipOperations, 'link_blocking_task')

    def test_task_status(self):
        from governance.typedb.queries.tasks.status import update_task_status
        assert callable(update_task_status)

    def test_nodes_execution(self):
        from governance.dsm.langgraph.nodes_execution import (
            optimize_node, validate_node, dream_node, report_node
        )
        assert callable(optimize_node)
        assert callable(validate_node)
        assert callable(dream_node)
        assert callable(report_node)
