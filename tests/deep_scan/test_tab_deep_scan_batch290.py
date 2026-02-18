"""
Batch 290-293 — Deep Scan: UI views, stores, vector store, workspace scanner, session sync.

Fixes verified:
- BUG-290-EXEC-001: task_execution_log null guard before .length access
- BUG-290-EXEC-002: selected_task null guard on click handler
- BUG-290-TC-001: Dynamic Vue key binding for expansion panels
- BUG-290-PROP-001: Threshold null guard prevents NaN rendering
- BUG-290-PROP-002: proposal_result field guards on error path
- BUG-290-PROP-003: Dynamic key binding for proposal_history list
- BUG-291-AUD-001: .tmp file cleanup on audit save failure
- BUG-291-TDB-001: None guard on _task_to_dict input
- BUG-292-VEC-001: search_by_source connection guard
- BUG-293-SYN-001: _esc() None guard for decision/task fields
- BUG-293-SYN-002: Duplicate relation guard before insert
- BUG-293-WSC-001: Path traversal guard on parse functions

Triage summary: 63 findings → 11 confirmed HIGH, 52 rejected/deferred.
"""
import inspect
import os
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# BUG-290-EXEC-001: task_execution_log null guard
# ===========================================================================

class TestExecutionLogNullGuard:
    """Verify task_execution_log has null guard before .length access."""

    def _get_source(self):
        from agent.governance_ui.views.tasks.execution import build_execution_timeline
        return inspect.getsource(build_execution_timeline)

    def test_timeline_has_null_guard(self):
        """Timeline v_if must use (task_execution_log || []).length pattern."""
        src = self._get_source()
        assert "(task_execution_log || [])" in src

    def test_no_bare_length_access(self):
        """Must not have bare task_execution_log.length without guard."""
        src = self._get_source()
        # Check no bare access (must have || [] before .length)
        assert "task_execution_log.length" not in src

    def test_empty_state_guard(self):
        """Empty state message must also use null guard."""
        from agent.governance_ui.views.tasks.execution import build_task_execution_log
        src = inspect.getsource(build_task_execution_log)
        assert "(task_execution_log || [])" in src


# ===========================================================================
# BUG-290-EXEC-002: selected_task null guard on click
# ===========================================================================

class TestSelectedTaskNullGuard:
    """Verify selected_task click handler has null guard."""

    def test_click_handler_has_guard(self):
        """Click handler must check selected_task before accessing task_id."""
        from agent.governance_ui.views.tasks.execution import build_task_execution_log
        src = inspect.getsource(build_task_execution_log)
        assert "selected_task && trigger" in src

    def test_no_unguarded_selected_task_access(self):
        """Must not have trigger directly accessing selected_task without guard."""
        from agent.governance_ui.views.tasks.execution import build_task_execution_log
        src = inspect.getsource(build_task_execution_log)
        # The trigger call should have a guard before it
        idx = src.find("trigger('load_task_execution'")
        assert idx > 0
        # Check that "selected_task &&" appears before the trigger
        block = src[max(0, idx - 100):idx]
        assert "selected_task &&" in block


# ===========================================================================
# BUG-290-TC-001: Dynamic Vue key binding for expansion panels
# ===========================================================================

class TestToolCallsDynamicKey:
    """Verify expansion panels use dynamic :key binding."""

    def test_tool_calls_panel_dynamic_key(self):
        """Tool calls expansion panel must use :key not static key."""
        from agent.governance_ui.views.sessions.tool_calls import build_tool_calls_card
        src = inspect.getsource(build_tool_calls_card)
        assert '":key": "idx"' in src or '":key"' in src

    def test_no_static_key_tuple(self):
        """Must not have static key=('idx',) pattern."""
        from agent.governance_ui.views.sessions.tool_calls import build_tool_calls_card
        src = inspect.getsource(build_tool_calls_card)
        assert 'key=("idx",)' not in src

    def test_thinking_panel_dynamic_key(self):
        """Thinking items expansion panel must also use dynamic key."""
        from agent.governance_ui.views.sessions.tool_calls import _build_thinking_items_card
        src = inspect.getsource(_build_thinking_items_card)
        assert '":key"' in src
        assert 'key=("idx",)' not in src


