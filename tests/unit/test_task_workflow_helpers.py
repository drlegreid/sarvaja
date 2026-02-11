"""
Unit tests for Tasks Workflow Helpers.

Per DOC-SIZE-01-v1: Tests for extracted routes/tasks/helpers.py module.
Tests: enrich_evidence_with_verification, determine_resolution,
       validate_promotion, combine_evidence, try_link_task_to_session,
       record_completion_audit, update_agent_metrics_on_claim_fallback.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.task_lifecycle import TaskResolution
from governance.routes.tasks.helpers import (
    enrich_evidence_with_verification,
    determine_resolution,
    validate_promotion,
    combine_evidence,
    try_link_task_to_session,
    record_completion_audit,
    update_agent_metrics_on_claim_fallback,
    VERIFICATION_DESCRIPTIONS,
)


class TestVerificationDescriptions:
    """Tests for VERIFICATION_DESCRIPTIONS constant."""

    def test_has_all_levels(self):
        assert "L1" in VERIFICATION_DESCRIPTIONS
        assert "L2" in VERIFICATION_DESCRIPTIONS
        assert "L3" in VERIFICATION_DESCRIPTIONS

    def test_l1_description(self):
        assert "Technical" in VERIFICATION_DESCRIPTIONS["L1"]

    def test_l2_description(self):
        assert "E2E" in VERIFICATION_DESCRIPTIONS["L2"]

    def test_l3_description(self):
        assert "user flow" in VERIFICATION_DESCRIPTIONS["L3"]


class TestEnrichEvidenceWithVerification:
    """Tests for enrich_evidence_with_verification()."""

    def test_no_verification(self):
        result = enrich_evidence_with_verification("evidence text", None)
        assert result == "evidence text"

    def test_l1_verification(self):
        result = enrich_evidence_with_verification("fix applied", "L1")
        assert "[Verification: L1]" in result
        assert "Technical" in result
        assert "fix applied" in result

    def test_l2_verification(self):
        result = enrich_evidence_with_verification("tests pass", "L2")
        assert "[Verification: L2]" in result
        assert "E2E" in result

    def test_l3_verification(self):
        result = enrich_evidence_with_verification("user confirmed", "L3")
        assert "[Verification: L3]" in result
        assert "user flow" in result

    def test_promotion_prefix(self):
        result = enrich_evidence_with_verification("upgrade", "L2", is_promotion=True)
        assert "[Promotion: L2]" in result
        assert "[Verification:" not in result

    def test_none_evidence(self):
        result = enrich_evidence_with_verification(None, "L1")
        assert "[Verification: L1]" in result
        assert result.startswith("[Verification:")

    def test_empty_evidence(self):
        result = enrich_evidence_with_verification("", "L1")
        assert "[Verification: L1]" in result


class TestDetermineResolution:
    """Tests for determine_resolution()."""

    def test_evidence_only_gives_implemented(self):
        result = determine_resolution(
            TaskResolution.NONE,
            has_evidence=True,
            has_tests=False,
            has_user_feedback=False,
        )
        assert result == TaskResolution.IMPLEMENTED

    def test_evidence_and_tests_gives_validated(self):
        result = determine_resolution(
            TaskResolution.NONE,
            has_evidence=True,
            has_tests=True,
            has_user_feedback=False,
        )
        assert result == TaskResolution.VALIDATED

    def test_all_gives_certified(self):
        result = determine_resolution(
            TaskResolution.NONE,
            has_evidence=True,
            has_tests=True,
            has_user_feedback=True,
        )
        assert result == TaskResolution.CERTIFIED

    def test_l2_verification_implies_tests(self):
        result = determine_resolution(
            TaskResolution.NONE,
            has_evidence=True,
            has_tests=False,
            has_user_feedback=False,
            verification_level="L2",
        )
        assert result == TaskResolution.VALIDATED

    def test_l3_verification_implies_user_feedback(self):
        result = determine_resolution(
            TaskResolution.NONE,
            has_evidence=True,
            has_tests=False,
            has_user_feedback=False,
            verification_level="L3",
        )
        assert result == TaskResolution.CERTIFIED

    def test_l1_no_upgrade(self):
        result = determine_resolution(
            TaskResolution.NONE,
            has_evidence=True,
            has_tests=False,
            has_user_feedback=False,
            verification_level="L1",
        )
        assert result == TaskResolution.IMPLEMENTED


class TestValidatePromotion:
    """Tests for validate_promotion()."""

    def test_implemented_to_validated(self):
        ok, err = validate_promotion(TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED)
        assert ok is True
        assert err is None

    def test_validated_to_certified(self):
        ok, err = validate_promotion(TaskResolution.VALIDATED, TaskResolution.CERTIFIED)
        assert ok is True
        assert err is None

    def test_none_to_certified_invalid(self):
        ok, err = validate_promotion(TaskResolution.NONE, TaskResolution.CERTIFIED)
        assert ok is False
        assert "Cannot promote" in err

    def test_same_resolution(self):
        ok, err = validate_promotion(TaskResolution.IMPLEMENTED, TaskResolution.IMPLEMENTED)
        assert ok is True


class TestCombineEvidence:
    """Tests for combine_evidence()."""

    def test_no_existing(self):
        result = combine_evidence(None, "new evidence")
        assert result == "new evidence"

    def test_with_existing(self):
        result = combine_evidence("old evidence", "new evidence")
        assert "old evidence" in result
        assert "---" in result
        assert "new evidence" in result

    def test_empty_existing(self):
        result = combine_evidence("", "new")
        assert result == "new"


class TestTryLinkTaskToSession:
    """Tests for try_link_task_to_session()."""

    def test_no_session_id(self):
        client = MagicMock()
        assert try_link_task_to_session(client, "T-1", None) is False
        client.link_task_to_session.assert_not_called()

    def test_successful_link(self):
        client = MagicMock()
        result = try_link_task_to_session(client, "T-1", "S-1")
        assert result is True
        client.link_task_to_session.assert_called_once_with("T-1", "S-1")

    def test_failed_link(self):
        client = MagicMock()
        client.link_task_to_session.side_effect = Exception("TypeDB down")
        result = try_link_task_to_session(client, "T-1", "S-1")
        assert result is False

    def test_with_context(self):
        client = MagicMock()
        try_link_task_to_session(client, "T-1", "S-1", "promotion")
        client.link_task_to_session.assert_called_once()


class TestRecordCompletionAudit:
    """Tests for record_completion_audit()."""

    @patch("governance.routes.tasks.helpers.record_audit")
    def test_records_audit(self, mock_audit):
        record_completion_audit(
            "TASK-001", "code-agent",
            "IN_PROGRESS", "CLOSED",
            "IMPLEMENTED", "L1", "SESSION-001"
        )
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        assert call_kwargs[1]["action_type"] == "COMPLETE" or call_kwargs[0][0] == "COMPLETE"

    @patch("governance.routes.tasks.helpers.record_audit")
    def test_no_agent_defaults_to_unknown(self, mock_audit):
        record_completion_audit(
            "TASK-001", None,
            "IN_PROGRESS", "CLOSED",
            "IMPLEMENTED", None, None
        )
        args, kwargs = mock_audit.call_args
        assert "unknown" in str(args) or kwargs.get("actor_id") == "unknown"


class TestUpdateAgentMetricsOnClaimFallback:
    """Tests for update_agent_metrics_on_claim_fallback()."""

    def test_increments_tasks_executed(self):
        store = {
            "code-agent": {
                "tasks_executed": 5,
                "last_active": "2026-02-10",
                "trust_score": 0.85,
            }
        }
        config = {"code-agent": {"base_trust": 0.85}}
        calc_fn = MagicMock(return_value=0.87)
        load_fn = MagicMock(return_value={})
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "code-agent", store, config, calc_fn, load_fn, save_fn
        )

        assert store["code-agent"]["tasks_executed"] == 6
        assert store["code-agent"]["trust_score"] == 0.87
        calc_fn.assert_called_once_with("code-agent", 6, 0.85)
        save_fn.assert_called_once()

    def test_unknown_agent_noop(self):
        store = {}
        config = {}
        calc_fn = MagicMock()
        load_fn = MagicMock()
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "unknown-agent", store, config, calc_fn, load_fn, save_fn
        )

        calc_fn.assert_not_called()
        save_fn.assert_not_called()

    def test_saves_metrics(self):
        store = {
            "test-agent": {
                "tasks_executed": 0,
                "last_active": "",
                "trust_score": 0.8,
            }
        }
        config = {"test-agent": {"base_trust": 0.8}}
        calc_fn = MagicMock(return_value=0.82)
        load_fn = MagicMock(return_value={})
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "test-agent", store, config, calc_fn, load_fn, save_fn
        )

        saved = save_fn.call_args[0][0]
        assert "test-agent" in saved
        assert saved["test-agent"]["tasks_executed"] == 1
