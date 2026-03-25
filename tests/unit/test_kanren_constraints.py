"""
Tests for Kanren constraint modules.

Per GOV-BICAM-01-v1, RULE-007, RULE-011, RULE-014, RULE-028:
Trust constraints, RAG validation, conflict detection, task validation.

Created: 2026-01-30
"""

import pytest
pytest.importorskip("kanren")  # BUG-014: skip if kanren not installed

from governance.kanren.models import AgentContext, TaskContext, RuleContext
from governance.kanren.trust import trust_level, requires_supervisor, can_execute_priority
from governance.kanren.rag import (
    ALLOWED_SOURCES, TRUSTED_TYPES,
    valid_rag_chunk, filter_rag_chunks,
)
from governance.kanren.conflicts import conflicting_priorities, find_rule_conflicts
from governance.kanren.tasks import (
    task_requires_evidence,
    valid_task_assignment,
    validate_agent_for_task,
)


# =========================================================================
# Models
# =========================================================================

class TestAgentContext:
    def test_create(self):
        a = AgentContext(agent_id="A1", name="Test", trust_score=0.9, agent_type="claude-code")
        assert a.agent_id == "A1"
        assert a.trust_score == 0.9

class TestTaskContext:
    def test_create(self):
        t = TaskContext(task_id="T1", priority="HIGH", requires_evidence=True)
        assert t.assigned_agent is None

    def test_with_agent(self):
        t = TaskContext(task_id="T1", priority="MEDIUM", requires_evidence=False, assigned_agent="A1")
        assert t.assigned_agent == "A1"

class TestRuleContext:
    def test_create(self):
        r = RuleContext(rule_id="R1", priority="HIGH", status="ACTIVE", category="governance")
        assert r.rule_id == "R1"


# =========================================================================
# Trust Constraints (GOV-BICAM-01-v1)
# =========================================================================

class TestTrustLevel:
    def test_expert(self):
        assert trust_level(0.95) == "expert"
        assert trust_level(0.9) == "expert"

    def test_trusted(self):
        assert trust_level(0.8) == "trusted"
        assert trust_level(0.7) == "trusted"

    def test_supervised(self):
        assert trust_level(0.6) == "supervised"
        assert trust_level(0.5) == "supervised"

    def test_restricted(self):
        assert trust_level(0.4) == "restricted"
        assert trust_level(0.0) == "restricted"

    def test_boundary_values(self):
        assert trust_level(0.9) == "expert"
        assert trust_level(0.89) == "trusted"
        assert trust_level(0.7) == "trusted"
        assert trust_level(0.69) == "supervised"
        assert trust_level(0.5) == "supervised"
        assert trust_level(0.49) == "restricted"


class TestRequiresSupervisor:
    def test_restricted_needs_supervisor(self):
        result = requires_supervisor("restricted")
        assert len(result) > 0 and result[0] is True

    def test_supervised_needs_supervisor(self):
        result = requires_supervisor("supervised")
        assert len(result) > 0 and result[0] is True

    def test_trusted_no_supervisor(self):
        result = requires_supervisor("trusted")
        assert len(result) > 0 and result[0] is False

    def test_expert_no_supervisor(self):
        result = requires_supervisor("expert")
        assert len(result) > 0 and result[0] is False


class TestCanExecutePriority:
    def test_expert_can_execute_critical(self):
        result = can_execute_priority("expert", "CRITICAL")
        assert len(result) > 0 and result[0] is True

    def test_trusted_can_execute_critical(self):
        result = can_execute_priority("trusted", "CRITICAL")
        assert len(result) > 0 and result[0] is True

    def test_supervised_cannot_execute_critical(self):
        result = can_execute_priority("supervised", "CRITICAL")
        assert len(result) > 0 and result[0] is False

    def test_restricted_cannot_execute_critical(self):
        result = can_execute_priority("restricted", "CRITICAL")
        assert len(result) > 0 and result[0] is False

    def test_all_can_execute_medium(self):
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "MEDIUM")
            assert len(result) > 0 and result[0] is True, f"{trust} should execute MEDIUM"

    def test_all_can_execute_low(self):
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "LOW")
            assert len(result) > 0 and result[0] is True


# =========================================================================
# RAG Validation (RULE-007)
# =========================================================================

class TestRagConstants:
    def test_allowed_sources(self):
        assert "typedb" in ALLOWED_SOURCES
        assert "chromadb" in ALLOWED_SOURCES
        assert "evidence" in ALLOWED_SOURCES

    def test_trusted_types(self):
        assert "rule" in TRUSTED_TYPES
        assert "decision" in TRUSTED_TYPES
        assert "evidence" in TRUSTED_TYPES
        assert "task" in TRUSTED_TYPES


class TestValidRagChunk:
    def test_valid_chunk(self):
        result = valid_rag_chunk("typedb", True, "rule")
        assert len(result) > 0 and result[0] is True

    def test_invalid_source(self):
        result = valid_rag_chunk("unknown_source", True, "rule")
        assert len(result) == 0  # No solution

    def test_unverified(self):
        result = valid_rag_chunk("typedb", False, "rule")
        assert len(result) == 0  # No solution

    def test_invalid_type(self):
        result = valid_rag_chunk("typedb", True, "random")
        assert len(result) == 0  # No solution


