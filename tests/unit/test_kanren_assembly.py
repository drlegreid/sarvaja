"""
Tests for Kanren context assembly.

Per KAN-002: Full context assembly with constraint validation.
Covers assemble_context with trust, RAG, and evidence requirements.

Created: 2026-01-30
"""

import pytest

from governance.kanren.models import AgentContext, TaskContext
from governance.kanren.assembly import assemble_context


class TestAssembleContext:
    """Test assemble_context function."""

    def test_expert_critical_with_valid_chunks(self):
        agent = AgentContext("A1", "Expert", 0.95, "claude-code")
        task = TaskContext("T1", "CRITICAL", True)
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "R1"},
            {"source": "bad", "verified": False, "type": "other", "content": "bad"},
        ]
        ctx = assemble_context(agent, task, chunks)
        assert ctx["assignment_valid"] is True
        assert ctx["agent"]["trust_level"] == "expert"
        assert ctx["agent"]["requires_supervisor"] is False
        assert ctx["task"]["priority"] == "CRITICAL"
        assert ctx["task"]["requires_evidence"] is True
        assert len(ctx["rag_chunks"]) == 1  # Only valid chunk passes
        assert "RULE-007: RAG validation" in ctx["constraints_applied"]

    def test_restricted_critical_invalid(self):
        agent = AgentContext("A2", "Newbie", 0.3, "claude-code")
        task = TaskContext("T2", "CRITICAL", True)
        ctx = assemble_context(agent, task, [])
        assert ctx["assignment_valid"] is False
        assert ctx["agent"]["trust_level"] == "restricted"
        assert ctx["agent"]["requires_supervisor"] is True

    def test_supervised_medium_no_evidence(self):
        agent = AgentContext("A3", "Mid", 0.6, "claude-code")
        task = TaskContext("T3", "MEDIUM", False)
        ctx = assemble_context(agent, task, [])
        assert ctx["assignment_valid"] is True
        assert ctx["task"]["requires_evidence"] is False
        assert ctx["rag_chunks"] == []

    def test_all_chunks_filtered(self):
        agent = AgentContext("A1", "Expert", 0.95, "claude-code")
        task = TaskContext("T1", "LOW", False)
        bad_chunks = [
            {"source": "unknown", "verified": True, "type": "rule"},
            {"source": "typedb", "verified": False, "type": "rule"},
        ]
        ctx = assemble_context(agent, task, bad_chunks)
        assert ctx["rag_chunks"] == []

    def test_multiple_valid_chunks(self):
        agent = AgentContext("A1", "Expert", 0.95, "claude-code")
        task = TaskContext("T1", "HIGH", True)
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule"},
            {"source": "chromadb", "verified": True, "type": "evidence"},
            {"source": "evidence", "verified": True, "type": "task"},
        ]
        ctx = assemble_context(agent, task, chunks)
        assert len(ctx["rag_chunks"]) == 3

    def test_constraints_list_complete(self):
        agent = AgentContext("A1", "Expert", 0.95, "claude-code")
        task = TaskContext("T1", "LOW", False)
        ctx = assemble_context(agent, task, [])
        assert len(ctx["constraints_applied"]) == 4  # 3 from assignment + 1 RAG
        assert "RULE-011" in ctx["constraints_applied"][0]
        assert "RULE-014" in ctx["constraints_applied"][1]
        assert "RULE-028" in ctx["constraints_applied"][2]
        assert "RULE-007" in ctx["constraints_applied"][3]
