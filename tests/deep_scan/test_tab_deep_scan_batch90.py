"""Deep scan batch 90: Evidence pipeline, DSM tracker, session collector sync.

Batch 90 findings: 26 total, 2 confirmed fixes, 24 rejected.
Confirmed: BUG-SYNC-LINK-ESCAPE-001 (sync.py L218-219 unescaped IDs in link_query)
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── BUG-SYNC-LINK-ESCAPE-001: Escaped IDs in link_query ──────────────


def _make_sync_mixin(session_id="SESSION-TEST"):
    """Create a SessionSyncMixin instance with required attrs."""
    from governance.session_collector.sync import SessionSyncMixin

    sync = SessionSyncMixin.__new__(SessionSyncMixin)
    sync.session_id = session_id
    sync.typedb_host = "localhost"
    sync.typedb_port = 1729
    sync.typedb_database = "test"
    return sync


def _make_task(task_id="TASK-001", name="Test", desc="Desc", status="pending"):
    """Create a mock Task."""
    task = MagicMock()
    task.id = task_id
    task.name = name
    task.description = desc
    task.status = status
    return task


class TestSyncLinkEscape:
    """Verify sync.py uses escaped IDs in TypeQL link_query."""

    def test_link_query_uses_escaped_task_id(self):
        """task_id_escaped must be used in link_query, not raw task.id."""
        sync = _make_sync_mixin()
        task = _make_task(task_id='task-with"quote')

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        # session exists, task doesn't exist
        mock_client.execute_query.side_effect = [
            ["session exists"],  # session check
            None,                # task check → doesn't exist
            None,                # task insert
            None,                # link insert
        ]

        with patch("governance.client.TypeDBClient", return_value=mock_client):
            sync._index_task_to_typedb(task)

        # Find the link_query call (last execute_query)
        calls = mock_client.execute_query.call_args_list
        link_query = calls[-1][0][0]
        # Must contain escaped quote
        assert 'task-with\\"quote' in link_query, \
            f"link_query must use escaped task_id, got: {link_query}"

    def test_link_query_uses_escaped_session_id(self):
        """session_id must be escaped in link_query."""
        sync = _make_sync_mixin(session_id='SESSION-"test"')
        task = _make_task()

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.side_effect = [
            ["session exists"],  # session check
            ["task exists"],     # task check → exists
            None,                # link insert
        ]

        with patch("governance.client.TypeDBClient", return_value=mock_client):
            sync._index_task_to_typedb(task)

        calls = mock_client.execute_query.call_args_list
        link_query = calls[-1][0][0]
        assert 'SESSION-\\"test\\"' in link_query, \
            f"session_id must be escaped, got: {link_query}"

    def test_task_check_uses_escaped_id(self):
        """Verify task existence check uses escaped ID."""
        sync = _make_sync_mixin()
        task = _make_task(task_id='id"injection')

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.side_effect = [
            ["session exists"],
            ["task exists"],
            None,
        ]

        with patch("governance.client.TypeDBClient", return_value=mock_client):
            sync._index_task_to_typedb(task)

        # Task check is the 2nd query
        check_query = mock_client.execute_query.call_args_list[1][0][0]
        assert 'id\\"injection' in check_query


# ── DSM abort_cycle defense verification ──────────────


class TestDSMAbortCycleDefense:
    """Verify abort_cycle safely discards cycle (no ValueError on read)."""

    def test_abort_cycle_nullifies_current_cycle(self):
        """After abort, current_cycle must be None."""
        from governance.dsm.tracker import DSMTracker

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.completed_cycles = []
        tracker._state_file = "/tmp/test_dsm_state.json"

        cycle = MagicMock()
        cycle.metrics = {}
        cycle.end_time = None
        cycle.current_phase = "audit"
        tracker.current_cycle = cycle

        with patch.object(tracker, "_save_state"):
            tracker.abort_cycle(reason="test abort")

        assert tracker.current_cycle is None

    def test_get_status_safe_after_abort(self):
        """get_status() must not crash after abort_cycle."""
        from governance.dsm.tracker import DSMTracker

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.completed_cycles = []
        tracker._state_file = "/tmp/test_dsm_state.json"

        cycle = MagicMock()
        cycle.metrics = {}
        cycle.end_time = None
        cycle.current_phase = "audit"
        tracker.current_cycle = cycle

        with patch.object(tracker, "_save_state"):
            tracker.abort_cycle()

        status = tracker.get_status()
        assert status["active"] is False


# ── DSPPhase enum completeness ──────────────


class TestDSPPhaseEnum:
    """Verify DSPPhase enum correctness."""

    def test_all_phases_present(self):
        from governance.dsm.phases import DSPPhase

        expected = {"idle", "audit", "hypothesize", "measure",
                    "optimize", "validate", "dream", "report", "complete"}
        actual = {p.value for p in DSPPhase}
        assert expected.issubset(actual)

    def test_phase_order_excludes_idle_complete(self):
        from governance.dsm.phases import DSPPhase

        order = DSPPhase.phase_order()
        assert DSPPhase.IDLE not in order
        assert DSPPhase.COMPLETE not in order

    def test_complete_has_no_next(self):
        from governance.dsm.phases import DSPPhase
        assert DSPPhase.COMPLETE.next_phase() is None


# ── Evidence pipeline defense verification ──────────────


class TestEvidencePipelineDefense:
    """Defense tests for batch 90 rejected evidence findings."""

    def test_generate_session_evidence_handles_missing_fields(self):
        from governance.services.session_evidence import generate_session_evidence

        result = generate_session_evidence({
            "session_id": "TEST-MINIMAL",
            "status": "COMPLETED",
        })
        assert result is None or isinstance(result, str)

    def test_generate_session_evidence_handles_empty(self):
        from governance.services.session_evidence import generate_session_evidence

        result = generate_session_evidence({})
        assert result is None or isinstance(result, str)


# ── CVP category overwrite defense (INTENTIONAL) ──────────────


class TestCVPCategoryOverwrite:
    """Documents that CVP category overwrite is intentional."""

    def test_test_results_is_dict(self):
        from governance.routes.tests.runner_exec import _test_results
        assert isinstance(_test_results, dict)


# ── Sync TypeDB fallback ──────────────


class TestSyncTypeDBFallback:
    """Verify sync handles TypeDB failure gracefully."""

    def test_index_task_returns_false_on_connect_failure(self):
        """_index_task_to_typedb returns False when connect fails."""
        sync = _make_sync_mixin()
        task = _make_task()

        mock_client = MagicMock()
        mock_client.connect.return_value = False

        with patch("governance.client.TypeDBClient", return_value=mock_client):
            result = sync._index_task_to_typedb(task)

        assert result is False

    def test_index_task_returns_false_on_exception(self):
        """_index_task_to_typedb returns False on exception."""
        sync = _make_sync_mixin()
        task = _make_task()

        with patch("governance.client.TypeDBClient", side_effect=Exception("fail")):
            result = sync._index_task_to_typedb(task)

        assert result is False

    def test_index_task_returns_true_on_success(self):
        """_index_task_to_typedb returns True on successful indexing."""
        sync = _make_sync_mixin()
        task = _make_task()

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.execute_query.return_value = ["exists"]

        with patch("governance.client.TypeDBClient", return_value=mock_client):
            result = sync._index_task_to_typedb(task)

        assert result is True
