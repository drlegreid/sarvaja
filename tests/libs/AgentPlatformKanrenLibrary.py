"""
Robot Framework Library for Agent Platform Kanren Integration Tests.

Per RD-AGENT-TESTING: ATEST-006 - Kanren-Agent Integration.
Split from test_agent_platform.py per DOC-SIZE-01-v1.
"""
from pathlib import Path
from unittest.mock import MagicMock
from robot.api.deco import keyword


class AgentPlatformKanrenLibrary:
    """Library for Kanren-agent integration tests (ATEST-006)."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    @keyword("Kanren Imports Available")
    def kanren_imports_available(self):
        """Kanren module can be imported."""
        try:
            from governance.kanren_constraints import (
                KanrenRAGFilter,
                AgentContext,
                TaskContext,
                trust_level,
                valid_task_assignment,
            )
            return {
                "rag_filter": KanrenRAGFilter is not None,
                "agent_context": AgentContext is not None,
                "task_context": TaskContext is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Expert Agent On Critical Task")
    def expert_agent_on_critical_task(self):
        """Expert agent (trust >= 0.9) can execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import (
                AgentContext, TaskContext, valid_task_assignment
            )

            expert = AgentContext("AGENT-EXP-001", "Expert Agent", 0.95, "claude-code")
            critical_task = TaskContext("TASK-CRIT-001", "CRITICAL", True)
            result = valid_task_assignment(expert, critical_task)

            return {
                "valid": result["valid"] is True,
                "trust_expert": result["trust_level"] == "expert",
                "can_execute": result["can_execute"] is True,
                "no_supervisor": result["requires_supervisor"] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Supervised Agent Blocked From Critical")
    def supervised_agent_blocked_from_critical(self):
        """Supervised agent (trust 0.5-0.7) cannot execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import (
                AgentContext, TaskContext, valid_task_assignment
            )

            supervised = AgentContext("AGENT-SUP-001", "Supervised Agent", 0.55, "sync-agent")
            critical_task = TaskContext("TASK-CRIT-002", "CRITICAL", True)
            result = valid_task_assignment(supervised, critical_task)

            return {
                "invalid": result["valid"] is False,
                "trust_supervised": result["trust_level"] == "supervised",
                "cannot_execute": result["can_execute"] is False,
                "needs_supervisor": result["requires_supervisor"] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Level Boundaries")
    def trust_level_boundaries(self):
        """Trust level boundaries are correctly enforced."""
        try:
            from governance.kanren_constraints import trust_level

            return {
                "expert_at_90": trust_level(0.90) == "expert",
                "trusted_at_89": trust_level(0.89) == "trusted",
                "trusted_at_70": trust_level(0.70) == "trusted",
                "supervised_at_69": trust_level(0.69) == "supervised",
                "supervised_at_50": trust_level(0.50) == "supervised",
                "restricted_at_49": trust_level(0.49) == "restricted"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Kanren RAG Filter With Agent Context")
    def kanren_rag_filter_with_agent_context(self):
        """KanrenRAGFilter integrates with agent context."""
        try:
            from governance.kanren_constraints import (
                KanrenRAGFilter, AgentContext, TaskContext
            )

            mock_store = MagicMock()
            mock_vec = MagicMock()
            mock_vec.id = "vec-rule-001"
            mock_vec.content = "governance constraint"
            mock_vec.source_type = "rule"
            mock_vec.source = "RULE-011"
            mock_store.get_all_vectors.return_value = [mock_vec]

            rag_filter = KanrenRAGFilter(vector_store=mock_store)
            expert = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
            task = TaskContext("TASK-001", "CRITICAL", True)

            context = rag_filter.search_for_task(
                query_text="governance",
                task_context=task,
                agent_context=expert
            )

            return {
                "assignment_valid": context["assignment_valid"] is True,
                "has_constraints": "constraints_applied" in context,
                "has_rule": any("RULE-011" in c for c in context["constraints_applied"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
