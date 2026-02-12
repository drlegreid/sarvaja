"""
Unit tests for Tasks Workflow Helpers.

Per DOC-SIZE-01-v1: Tests for governance/routes/tasks/helpers.py.
Tests: enrich_evidence_with_verification, determine_resolution,
       validate_promotion, combine_evidence, try_link_task_to_session,
       record_completion_audit, update_agent_metrics_on_claim_fallback.
"""

from unittest.mock import patch, MagicMock

from governance.task_lifecycle import TaskResolution
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


# ── VERIFICATION_DESCRIPTIONS ─────────────────────────


class TestVerificationDescriptions:
    def test_all_levels(self):
        assert "L1" in VERIFICATION_DESCRIPTIONS
        assert "L2" in VERIFICATION_DESCRIPTIONS
        assert "L3" in VERIFICATION_DESCRIPTIONS

    def test_values_are_strings(self):
        for v in VERIFICATION_DESCRIPTIONS.values():
            assert isinstance(v, str)


# ── enrich_evidence_with_verification ──────────────────


class TestEnrichEvidence:
    def test_no_verification(self):
        result = enrich_evidence_with_verification("base evidence", None)
        assert result == "base evidence"

    def test_with_l1(self):
        result = enrich_evidence_with_verification("fix applied", "L1")
        assert "[Verification: L1]" in result
        assert "fix applied" in result

    def test_with_promotion(self):
        result = enrich_evidence_with_verification("promoted", "L2", is_promotion=True)
        assert "[Promotion: L2]" in result

    def test_none_evidence(self):
        result = enrich_evidence_with_verification(None, "L1")
        assert "[Verification: L1]" in result

    def test_empty_evidence(self):
        result = enrich_evidence_with_verification("", "L3")
        assert result.startswith("[Verification: L3]")


# ── determine_resolution ──────────────────────────────


class TestDetermineResolution:
    def test_with_evidence_only(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=False, has_user_feedback=False)
        assert result == TaskResolution.IMPLEMENTED

    def test_with_tests(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=True, has_user_feedback=False)
        assert result == TaskResolution.VALIDATED

    def test_with_user_feedback(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=True, has_user_feedback=True)
        assert result == TaskResolution.CERTIFIED

    def test_l2_implies_tests(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=False, has_user_feedback=False,
            verification_level="L2")
        assert result == TaskResolution.VALIDATED

    def test_l3_implies_user_feedback(self):
        result = determine_resolution(
            TaskResolution.NONE, has_evidence=True,
            has_tests=False, has_user_feedback=False,
            verification_level="L3")
        assert result == TaskResolution.CERTIFIED


# ── validate_promotion ─────────────────────────────────


class TestValidatePromotion:
    def test_implemented_to_validated(self):
        ok, err = validate_promotion(
            TaskResolution.IMPLEMENTED, TaskResolution.VALIDATED)
        assert ok is True
        assert err is None

    def test_validated_to_certified(self):
        ok, err = validate_promotion(
            TaskResolution.VALIDATED, TaskResolution.CERTIFIED)
        assert ok is True

    def test_invalid_transition(self):
        ok, err = validate_promotion(
            TaskResolution.NONE, TaskResolution.CERTIFIED)
        assert ok is False
        assert "Cannot promote" in err


# ── combine_evidence ───────────────────────────────────


class TestCombineEvidence:
    def test_no_existing(self):
        assert combine_evidence(None, "new") == "new"

    def test_empty_existing(self):
        assert combine_evidence("", "new") == "new"

    def test_with_existing(self):
        result = combine_evidence("old", "new")
        assert "old" in result
        assert "---" in result
        assert "new" in result


# ── try_link_task_to_session ───────────────────────────


class TestTryLinkTaskToSession:
    def test_no_session_id(self):
        client = MagicMock()
        assert try_link_task_to_session(client, "T-1", None) is False
        client.link_task_to_session.assert_not_called()

    def test_success(self):
        client = MagicMock()
        assert try_link_task_to_session(client, "T-1", "S-1") is True
        client.link_task_to_session.assert_called_once_with("T-1", "S-1")

    def test_exception_returns_false(self):
        client = MagicMock()
        client.link_task_to_session.side_effect = Exception("db error")
        assert try_link_task_to_session(client, "T-1", "S-1") is False


# ── record_completion_audit ────────────────────────────


class TestRecordCompletionAudit:
    @patch("governance.routes.tasks.helpers.record_audit")
    def test_records_audit(self, mock_audit):
        record_completion_audit("T-1", "code-agent", "IN_PROGRESS", "CLOSED",
                                "IMPLEMENTED", "L1", "S-1")

        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args[1]
        assert call_kwargs["action_type"] == "COMPLETE"
        assert call_kwargs["entity_id"] == "T-1"
        assert call_kwargs["actor_id"] == "code-agent"

    @patch("governance.routes.tasks.helpers.record_audit")
    def test_no_agent_uses_unknown(self, mock_audit):
        record_completion_audit("T-1", None, "IN_PROGRESS", "CLOSED",
                                "IMPLEMENTED", None, None)

        call_kwargs = mock_audit.call_args[1]
        assert call_kwargs["actor_id"] == "unknown"


# ── update_agent_metrics_on_claim_fallback ─────────────


class TestUpdateAgentMetrics:
    def test_unknown_agent_noop(self):
        store = {}
        update_agent_metrics_on_claim_fallback(
            "unknown", store, {}, lambda *a: 0.9, lambda: {}, lambda m: None)

    def test_updates_metrics(self):
        store = {"bot-1": {"tasks_executed": 5, "last_active": "", "trust_score": 0.8}}
        config = {"bot-1": {"base_trust": 0.85}}
        saved = {}

        def save_fn(m):
            saved.update(m)

        update_agent_metrics_on_claim_fallback(
            "bot-1", store, config,
            lambda aid, count, base: 0.9,
            lambda: {},
            save_fn
        )

        assert store["bot-1"]["tasks_executed"] == 6
        assert store["bot-1"]["trust_score"] == 0.9
        assert "bot-1" in saved