# ===========================================================================
# BUG-290-PROP-001: Threshold null guard prevents NaN
# ===========================================================================

class TestThresholdNullGuard:
    """Verify thresholds use || 0 guard to prevent NaN rendering."""

    def _get_source(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_graph_panel
        return inspect.getsource(build_proposal_graph_panel)

    def test_quorum_has_null_guard(self):
        """Quorum threshold must use || 0 guard."""
        src = self._get_source()
        assert "quorum || 0" in src

    def test_approval_has_null_guard(self):
        """Approval threshold must use || 0 guard."""
        src = self._get_source()
        assert "approval || 0" in src

    def test_dispute_has_null_guard(self):
        """Dispute threshold must use || 0 guard."""
        src = self._get_source()
        assert "dispute || 0" in src

    def test_all_use_toFixed(self):
        """All thresholds must use .toFixed(0) for consistent display."""
        src = self._get_source()
        assert src.count("toFixed(0)") >= 3


# ===========================================================================
# BUG-290-PROP-002: proposal_result field guards on error path
# ===========================================================================

class TestProposalResultFieldGuards:
    """Verify proposal_result fields have null guards for error path."""

    def _get_source(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_form
        return inspect.getsource(build_proposal_form)

    def test_proposal_id_guarded(self):
        """proposal_id must have || 'N/A' guard."""
        src = self._get_source()
        assert "proposal_id || 'N/A'" in src

    def test_impact_score_guarded(self):
        """impact_score must have guard."""
        src = self._get_source()
        assert "impact_score || 'N/A'" in src

    def test_risk_level_guarded(self):
        """risk_level must have guard."""
        src = self._get_source()
        assert "risk_level || 'N/A'" in src

    def test_decision_reasoning_guarded(self):
        """decision_reasoning must have guard."""
        src = self._get_source()
        assert "decision_reasoning || ''" in src


# ===========================================================================
# BUG-290-PROP-003: Dynamic key binding for proposal_history
# ===========================================================================

class TestProposalHistoryDynamicKey:
    """Verify proposal_history list uses dynamic key binding."""

    def test_dynamic_key_with_proposal_id(self):
        """Proposal history list must use dynamic :key with proposal_id."""
        from agent.governance_ui.views.workflow_proposals import build_proposal_history
        src = inspect.getsource(build_proposal_history)
        assert '":key"' in src
        assert "p.proposal_id" in src

    def test_no_static_key_string(self):
        """Must not have static key='idx' pattern."""
        from agent.governance_ui.views.workflow_proposals import build_proposal_history
        src = inspect.getsource(build_proposal_history)
        # Check no static key="idx" (without colon)
        lines = src.split('\n')
        for line in lines:
            if 'key=' in line and '":key"' not in line and '#' not in line.split('key=')[0]:
                assert ':key' in line or 'proposal_id' in line, f"Static key found: {line.strip()}"


# ===========================================================================
# BUG-291-AUD-001: .tmp file cleanup on audit save failure
# ===========================================================================

class TestAuditTmpCleanup:
    """Verify .tmp file is cleaned up on audit save failure."""

    def test_unlink_in_save_error_path(self):
        """_save_audit_store must unlink .tmp on failure."""
        from governance.stores.audit import _save_audit_store
        src = inspect.getsource(_save_audit_store)
        idx = src.index("BUG-291-AUD-001")
        block = src[idx:idx + 200]
        assert "unlink" in block
        assert "missing_ok=True" in block

    def test_cleanup_before_log_warning(self):
        """Cleanup must happen before the warning log."""
        from governance.stores.audit import _save_audit_store
        src = inspect.getsource(_save_audit_store)
        unlink_pos = src.find("unlink(missing_ok=True)")
        log_pos = src.find("Failed to save audit store")
        assert unlink_pos > 0
        assert log_pos > 0
        assert unlink_pos < log_pos


# ===========================================================================
# BUG-291-TDB-001: None guard on _task_to_dict
# ===========================================================================

class TestTaskToDictNoneGuard:
    """Verify _task_to_dict handles None task."""

    def test_none_raises_value_error(self):
        """_task_to_dict must raise ValueError for None task."""
        from governance.stores.typedb_access import _task_to_dict
        with pytest.raises(ValueError, match="Cannot convert None"):
            _task_to_dict(None)

    def test_source_has_none_check(self):
        """Source must have 'if task is None' guard."""
        from governance.stores.typedb_access import _task_to_dict
        src = inspect.getsource(_task_to_dict)
        assert "task is None" in src

    def test_uses_getattr_for_id(self):
        """Must use getattr for task.id to handle partial entities."""
        from governance.stores.typedb_access import _task_to_dict
        src = inspect.getsource(_task_to_dict)
        assert "getattr(task, 'id'" in src


# ===========================================================================
# BUG-292-VEC-001: search_by_source connection guard
# ===========================================================================

class TestVectorStoreSearchGuard:
    """Verify search_by_source has connection guard."""

    def test_source_has_connection_guard(self):
        """search_by_source must check _connected before get_all_vectors."""
        from governance.vector_store.store import VectorStore
        src = inspect.getsource(VectorStore.search_by_source)
        assert "not self._connected" in src
        assert "return None" in src

    def test_returns_none_when_disconnected(self):
        """Must return None when not connected and cache empty."""
        from governance.vector_store.store import VectorStore
        store = VectorStore()
        # Not connected, cache empty
        result = store.search_by_source("RULE-001")
        assert result is None

    def test_guard_matches_search_method(self):
        """Connection guard pattern must match the search() method."""
        from governance.vector_store.store import VectorStore
        search_src = inspect.getsource(VectorStore.search)
        search_by_src = inspect.getsource(VectorStore.search_by_source)
        # Both must have the same guard pattern
        assert "not self._connected" in search_src
        assert "not self._connected" in search_by_src


# ===========================================================================
# BUG-293-SYN-001: _esc() None guard
# ===========================================================================

class TestSyncEscNoneGuard:
    """Verify _esc() handles None values in decision/task indexing."""

    def test_decision_esc_handles_none(self):
        """_esc in _index_decision_to_typedb must handle None."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_decision_to_typedb)
        idx = src.index("BUG-293-SYN-001")
        block = src[idx:idx + 200]
        assert "if val is None" in block
        assert 'return ""' in block

    def test_task_esc_handles_none(self):
        """_esc in _index_task_to_typedb must handle None."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_task_to_typedb)
        idx = src.index("BUG-293-SYN-001")
        block = src[idx:idx + 200]
        assert "if val is None" in block
        assert 'return ""' in block

    def test_esc_uses_str_coercion(self):
        """_esc must use str() coercion for non-string values."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_decision_to_typedb)
        # Find the _esc function body
        idx = src.index("def _esc")
        block = src[idx:idx + 200]
        assert "str(val)" in block


# ===========================================================================
# BUG-293-SYN-002: Duplicate relation guard
# ===========================================================================

class TestSyncDuplicateRelationGuard:
    """Verify completed-in relation check before insert."""

    def test_relation_check_before_insert(self):
        """Must check for existing relation before inserting."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_task_to_typedb)
        idx = src.index("BUG-293-SYN-002")
        block = src[idx:idx + 800]
        assert "completed-in" in block
        assert "select $r" in block
        assert "if not existing_rel" in block

    def test_relation_check_comes_before_insert(self):
        """Relation existence check must come before the insert query."""
        from governance.session_collector.sync import SessionSyncMixin
        src = inspect.getsource(SessionSyncMixin._index_task_to_typedb)
        check_pos = src.find("existing_rel = client.execute_query(relation_check)")
        # Find the INSERT of the relation (not the match/check)
        insert_pos = src.find("link_query = f'''")
        assert check_pos > 0, "Relation check must exist"
        assert insert_pos > 0, "Insert query must exist"
        assert check_pos < insert_pos, "Check must come before insert"


# ===========================================================================
# BUG-293-WSC-001: Path traversal guard
# ===========================================================================

class TestWorkspaceScannerPathGuard:
    """Verify workspace scanner guards against path traversal."""

    def test_assert_within_workspace_exists(self):
        """_assert_within_workspace function must exist."""
        from governance.workspace_scanner import _assert_within_workspace
        assert callable(_assert_within_workspace)

    def test_rejects_path_outside_workspace(self):
        """Must reject paths outside workspace root."""
        from governance.workspace_scanner import _assert_within_workspace
        with pytest.raises(ValueError, match="Path escapes workspace"):
            _assert_within_workspace("/etc/passwd")

    def test_allows_path_inside_workspace(self):
        """Must allow paths within workspace root."""
        from governance.workspace_scanner import _assert_within_workspace, WORKSPACE_ROOT
        valid_path = os.path.join(WORKSPACE_ROOT, "TODO.md")
        # Should not raise
        _assert_within_workspace(valid_path)

    def test_scan_workspace_calls_guard(self):
        """scan_workspace must call path validation for all file types."""
        from governance.workspace_scanner import scan_workspace
        src = inspect.getsource(scan_workspace)
        # Guard called for TODO, PHASE, and RD paths
        assert src.count("_assert_within_workspace") >= 3

    def test_guard_before_parse_todo(self):
        """Path guard must come before parse_todo_md call in scan_workspace."""
        from governance.workspace_scanner import scan_workspace
        src = inspect.getsource(scan_workspace)
        guard_pos = src.find("_assert_within_workspace(todo_path)")
        parse_pos = src.find("parse_todo_md(todo_path)")
        assert guard_pos > 0 and guard_pos < parse_pos

    def test_guard_before_parse_phase(self):
        """Path guard must come before parse_phase_md call in scan_workspace."""
        from governance.workspace_scanner import scan_workspace
        src = inspect.getsource(scan_workspace)
        # Find guard and parse call in the phase section
        phase_guard = src.find("_assert_within_workspace(filepath)")
        phase_parse = src.find("parse_phase_md(filepath)")
        assert phase_guard > 0 and phase_guard < phase_parse


# ===========================================================================
# Cross-batch: Import verification
# ===========================================================================

class TestBatch290Imports:
    """Verify all fixed modules import cleanly."""

    def test_execution_view(self):
        from agent.governance_ui.views.tasks.execution import build_task_execution_log
        assert callable(build_task_execution_log)

    def test_tool_calls_view(self):
        from agent.governance_ui.views.sessions.tool_calls import build_tool_calls_card
        assert callable(build_tool_calls_card)

    def test_workflow_proposals_view(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_form
        assert callable(build_proposal_form)

    def test_audit_store(self):
        from governance.stores.audit import record_audit, _save_audit_store
        assert callable(record_audit)

    def test_typedb_access(self):
        from governance.stores.typedb_access import _task_to_dict
        assert callable(_task_to_dict)

    def test_vector_store(self):
        from governance.vector_store.store import VectorStore
        assert hasattr(VectorStore, 'search_by_source')

    def test_session_sync(self):
        from governance.session_collector.sync import SessionSyncMixin
        assert hasattr(SessionSyncMixin, '_index_task_to_typedb')

    def test_workspace_scanner(self):
        from governance.workspace_scanner import _assert_within_workspace
        assert callable(_assert_within_workspace)
