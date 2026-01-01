"""
Tests for Kanren Constraint Engine (KAN-002).

Per RULE-023: Test Coverage Protocol
"""

import pytest
from governance.kanren_constraints import (
    trust_level,
    requires_supervisor,
    can_execute_priority,
    task_requires_evidence,
    valid_task_assignment,
    valid_rag_chunk,
    filter_rag_chunks,
    conflicting_priorities,
    find_rule_conflicts,
    assemble_context,
    validate_agent_for_task,
    AgentContext,
    TaskContext,
    RuleContext,
)


# =============================================================================
# Trust Level Tests (RULE-011)
# =============================================================================

class TestTrustLevel:
    """Trust level determination per RULE-011."""

    def test_expert_trust(self):
        """Score >= 0.9 is expert."""
        assert trust_level(0.95) == "expert"
        assert trust_level(0.90) == "expert"
        assert trust_level(1.0) == "expert"

    def test_trusted_trust(self):
        """Score >= 0.7 and < 0.9 is trusted."""
        assert trust_level(0.89) == "trusted"
        assert trust_level(0.75) == "trusted"
        assert trust_level(0.70) == "trusted"

    def test_supervised_trust(self):
        """Score >= 0.5 and < 0.7 is supervised."""
        assert trust_level(0.69) == "supervised"
        assert trust_level(0.55) == "supervised"
        assert trust_level(0.50) == "supervised"

    def test_restricted_trust(self):
        """Score < 0.5 is restricted."""
        assert trust_level(0.49) == "restricted"
        assert trust_level(0.25) == "restricted"
        assert trust_level(0.0) == "restricted"


class TestRequiresSupervisor:
    """Supervisor requirement per RULE-011."""

    def test_restricted_requires_supervisor(self):
        """Restricted agents need supervisor."""
        result = requires_supervisor("restricted")
        assert len(result) > 0
        assert result[0] is True

    def test_supervised_requires_supervisor(self):
        """Supervised agents need supervisor."""
        result = requires_supervisor("supervised")
        assert len(result) > 0
        assert result[0] is True

    def test_trusted_no_supervisor(self):
        """Trusted agents don't need supervisor."""
        result = requires_supervisor("trusted")
        assert len(result) > 0
        assert result[0] is False

    def test_expert_no_supervisor(self):
        """Expert agents don't need supervisor."""
        result = requires_supervisor("expert")
        assert len(result) > 0
        assert result[0] is False


class TestCanExecutePriority:
    """Task execution permissions per RULE-011."""

    def test_critical_expert_can_execute(self):
        """Expert can execute CRITICAL tasks."""
        result = can_execute_priority("expert", "CRITICAL")
        assert len(result) > 0
        assert result[0] is True

    def test_critical_trusted_can_execute(self):
        """Trusted can execute CRITICAL tasks."""
        result = can_execute_priority("trusted", "CRITICAL")
        assert len(result) > 0
        assert result[0] is True

    def test_critical_supervised_cannot_execute(self):
        """Supervised cannot execute CRITICAL tasks."""
        result = can_execute_priority("supervised", "CRITICAL")
        assert len(result) > 0
        assert result[0] is False

    def test_critical_restricted_cannot_execute(self):
        """Restricted cannot execute CRITICAL tasks."""
        result = can_execute_priority("restricted", "CRITICAL")
        assert len(result) > 0
        assert result[0] is False

    def test_high_supervised_can_execute(self):
        """Supervised can execute HIGH tasks."""
        result = can_execute_priority("supervised", "HIGH")
        assert len(result) > 0
        assert result[0] is True

    def test_high_restricted_cannot_execute(self):
        """Restricted cannot execute HIGH tasks."""
        result = can_execute_priority("restricted", "HIGH")
        assert len(result) > 0
        assert result[0] is False

    def test_medium_all_can_execute(self):
        """All trust levels can execute MEDIUM tasks."""
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "MEDIUM")
            assert len(result) > 0
            assert result[0] is True

    def test_low_all_can_execute(self):
        """All trust levels can execute LOW tasks."""
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "LOW")
            assert len(result) > 0
            assert result[0] is True


# =============================================================================
# Task Validation Tests (RULE-014, RULE-028)
# =============================================================================

class TestTaskRequiresEvidence:
    """Evidence requirements per RULE-028."""

    def test_critical_requires_evidence(self):
        """CRITICAL tasks require evidence."""
        result = task_requires_evidence("CRITICAL")
        assert len(result) > 0
        assert result[0] is True

    def test_high_requires_evidence(self):
        """HIGH tasks require evidence."""
        result = task_requires_evidence("HIGH")
        assert len(result) > 0
        assert result[0] is True

    def test_medium_no_evidence(self):
        """MEDIUM tasks don't require evidence."""
        result = task_requires_evidence("MEDIUM")
        assert len(result) > 0
        assert result[0] is False

    def test_low_no_evidence(self):
        """LOW tasks don't require evidence."""
        result = task_requires_evidence("LOW")
        assert len(result) > 0
        assert result[0] is False


