"""
Unit tests for Kanren Task Validation Constraints.

Per DOC-SIZE-01-v1: Tests for kanren/tasks.py module.
Tests: task_requires_evidence, valid_task_assignment, validate_agent_for_task.
"""

import pytest

from governance.kanren.models import AgentContext, TaskContext
from governance.kanren.tasks import (
    task_requires_evidence,
    valid_task_assignment,
    validate_agent_for_task,
)


class TestTaskRequiresEvidence:
    """Tests for task_requires_evidence()."""

    def test_critical_requires(self):
        result = task_requires_evidence("CRITICAL")
        assert result and result[0] is True

    def test_high_requires(self):
        result = task_requires_evidence("HIGH")
        assert result and result[0] is True

    def test_medium_no_evidence(self):
        result = task_requires_evidence("MEDIUM")
        assert result and result[0] is False

    def test_low_no_evidence(self):
        result = task_requires_evidence("LOW")
        assert result and result[0] is False


class TestValidTaskAssignment:
    """Tests for valid_task_assignment()."""

    def test_expert_critical(self):
        agent = AgentContext(agent_id="A-1", name="Expert", trust_score=0.95, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="CRITICAL", requires_evidence=True)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is True
        assert result["trust_level"] == "expert"
        assert result["requires_supervisor"] is False

    def test_restricted_critical_invalid(self):
        agent = AgentContext(agent_id="A-2", name="New", trust_score=0.3, agent_type="test-agent")
        task = TaskContext(task_id="T-1", priority="CRITICAL", requires_evidence=True)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is False

    def test_supervised_medium_valid(self):
        agent = AgentContext(agent_id="A-3", name="Mid", trust_score=0.6, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="MEDIUM", requires_evidence=False)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is True
        assert result["requires_supervisor"] is True

    def test_contains_constraints(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.95, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="LOW", requires_evidence=False)
        result = valid_task_assignment(agent, task)
        assert len(result["constraints_checked"]) == 3
        assert any("RULE-011" in c for c in result["constraints_checked"])

    def test_result_has_all_fields(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.8, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="HIGH", requires_evidence=True)
        result = valid_task_assignment(agent, task)
        assert "valid" in result
        assert "agent_id" in result
        assert "task_id" in result
        assert "trust_level" in result
        assert "can_execute" in result
        assert "requires_supervisor" in result
        assert "requires_evidence" in result


class TestValidateAgentForTask:
    """Tests for validate_agent_for_task()."""

    def test_high_trust_high_priority(self):
        result = validate_agent_for_task("code-agent", 0.85, "HIGH")
        assert result["valid"] is True

    def test_low_trust_critical(self):
        result = validate_agent_for_task("new-agent", 0.3, "CRITICAL")
        assert result["valid"] is False

    def test_any_trust_low_priority(self):
        result = validate_agent_for_task("any-agent", 0.1, "LOW")
        assert result["valid"] is True

    def test_returns_dict(self):
        result = validate_agent_for_task("agent", 0.5, "MEDIUM")
        assert isinstance(result, dict)
        assert result["agent_id"] == "agent"
