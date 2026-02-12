"""
Unit tests for Kanren Task Validation Constraints.

Per DOC-SIZE-01-v1: Tests for kanren/tasks.py module.
Tests: task_requires_evidence(), valid_task_assignment(), validate_agent_for_task().
"""

from governance.kanren.tasks import (
    task_requires_evidence,
    valid_task_assignment,
    validate_agent_for_task,
)
from governance.kanren.models import AgentContext, TaskContext


class TestTaskRequiresEvidence:
    def test_critical(self):
        result = task_requires_evidence("CRITICAL")
        assert result and result[0] is True

    def test_high(self):
        result = task_requires_evidence("HIGH")
        assert result and result[0] is True

    def test_medium(self):
        result = task_requires_evidence("MEDIUM")
        assert result and result[0] is False

    def test_low(self):
        result = task_requires_evidence("LOW")
        assert result and result[0] is False


class TestValidTaskAssignment:
    def test_expert_critical(self):
        agent = AgentContext("A-1", "Expert", 0.95, "code")
        task = TaskContext("T-1", "CRITICAL", True)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is True
        assert result["trust_level"] == "expert"
        assert result["can_execute"] is True
        assert result["requires_supervisor"] is False

    def test_restricted_critical(self):
        agent = AgentContext("A-2", "Newbie", 0.3, "code")
        task = TaskContext("T-2", "CRITICAL", True)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is False
        assert result["trust_level"] == "restricted"
        assert result["requires_supervisor"] is True

    def test_supervised_medium(self):
        agent = AgentContext("A-3", "Mid", 0.6, "code")
        task = TaskContext("T-3", "MEDIUM", False)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is True
        assert result["requires_evidence"] is False

    def test_constraints_listed(self):
        agent = AgentContext("A-1", "Test", 0.85, "code")
        task = TaskContext("T-1", "HIGH", True)
        result = valid_task_assignment(agent, task)
        assert len(result["constraints_checked"]) == 3
        assert "RULE-011" in result["constraints_checked"][0]


class TestValidateAgentForTask:
    def test_expert_high(self):
        result = validate_agent_for_task("code-agent", 0.95, "HIGH")
        assert result["valid"] is True
        assert result["agent_id"] == "code-agent"

    def test_restricted_critical(self):
        result = validate_agent_for_task("new-agent", 0.2, "CRITICAL")
        assert result["valid"] is False

    def test_any_low(self):
        result = validate_agent_for_task("any", 0.1, "LOW")
        assert result["valid"] is True