class TestFilterRagChunks:
    def test_filters_valid(self):
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "A"},
            {"source": "unknown", "verified": True, "type": "rule", "content": "B"},
            {"source": "typedb", "verified": False, "type": "rule", "content": "C"},
            {"source": "chromadb", "verified": True, "type": "evidence", "content": "D"},
        ]
        result = filter_rag_chunks(chunks)
        assert len(result) == 2
        assert result[0]["content"] == "A"
        assert result[1]["content"] == "D"

    def test_empty_input(self):
        assert filter_rag_chunks([]) == []

    def test_all_invalid(self):
        chunks = [
            {"source": "bad", "verified": True, "type": "rule"},
            {"source": "typedb", "verified": False, "type": "rule"},
        ]
        assert filter_rag_chunks(chunks) == []

    def test_missing_fields_rejected(self):
        chunks = [{"content": "orphan"}]  # Missing source, verified, type
        assert filter_rag_chunks(chunks) == []


# =========================================================================
# Conflict Detection (RULE-011)
# =========================================================================

class TestConflictingPriorities:
    def test_same_category_different_priority(self):
        r1 = RuleContext("R1", "HIGH", "ACTIVE", "governance")
        r2 = RuleContext("R2", "LOW", "ACTIVE", "governance")
        assert conflicting_priorities(r1, r2) is True

    def test_same_category_same_priority(self):
        r1 = RuleContext("R1", "HIGH", "ACTIVE", "governance")
        r2 = RuleContext("R2", "HIGH", "ACTIVE", "governance")
        assert conflicting_priorities(r1, r2) is False

    def test_different_category(self):
        r1 = RuleContext("R1", "HIGH", "ACTIVE", "governance")
        r2 = RuleContext("R2", "LOW", "ACTIVE", "technical")
        assert conflicting_priorities(r1, r2) is False


class TestFindRuleConflicts:
    def test_no_conflicts(self):
        rules = [
            RuleContext("R1", "HIGH", "ACTIVE", "governance"),
            RuleContext("R2", "HIGH", "ACTIVE", "governance"),
        ]
        assert find_rule_conflicts(rules) == []

    def test_one_conflict(self):
        rules = [
            RuleContext("R1", "HIGH", "ACTIVE", "governance"),
            RuleContext("R2", "LOW", "ACTIVE", "governance"),
        ]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) == 1
        assert conflicts[0][0] == "R1"
        assert conflicts[0][1] == "R2"

    def test_multiple_conflicts(self):
        rules = [
            RuleContext("R1", "HIGH", "ACTIVE", "governance"),
            RuleContext("R2", "LOW", "ACTIVE", "governance"),
            RuleContext("R3", "CRITICAL", "ACTIVE", "governance"),
        ]
        conflicts = find_rule_conflicts(rules)
        assert len(conflicts) == 3  # R1-R2, R1-R3, R2-R3

    def test_empty_rules(self):
        assert find_rule_conflicts([]) == []


# =========================================================================
# Task Validation (RULE-014, RULE-028)
# =========================================================================

class TestTaskRequiresEvidence:
    def test_critical_requires(self):
        result = task_requires_evidence("CRITICAL")
        assert len(result) > 0 and result[0] is True

    def test_high_requires(self):
        result = task_requires_evidence("HIGH")
        assert len(result) > 0 and result[0] is True

    def test_medium_no_evidence(self):
        result = task_requires_evidence("MEDIUM")
        assert len(result) > 0 and result[0] is False

    def test_low_no_evidence(self):
        result = task_requires_evidence("LOW")
        assert len(result) > 0 and result[0] is False


class TestValidTaskAssignment:
    def test_expert_critical_valid(self):
        agent = AgentContext("A1", "Expert", 0.95, "claude-code")
        task = TaskContext("T1", "CRITICAL", True)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is True
        assert result["trust_level"] == "expert"
        assert result["requires_supervisor"] is False

    def test_restricted_critical_invalid(self):
        agent = AgentContext("A1", "Newbie", 0.3, "claude-code")
        task = TaskContext("T1", "CRITICAL", True)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is False
        assert result["trust_level"] == "restricted"
        assert result["requires_supervisor"] is True

    def test_supervised_medium_valid(self):
        agent = AgentContext("A1", "Mid", 0.6, "claude-code")
        task = TaskContext("T1", "MEDIUM", False)
        result = valid_task_assignment(agent, task)
        assert result["valid"] is True
        assert result["trust_level"] == "supervised"


class TestValidateAgentForTask:
    def test_quick_validation(self):
        result = validate_agent_for_task("A1", 0.95, "CRITICAL")
        assert result["valid"] is True
        assert result["agent_id"] == "A1"

    def test_quick_validation_fails(self):
        result = validate_agent_for_task("A2", 0.3, "CRITICAL")
        assert result["valid"] is False
