"""
Unit tests for Kanren Context Assembly.

Per DOC-SIZE-01-v1: Tests for kanren/assembly.py module.
Tests: assemble_context function.
"""

import pytest
pytest.importorskip("kanren")  # BUG-014: skip if kanren not installed

from governance.kanren.models import AgentContext, TaskContext
from governance.kanren.assembly import assemble_context


class TestAssembleContext:
    """Tests for assemble_context()."""

    def test_basic_valid(self):
        agent = AgentContext(agent_id="A-1", name="Expert", trust_score=0.95, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="HIGH", requires_evidence=True)
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "test"},
        ]
        ctx = assemble_context(agent, task, chunks)
        assert ctx["assignment_valid"] is True
        assert ctx["agent"]["id"] == "A-1"
        assert ctx["task"]["id"] == "T-1"
        assert len(ctx["rag_chunks"]) == 1

    def test_invalid_assignment(self):
        agent = AgentContext(agent_id="A-2", name="New", trust_score=0.2, agent_type="test-agent")
        task = TaskContext(task_id="T-1", priority="CRITICAL", requires_evidence=True)
        ctx = assemble_context(agent, task, [])
        assert ctx["assignment_valid"] is False

    def test_filters_invalid_chunks(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.95, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="LOW", requires_evidence=False)
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "valid"},
            {"source": "unknown", "verified": False, "type": "spam", "content": "invalid"},
        ]
        ctx = assemble_context(agent, task, chunks)
        assert len(ctx["rag_chunks"]) == 1  # Only the valid chunk

    def test_empty_chunks(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.9, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="MEDIUM", requires_evidence=False)
        ctx = assemble_context(agent, task, [])
        assert ctx["rag_chunks"] == []

    def test_constraints_applied(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.9, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="MEDIUM", requires_evidence=False)
        ctx = assemble_context(agent, task, [])
        assert "RULE-007: RAG validation" in ctx["constraints_applied"]
        assert len(ctx["constraints_applied"]) == 4  # 3 from tasks + 1 RAG

    def test_trust_level_in_context(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.6, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="LOW", requires_evidence=False)
        ctx = assemble_context(agent, task, [])
        assert ctx["agent"]["trust_level"] == "supervised"
        assert ctx["agent"]["requires_supervisor"] is True

    def test_evidence_requirement_in_context(self):
        agent = AgentContext(agent_id="A-1", name="E", trust_score=0.95, agent_type="claude-code")
        task = TaskContext(task_id="T-1", priority="CRITICAL", requires_evidence=True)
        ctx = assemble_context(agent, task, [])
        assert ctx["task"]["requires_evidence"] is True
