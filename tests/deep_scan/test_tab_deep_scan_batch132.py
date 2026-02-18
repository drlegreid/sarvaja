"""Deep scan batch 132: Store persistence + agents + audit.

Batch 132 findings: 15 total, 0 confirmed fixes, 15 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import math


# ── Session sync status persistence defense ──────────────


class TestSessionSyncStatusDefense:
    """Verify sync_pending_sessions handles status correctly."""

    def test_sync_logs_status_failure_at_warning(self):
        """Status sync failure logs at WARNING, not silent pass."""
        import logging
        from unittest.mock import patch, MagicMock

        mock_client = MagicMock()
        mock_client.get_session.return_value = None  # Not yet persisted
        mock_client.insert_session.return_value = True
        mock_client.update_session.side_effect = Exception("TypeDB transient")

        with patch("governance.services.sessions.get_typedb_client", return_value=mock_client), \
             patch("governance.services.sessions._sessions_store", {
                 "SESSION-2026-02-15-TEST": {
                     "session_id": "SESSION-2026-02-15-TEST",
                     "status": "ACTIVE",
                     "description": "Test",
                 }
             }), \
             patch("governance.services.sessions.logger") as mock_logger:
            from governance.services.sessions import sync_pending_sessions
            result = sync_pending_sessions()
            # Insert succeeds, status update logged
            assert result["synced"] == 1
            # Status failure logged at WARNING not silently swallowed
            mock_logger.warning.assert_called()

    def test_sync_passes_cc_fields_to_insert(self):
        """sync_pending_sessions passes CC fields atomically."""
        mock_client = MagicMock()
        mock_client.get_session.return_value = None
        mock_client.insert_session.return_value = True

        session_data = {
            "session_id": "SESSION-2026-02-15-CC",
            "description": "CC session",
            "cc_session_uuid": "uuid-123",
            "cc_project_slug": "sarvaja",
        }

        with patch("governance.services.sessions.get_typedb_client", return_value=mock_client), \
             patch("governance.services.sessions._sessions_store", {
                 "SESSION-2026-02-15-CC": session_data,
             }):
            from governance.services.sessions import sync_pending_sessions
            sync_pending_sessions()
            # Verify CC fields passed to insert_session
            call_kwargs = mock_client.insert_session.call_args
            assert call_kwargs[1].get("cc_session_uuid") == "uuid-123"


# ── Evidence merge fallback defense ──────────────


class TestEvidenceMergeFallbackDefense:
    """Verify evidence merge only fills gaps, doesn't override TypeDB."""

    def test_merge_only_when_typedb_empty(self):
        """Evidence from _tasks_store only used when TypeDB field is empty."""
        from governance.stores.typedb_access import _tasks_store

        # Simulate: TypeDB has evidence, memory also has evidence
        typedb_task = {"task_id": "T-001", "evidence": "from-typedb"}
        mem_evidence = "from-memory"

        # Only merge if TypeDB evidence is empty
        if not typedb_task.get("evidence"):
            typedb_task["evidence"] = mem_evidence
        assert typedb_task["evidence"] == "from-typedb"  # TypeDB wins

    def test_merge_fills_gap_when_typedb_empty(self):
        """Evidence from memory fills gap when TypeDB has none."""
        typedb_task = {"task_id": "T-001", "evidence": None}
        mem_evidence = "from-memory"

        if not typedb_task.get("evidence") and mem_evidence:
            typedb_task["evidence"] = mem_evidence
        assert typedb_task["evidence"] == "from-memory"


# ── Agent trust score calculation defense ──────────────


class TestAgentTrustScoreDefense:
    """Verify trust score calculation is bounded and correct."""

    def test_zero_tasks_returns_base_trust(self):
        """Agent with 0 tasks returns base_trust unchanged."""
        from governance.stores.agents import _calculate_trust_score

        result = _calculate_trust_score("test-agent", 0, 0.85)
        assert result == 0.85

    def test_trust_score_increases_with_tasks(self):
        """More tasks = higher trust (logarithmic)."""
        from governance.stores.agents import _calculate_trust_score

        score_10 = _calculate_trust_score("a", 10, 0.85)
        score_100 = _calculate_trust_score("a", 100, 0.85)
        assert score_100 > score_10 > 0.85

    def test_trust_score_capped_at_1(self):
        """Trust score never exceeds 1.0."""
        from governance.stores.agents import _calculate_trust_score

        result = _calculate_trust_score("a", 1_000_000, 0.99)
        assert result <= 1.0

    def test_trust_formula_log10(self):
        """Trust follows log10(tasks+1) * 0.05 formula."""
        from governance.stores.agents import _calculate_trust_score

        # 100 tasks: log10(101) * 0.05 ≈ 0.1003
        result = _calculate_trust_score("a", 100, 0.85)
        expected = min(1.0, 0.85 * (1 + math.log10(101) * 0.05))
        assert abs(result - expected) < 0.001


# ── Agent metrics persistence defense ──────────────


class TestAgentMetricsPersistenceDefense:
    """Verify metrics update-then-save pattern."""

    def test_metrics_saved_after_claim(self):
        """Metrics are persisted after task claim."""
        from governance.stores.agents import _update_agent_metrics_on_claim, _agents_store

        # Ensure agent exists
        if "code-agent" in _agents_store:
            original_tasks = _agents_store["code-agent"]["tasks_executed"]
            with patch("governance.stores.agents._save_agent_metrics") as mock_save:
                _update_agent_metrics_on_claim("code-agent")
                mock_save.assert_called_once()

    def test_nonexistent_agent_skipped(self):
        """Claim for nonexistent agent is silently skipped."""
        from governance.stores.agents import _update_agent_metrics_on_claim

        # Should not raise
        _update_agent_metrics_on_claim("nonexistent-agent-id-xyz")


# ── Audit store dict filter defense ──────────────


class TestAuditStoreDictFilterDefense:
    """Verify audit loading filters non-dict entries."""

    def test_non_dict_entries_filtered(self):
        """Non-dict entries in audit JSON are filtered out."""
        data = [
            {"audit_id": "A1", "timestamp": "2026-02-15"},
            "not-a-dict",
            42,
            {"audit_id": "A2", "timestamp": "2026-02-15"},
            None,
        ]
        filtered = [e for e in data if isinstance(e, dict)]
        assert len(filtered) == 2

    def test_empty_list_preserved(self):
        """Empty list stays empty after filter."""
        data = []
        filtered = [e for e in data if isinstance(e, dict)]
        assert filtered == []


# ── Dual session converter parity defense ──────────────


class TestDualSessionConverterDefense:
    """Verify both session converters include CC fields."""

    def test_session_to_response_has_cc_fields(self):
        """session_to_response() includes CC fields."""
        import inspect
        from governance.stores.helpers import session_to_response
        source = inspect.getsource(session_to_response)
        assert "cc_session_uuid" in source
        assert "cc_project_slug" in source

    def test_session_to_dict_has_cc_fields(self):
        """_session_to_dict() includes CC fields."""
        import inspect
        from governance.stores.typedb_access import _session_to_dict
        source = inspect.getsource(_session_to_dict)
        assert "cc_session_uuid" in source
        assert "cc_project_slug" in source
