"""
Unit tests for Kanren Context Assembly.

Per DOC-SIZE-01-v1: Tests for kanren/assembly.py module.
Tests: assemble_context().
"""

import pytest
pytest.importorskip("kanren")  # BUG-014: skip if kanren not installed

from governance.kanren.assembly import assemble_context
from governance.kanren.models import AgentContext, TaskContext


class TestAssembleContext:
    def test_basic_assembly(self):
        agent = AgentContext("A-1", "Expert", 0.95, "code")
        task = TaskContext("T-1", "HIGH", True)
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "R1"},
        ]
        result = assemble_context(agent, task, chunks)
        assert result["assignment_valid"] is True
        assert result["agent"]["id"] == "A-1"
        assert result["task"]["id"] == "T-1"
        assert len(result["rag_chunks"]) == 1

    def test_filters_invalid_chunks(self):
        agent = AgentContext("A-1", "Expert", 0.95, "code")
        task = TaskContext("T-1", "MEDIUM", False)
        chunks = [
            {"source": "typedb", "verified": True, "type": "rule", "content": "Valid"},
            {"source": "bad", "verified": True, "type": "rule", "content": "Invalid"},
        ]
        result = assemble_context(agent, task, chunks)
        assert len(result["rag_chunks"]) == 1

    def test_restricted_agent(self):
        agent = AgentContext("A-2", "Newbie", 0.3, "code")
        task = TaskContext("T-2", "CRITICAL", True)
        result = assemble_context(agent, task, [])
        assert result["assignment_valid"] is False
        assert result["agent"]["requires_supervisor"] is True

    def test_constraints_include_rag(self):
        agent = AgentContext("A-1", "Test", 0.85, "code")
        task = TaskContext("T-1", "HIGH", True)
        result = assemble_context(agent, task, [])
        assert any("RULE-007" in c for c in result["constraints_applied"])

    def test_trust_level_in_result(self):
        agent = AgentContext("A-1", "Test", 0.6, "code")
        task = TaskContext("T-1", "MEDIUM", False)
        result = assemble_context(agent, task, [])
        assert result["agent"]["trust_level"] == "supervised"
