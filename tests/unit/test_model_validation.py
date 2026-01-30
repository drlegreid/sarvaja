"""
Tests for Pydantic model input validation.

Per RULE-012: DSP Semantic Code Structure.
Validates Literal enum types and min_length constraints on API models.

Created: 2026-01-30
"""

import pytest
from pydantic import ValidationError

from governance.models import (
    RuleCreate,
    RuleUpdate,
    DecisionCreate,
    DecisionUpdate,
    TaskCreate,
)


class TestRuleCreateValidation:
    """Validate RuleCreate model constraints."""

    def test_valid_rule_create(self):
        """Accept valid rule creation data."""
        rule = RuleCreate(
            rule_id="RULE-099",
            name="Test Rule",
            category="governance",
            priority="HIGH",
            directive="Do something",
        )
        assert rule.rule_id == "RULE-099"
        assert rule.status == "DRAFT"

    def test_all_categories_accepted(self):
        """Accept all valid category values."""
        for cat in ["governance", "technical", "operational"]:
            rule = RuleCreate(
                rule_id="R1", name="N", category=cat,
                priority="LOW", directive="D",
            )
            assert rule.category == cat

    def test_all_priorities_accepted(self):
        """Accept all valid priority values."""
        for pri in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            rule = RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority=pri, directive="D",
            )
            assert rule.priority == pri

    def test_all_statuses_accepted(self):
        """Accept all valid status values."""
        for st in ["DRAFT", "ACTIVE", "DEPRECATED"]:
            rule = RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="LOW", directive="D", status=st,
            )
            assert rule.status == st

    def test_invalid_category_rejected(self):
        """Reject invalid category value."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="invalid",
                priority="LOW", directive="D",
            )
        assert "category" in str(exc_info.value)

    def test_invalid_priority_rejected(self):
        """Reject invalid priority value."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="ULTRA", directive="D",
            )
        assert "priority" in str(exc_info.value)

    def test_invalid_status_rejected(self):
        """Reject invalid status value."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="LOW", directive="D", status="INVALID",
            )
        assert "status" in str(exc_info.value)

    def test_empty_rule_id_rejected(self):
        """Reject empty rule_id."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="", name="N", category="governance",
                priority="LOW", directive="D",
            )
        assert "rule_id" in str(exc_info.value)

    def test_empty_name_rejected(self):
        """Reject empty name."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="", category="governance",
                priority="LOW", directive="D",
            )
        assert "name" in str(exc_info.value)

    def test_empty_directive_rejected(self):
        """Reject empty directive."""
        with pytest.raises(ValidationError) as exc_info:
            RuleCreate(
                rule_id="R1", name="N", category="governance",
                priority="LOW", directive="",
            )
        assert "directive" in str(exc_info.value)


class TestRuleUpdateValidation:
    """Validate RuleUpdate model constraints."""

    def test_valid_partial_update(self):
        """Accept partial update with valid values."""
        update = RuleUpdate(priority="CRITICAL", status="ACTIVE")
        assert update.priority == "CRITICAL"
        assert update.status == "ACTIVE"
        assert update.name is None

    def test_empty_update_allowed(self):
        """Accept update with no fields set."""
        update = RuleUpdate()
        assert update.name is None
        assert update.category is None

    def test_invalid_category_rejected(self):
        """Reject invalid category in update."""
        with pytest.raises(ValidationError):
            RuleUpdate(category="wrong")

    def test_invalid_priority_rejected(self):
        """Reject invalid priority in update."""
        with pytest.raises(ValidationError):
            RuleUpdate(priority="SUPER")

    def test_invalid_status_rejected(self):
        """Reject invalid status in update."""
        with pytest.raises(ValidationError):
            RuleUpdate(status="ARCHIVED")


class TestDecisionCreateValidation:
    """Validate DecisionCreate model constraints."""

    def test_valid_decision_create(self):
        """Accept valid decision creation data."""
        decision = DecisionCreate(
            decision_id="DECISION-099",
            name="Test Decision",
            context="Some context",
            rationale="Some reasoning",
        )
        assert decision.decision_id == "DECISION-099"
        assert decision.status == "PENDING"

    def test_all_statuses_accepted(self):
        """Accept all valid decision status values."""
        for st in ["PENDING", "APPROVED", "REJECTED"]:
            decision = DecisionCreate(
                decision_id="D1", name="N", context="C",
                rationale="R", status=st,
            )
            assert decision.status == st

    def test_invalid_status_rejected(self):
        """Reject invalid decision status."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="N", context="C",
                rationale="R", status="MAYBE",
            )

    def test_empty_decision_id_rejected(self):
        """Reject empty decision_id."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="", name="N", context="C", rationale="R",
            )

    def test_empty_name_rejected(self):
        """Reject empty name."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="", context="C", rationale="R",
            )

    def test_empty_context_rejected(self):
        """Reject empty context."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="N", context="", rationale="R",
            )

    def test_empty_rationale_rejected(self):
        """Reject empty rationale."""
        with pytest.raises(ValidationError):
            DecisionCreate(
                decision_id="D1", name="N", context="C", rationale="",
            )


class TestDecisionUpdateValidation:
    """Validate DecisionUpdate model constraints."""

    def test_valid_partial_update(self):
        """Accept partial update with valid status."""
        update = DecisionUpdate(status="APPROVED")
        assert update.status == "APPROVED"

    def test_invalid_status_rejected(self):
        """Reject invalid decision status in update."""
        with pytest.raises(ValidationError):
            DecisionUpdate(status="SUPERSEDED")


class TestTaskCreateValidation:
    """Validate TaskCreate model constraints."""

    def test_valid_task_create(self):
        """Accept valid task creation data."""
        task = TaskCreate(
            task_id="T-001",
            description="Implement feature",
            phase="development",
        )
        assert task.task_id == "T-001"
        assert task.status == "TODO"

    def test_empty_task_id_rejected(self):
        """Reject empty task_id."""
        with pytest.raises(ValidationError):
            TaskCreate(task_id="", description="D", phase="P")

    def test_empty_description_rejected(self):
        """Reject empty description."""
        with pytest.raises(ValidationError):
            TaskCreate(task_id="T1", description="", phase="P")

    def test_empty_phase_rejected(self):
        """Reject empty phase."""
        with pytest.raises(ValidationError):
            TaskCreate(task_id="T1", description="D", phase="")

    def test_optional_fields_default_none(self):
        """Optional fields default to None."""
        task = TaskCreate(task_id="T1", description="D", phase="P")
        assert task.agent_id is None
        assert task.body is None
        assert task.linked_rules is None
        assert task.gap_id is None
