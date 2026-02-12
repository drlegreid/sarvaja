"""
Unit tests for Tasks Workflow Helpers.

Per DOC-SIZE-01-v1: Tests for routes/tasks/helpers.py module.
Tests: enrich_evidence_with_verification, determine_resolution,
       validate_promotion, combine_evidence, try_link_task_to_session,
       record_completion_audit, update_agent_metrics_on_claim_fallback.
"""

from unittest.mock import patch, MagicMock

import pytest

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
from governance.task_lifecycle import TaskResolution


class TestEnrichEvidence:
    def test_no_verification(self):
        result = enrich_evidence_with_verification("Fix applied", None)
        assert result == "Fix applied"

    def test_with_l1(self):
        result = enrich_evidence_with_verification("Fix applied", "L1")
        assert "[Verification: L1]" in result
        assert "Technical fix verified" in result
        assert "Fix applied" in result

    def test_with_l2(self):
        result = enrich_evidence_with_verification("Tests pass", "L2")
        assert "[Verification: L2]" in result
        assert "E2E functionality verified" in result

    def test_with_l3(self):
        result = enrich_evidence_with_verification("User approved", "L3")
        assert "[Verification: L3]" in result
        assert "Full user flow verified" in result

    def test_promotion_prefix(self):
        result = enrich_evidence_with_verification("Tests pass", "L2", is_promotion=True)
        assert "[Promotion: L2]" in result

    def test_none_evidence(self):
        result = enrich_evidence_with_verification(None, "L1")
        assert "[Verification: L1]" in result

    def test_empty_evidence(self):
        result = enrich_evidence_with_verification("", "L1")
        assert "[Verification: L1]" in result


class TestDetermineResolution:
    def test_no_evidence_defaults_to_implemented(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=False,
            has_tests=False, has_user_feedback=False,
        )
        # get_resolution_for_close defaults to IMPLEMENTED
        assert result == TaskResolution.IMPLEMENTED

    def test_with_evidence_only(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=False, has_user_feedback=False,
        )
        assert result == TaskResolution.IMPLEMENTED

    def test_with_tests(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=True, has_user_feedback=False,
        )
        assert result == TaskResolution.VALIDATED

    def test_with_user_feedback(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=True, has_user_feedback=True,
        )
        assert result == TaskResolution.CERTIFIED

    def test_l2_implies_tests(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=False, has_user_feedback=False,
            verification_level="L2",
        )
        assert result == TaskResolution.VALIDATED

    def test_l3_implies_certified(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=False, has_user_feedback=False,
            verification_level="L3",
        )
        assert result == TaskResolution.CERTIFIED


class TestValidatePromotion:
    def test_valid_implemented_to_validated(self):
        valid, msg = validate_promotion(
            TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED
        )
        assert valid is True
        assert msg is None

    def test_valid_validated_to_certified(self):
        valid, msg = validate_promotion(
            TaskResolution.VALIDATED, TaskResolution.CERTIFIED
        )
        assert valid is True

    def test_same_level_is_valid(self):
        # validate_resolution_transition allows same-level (from == to)
        valid, msg = validate_promotion(
            TaskResolution.VALIDATED, TaskResolution.VALIDATED
        )
        assert valid is True
        assert msg is None

    def test_invalid_downgrade(self):
        valid, msg = validate_promotion(
            TaskResolution.CERTIFIED, TaskResolution.IMPLEMENTED
        )
        assert valid is False


class TestCombineEvidence:
    def test_no_existing(self):
        result = combine_evidence(None, "New evidence")
        assert result == "New evidence"

    def test_with_existing(self):
        result = combine_evidence("Old evidence", "New evidence")
        assert "Old evidence" in result
        assert "---" in result
        assert "New evidence" in result

    def test_empty_existing(self):
        result = combine_evidence("", "New evidence")
        assert result == "New evidence"


class TestTryLinkTaskToSession:
    def test_success(self):
        client = MagicMock()
        result = try_link_task_to_session(client, "T-1", "S-1", "completion")
        assert result is True
        client.link_task_to_session.assert_called_once_with("T-1", "S-1")

    def test_no_session_id(self):
        client = MagicMock()
        result = try_link_task_to_session(client, "T-1", None)
        assert result is False
        client.link_task_to_session.assert_not_called()

    def test_error_returns_false(self):
        client = MagicMock()
        client.link_task_to_session.side_effect = Exception("link failed")
        result = try_link_task_to_session(client, "T-1", "S-1")
        assert result is False


class TestRecordCompletionAudit:
    def test_records(self):
        with patch("governance.routes.tasks.helpers.record_audit") as mock_audit:
            record_completion_audit(
                "T-1", "agent-1", "IN_PROGRESS", "DONE",
                "IMPLEMENTED", "L1", "S-1",
            )
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args[1]
        assert call_kwargs["entity_id"] == "T-1"
        assert call_kwargs["action_type"] == "COMPLETE"


class TestUpdateAgentMetricsFallback:
    def test_updates_metrics(self):
        agents_store = {
            "agent-1": {
                "tasks_executed": 5,
                "last_active": None,
                "trust_score": 0.85,
            }
        }
        calc_fn = MagicMock(return_value=0.90)
        load_fn = MagicMock(return_value={})
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "agent-1", agents_store, {"agent-1": {"base_trust": 0.85}},
            calc_fn, load_fn, save_fn,
        )

        assert agents_store["agent-1"]["tasks_executed"] == 6
        assert agents_store["agent-1"]["trust_score"] == 0.90
        save_fn.assert_called_once()

    def test_unknown_agent_noop(self):
        agents_store = {}
        calc_fn = MagicMock()
        load_fn = MagicMock()
        save_fn = MagicMock()

        update_agent_metrics_on_claim_fallback(
            "unknown", agents_store, {},
            calc_fn, load_fn, save_fn,
        )

        calc_fn.assert_not_called()
        save_fn.assert_not_called()
