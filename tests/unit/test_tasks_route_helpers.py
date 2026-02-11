"""
Unit tests for Tasks Workflow Helpers.

Per DOC-SIZE-01-v1: Tests for extracted routes/tasks/helpers.py.
Tests: enrich_evidence, determine_resolution, validate_promotion,
       combine_evidence, try_link_task_to_session, update_agent_metrics.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.routes.tasks.helpers import (
    VERIFICATION_DESCRIPTIONS,
    enrich_evidence_with_verification,
    determine_resolution,
    validate_promotion,
    combine_evidence,
    try_link_task_to_session,
    record_completion_audit,
    update_agent_metrics_on_claim_fallback,
)
from governance.task_lifecycle import TaskResolution


class TestEnrichEvidenceWithVerification:
    """Tests for enrich_evidence_with_verification()."""

    def test_no_verification_returns_original(self):
        result = enrich_evidence_with_verification("test evidence", None)
        assert result == "test evidence"

    def test_l1_verification(self):
        result = enrich_evidence_with_verification("ev", "L1")
        assert "[Verification: L1]" in result
        assert "Technical fix verified" in result

    def test_l2_verification(self):
        result = enrich_evidence_with_verification("ev", "L2")
        assert "[Verification: L2]" in result

    def test_promotion_prefix(self):
        result = enrich_evidence_with_verification("ev", "L3", is_promotion=True)
        assert "[Promotion: L3]" in result

    def test_none_evidence(self):
        result = enrich_evidence_with_verification(None, "L1")
        assert "[Verification: L1]" in result

    def test_empty_evidence(self):
        result = enrich_evidence_with_verification("", "L1")
        assert result.startswith("[Verification:")


class TestDetermineResolution:
    """Tests for determine_resolution()."""

    def test_with_evidence_only(self):
        result = determine_resolution(
            TaskResolution.IMPLEMENTED,
            has_evidence=True, has_tests=False, has_user_feedback=False,
        )
        assert result == TaskResolution.IMPLEMENTED

    def test_with_tests_validated(self):
        result = determine_resolution(
            TaskResolution.IMPLEMENTED,
            has_evidence=True, has_tests=True, has_user_feedback=False,
        )
        assert result == TaskResolution.VALIDATED

    def test_with_feedback_certified(self):
        result = determine_resolution(
            TaskResolution.IMPLEMENTED,
            has_evidence=True, has_tests=True, has_user_feedback=True,
        )
        assert result == TaskResolution.CERTIFIED

    def test_l2_implies_tests(self):
        result = determine_resolution(
            TaskResolution.IMPLEMENTED,
            has_evidence=True, has_tests=False, has_user_feedback=False,
            verification_level="L2",
        )
        assert result == TaskResolution.VALIDATED

    def test_l3_implies_feedback(self):
        result = determine_resolution(
            TaskResolution.IMPLEMENTED,
            has_evidence=True, has_tests=False, has_user_feedback=False,
            verification_level="L3",
        )
        assert result == TaskResolution.CERTIFIED


class TestValidatePromotion:
    """Tests for validate_promotion()."""

    def test_valid_promotion(self):
        ok, err = validate_promotion(TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED)
        assert ok is True
        assert err is None

    def test_invalid_promotion(self):
        ok, err = validate_promotion(TaskResolution.CERTIFIED, TaskResolution.IMPLEMENTED)
        assert ok is False
        assert err is not None
        assert "Cannot promote" in err


class TestCombineEvidence:
    """Tests for combine_evidence()."""

    def test_no_existing(self):
        result = combine_evidence(None, "new evidence")
        assert result == "new evidence"

    def test_with_existing(self):
        result = combine_evidence("old", "new")
        assert "old" in result
        assert "new" in result
        assert "---" in result

    def test_empty_existing(self):
        result = combine_evidence("", "new")
        assert result == "new"


class TestTryLinkTaskToSession:
    """Tests for try_link_task_to_session()."""

    def test_no_session_id(self):
        client = MagicMock()
        result = try_link_task_to_session(client, "T-1", None)
        assert result is False

    def test_successful_link(self):
        client = MagicMock()
        result = try_link_task_to_session(client, "T-1", "S-1")
        assert result is True
        client.link_task_to_session.assert_called_once_with("T-1", "S-1")

    def test_link_error(self):
        client = MagicMock()
        client.link_task_to_session.side_effect = Exception("DB error")
        result = try_link_task_to_session(client, "T-1", "S-1")
        assert result is False


class TestRecordCompletionAudit:
    """Tests for record_completion_audit()."""

    @patch("governance.routes.tasks.helpers.record_audit")
    def test_records_audit(self, mock_audit):
        record_completion_audit(
            "T-1", "code-agent", "IN_PROGRESS", "DONE",
            "VALIDATED", "L2", "S-1",
        )
        mock_audit.assert_called_once()
        args = mock_audit.call_args
        assert args[1]["entity_id"] == "T-1"
        assert args[1]["old_value"] == "IN_PROGRESS"

    @patch("governance.routes.tasks.helpers.record_audit")
    def test_unknown_agent(self, mock_audit):
        record_completion_audit(
            "T-1", None, "OPEN", "DONE", "IMPLEMENTED", None, None,
        )
        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["actor_id"] == "unknown"


class TestUpdateAgentMetricsOnClaimFallback:
    """Tests for update_agent_metrics_on_claim_fallback()."""

    def test_updates_metrics(self):
        store = {
            "code-agent": {"tasks_executed": 5, "last_active": None, "trust_score": 0.8},
        }
        config = {"code-agent": {"base_trust": 0.85}}
        calc_fn = MagicMock(return_value=0.9)
        load_fn = MagicMock(return_value={})
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "code-agent", store, config, calc_fn, load_fn, save_fn,
        )

        assert store["code-agent"]["tasks_executed"] == 6
        assert store["code-agent"]["trust_score"] == 0.9
        assert store["code-agent"]["last_active"] is not None
        save_fn.assert_called_once()

    def test_unknown_agent_skipped(self):
        store = {}
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "unknown", store, {}, MagicMock(), MagicMock(), save_fn,
        )

        save_fn.assert_not_called()