class TestValidTaskAssignment:
    """Task assignment validation per RULE-011, RULE-014."""

    def test_expert_critical_valid(self):
        """Expert can be assigned CRITICAL tasks."""
        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)
        result = valid_task_assignment(agent, task)

        assert result["valid"] is True
        assert result["trust_level"] == "expert"
        assert result["can_execute"] is True
        assert result["requires_supervisor"] is False
        assert result["requires_evidence"] is True

    def test_supervised_critical_invalid(self):
        """Supervised cannot be assigned CRITICAL tasks."""
        agent = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
        task = TaskContext("TASK-002", "CRITICAL", True)
        result = valid_task_assignment(agent, task)

        assert result["valid"] is False
        assert result["trust_level"] == "supervised"
        assert result["can_execute"] is False
        assert result["requires_supervisor"] is True

    def test_supervised_medium_valid(self):
        """Supervised can be assigned MEDIUM tasks."""
        agent = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
        task = TaskContext("TASK-003", "MEDIUM", False)
        result = valid_task_assignment(agent, task)

        assert result["valid"] is True
        assert result["trust_level"] == "supervised"
        assert result["can_execute"] is True
        assert result["requires_supervisor"] is True
        assert result["requires_evidence"] is False

    def test_constraints_checked_included(self):
        """Validation result includes constraints checked."""
        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)
        result = valid_task_assignment(agent, task)

        assert "constraints_checked" in result
        assert len(result["constraints_checked"]) >= 3
        assert any("RULE-011" in c for c in result["constraints_checked"])


# =============================================================================
# RAG Validation Tests (RULE-007)
# =============================================================================

class TestValidRagChunk:
    """RAG chunk validation per RULE-007."""

    def test_valid_typedb_chunk(self):
        """Valid TypeDB chunk passes validation."""
        result = valid_rag_chunk("typedb", True, "rule")
        assert len(result) > 0
        assert result[0] is True

    def test_valid_chromadb_chunk(self):
        """Valid ChromaDB chunk passes validation."""
        result = valid_rag_chunk("chromadb", True, "evidence")
        assert len(result) > 0
        assert result[0] is True

    def test_invalid_source(self):
        """Invalid source fails validation."""
        result = valid_rag_chunk("external", True, "rule")
        assert len(result) == 0  # No valid solutions

    def test_unverified_chunk(self):
        """Unverified chunk fails validation."""
        result = valid_rag_chunk("typedb", False, "rule")
        assert len(result) == 0  # No valid solutions

    def test_invalid_type(self):
        """Invalid chunk type fails validation."""
        result = valid_rag_chunk("typedb", True, "unknown")
        assert len(result) == 0  # No valid solutions


class TestFilterRagChunks:
    """RAG chunk filtering per RULE-007."""

    def test_filter_mixed_chunks(self):
        """Filters mixed valid/invalid chunks."""
        chunks = [
            {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
            {"id": 2, "source": "external", "verified": False, "type": "unknown"},
            {"id": 3, "source": "chromadb", "verified": True, "type": "evidence"},
            {"id": 4, "source": "evidence", "verified": True, "type": "decision"},
        ]
        valid = filter_rag_chunks(chunks)

        assert len(valid) == 3
        assert all(c["source"] in ["typedb", "chromadb", "evidence"] for c in valid)

    def test_filter_empty_list(self):
        """Handles empty chunk list."""
        valid = filter_rag_chunks([])
        assert valid == []

    def test_filter_all_invalid(self):
        """Returns empty when all chunks invalid."""
        chunks = [
            {"id": 1, "source": "external", "verified": False, "type": "unknown"},
        ]
        valid = filter_rag_chunks(chunks)
        assert valid == []


# =============================================================================
# Rule Conflict Detection Tests (RULE-011)
# =============================================================================

class TestRuleConflicts:
    """Rule conflict detection per RULE-011."""

    def test_conflicting_priorities(self):
        """Detects priority conflicts in same category."""
        rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
        rule2 = RuleContext("RULE-002", "MEDIUM", "ACTIVE", "governance")

        assert conflicting_priorities(rule1, rule2) is True

    def test_no_conflict_different_category(self):
        """No conflict for different categories."""
        rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
        rule2 = RuleContext("RULE-002", "MEDIUM", "ACTIVE", "technical")

        assert conflicting_priorities(rule1, rule2) is False

    def test_no_conflict_same_priority(self):
        """No conflict for same priority."""
        rule1 = RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance")
        rule2 = RuleContext("RULE-002", "CRITICAL", "ACTIVE", "governance")

        assert conflicting_priorities(rule1, rule2) is False

    def test_find_all_conflicts(self):
        """Finds all conflicts in rule set."""
        rules = [
            RuleContext("RULE-001", "CRITICAL", "ACTIVE", "governance"),
            RuleContext("RULE-002", "HIGH", "ACTIVE", "governance"),
            RuleContext("RULE-003", "MEDIUM", "ACTIVE", "governance"),
            RuleContext("RULE-004", "HIGH", "ACTIVE", "technical"),
        ]
        conflicts = find_rule_conflicts(rules)

        # RULE-001 conflicts with RULE-002 and RULE-003
        # RULE-002 conflicts with RULE-003
        assert len(conflicts) == 3


# =============================================================================
# Context Assembly Tests
# =============================================================================

class TestAssembleContext:
    """Context assembly for LLM prompts."""

    def test_assemble_valid_context(self):
        """Assembles valid context with filtered chunks."""
        agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)
        chunks = [
            {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
            {"id": 2, "source": "external", "verified": False, "type": "unknown"},
        ]

        context = assemble_context(agent, task, chunks)

        assert context["assignment_valid"] is True
        assert context["agent"]["trust_level"] == "expert"
        assert context["task"]["requires_evidence"] is True
        assert len(context["rag_chunks"]) == 1
        assert "RULE-007: RAG validation" in context["constraints_applied"]


class TestValidateAgentForTask:
    """Quick validation helper function."""

    def test_validate_expert_critical(self):
        """Quick validation for expert + CRITICAL."""
        result = validate_agent_for_task("AGENT-001", 0.95, "CRITICAL")
        assert result["valid"] is True

    def test_validate_restricted_critical(self):
        """Quick validation for restricted + CRITICAL."""
        result = validate_agent_for_task("AGENT-002", 0.35, "CRITICAL")
        assert result["valid"] is False
