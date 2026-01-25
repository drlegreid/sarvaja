"""
Robot Framework Library for Kanren Task Validation Tests.

Per KAN-002: Kanren Constraint Engine - Task Module.
Split from KanrenConstraintsLibrary.py per DOC-SIZE-01-v1.

Covers: Task Evidence Requirements, Task Assignment Validation.
"""
from robot.api.deco import keyword


class KanrenTaskLibrary:
    """Library for testing Kanren task constraints."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Task Evidence Requirements Tests
    # =========================================================================

    @keyword("Critical Requires Evidence")
    def critical_requires_evidence(self):
        """CRITICAL tasks require evidence."""
        try:
            from governance.kanren_constraints import task_requires_evidence
            result = task_requires_evidence("CRITICAL")
            return {
                "has_result": len(result) > 0,
                "requires": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("High Requires Evidence")
    def high_requires_evidence(self):
        """HIGH tasks require evidence."""
        try:
            from governance.kanren_constraints import task_requires_evidence
            result = task_requires_evidence("HIGH")
            return {
                "has_result": len(result) > 0,
                "requires": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Medium No Evidence")
    def medium_no_evidence(self):
        """MEDIUM tasks don't require evidence."""
        try:
            from governance.kanren_constraints import task_requires_evidence
            result = task_requires_evidence("MEDIUM")
            return {
                "has_result": len(result) > 0,
                "no_evidence": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Low No Evidence")
    def low_no_evidence(self):
        """LOW tasks don't require evidence."""
        try:
            from governance.kanren_constraints import task_requires_evidence
            result = task_requires_evidence("LOW")
            return {
                "has_result": len(result) > 0,
                "no_evidence": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Task Assignment Validation Tests
    # =========================================================================

    @keyword("Expert Critical Valid")
    def expert_critical_valid(self):
        """Expert can be assigned CRITICAL tasks."""
        try:
            from governance.kanren_constraints import valid_task_assignment, AgentContext, TaskContext
            agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
            task = TaskContext("TASK-001", "CRITICAL", True)
            result = valid_task_assignment(agent, task)
            return {
                "valid": result["valid"] is True,
                "trust_level": result["trust_level"] == "expert",
                "can_execute": result["can_execute"] is True,
                "no_supervisor": result["requires_supervisor"] is False,
                "requires_evidence": result["requires_evidence"] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Supervised Critical Invalid")
    def supervised_critical_invalid(self):
        """Supervised cannot be assigned CRITICAL tasks."""
        try:
            from governance.kanren_constraints import valid_task_assignment, AgentContext, TaskContext
            agent = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
            task = TaskContext("TASK-002", "CRITICAL", True)
            result = valid_task_assignment(agent, task)
            return {
                "invalid": result["valid"] is False,
                "trust_level": result["trust_level"] == "supervised",
                "cannot_execute": result["can_execute"] is False,
                "requires_supervisor": result["requires_supervisor"] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Supervised Medium Valid")
    def supervised_medium_valid(self):
        """Supervised can be assigned MEDIUM tasks."""
        try:
            from governance.kanren_constraints import valid_task_assignment, AgentContext, TaskContext
            agent = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
            task = TaskContext("TASK-003", "MEDIUM", False)
            result = valid_task_assignment(agent, task)
            return {
                "valid": result["valid"] is True,
                "trust_level": result["trust_level"] == "supervised",
                "can_execute": result["can_execute"] is True,
                "requires_supervisor": result["requires_supervisor"] is True,
                "no_evidence": result["requires_evidence"] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Constraints Checked Included")
    def constraints_checked_included(self):
        """Validation result includes constraints checked."""
        try:
            from governance.kanren_constraints import valid_task_assignment, AgentContext, TaskContext
            agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
            task = TaskContext("TASK-001", "CRITICAL", True)
            result = valid_task_assignment(agent, task)
            return {
                "has_constraints": "constraints_checked" in result,
                "has_multiple": len(result["constraints_checked"]) >= 3,
                "has_rule_011": any("RULE-011" in c for c in result["constraints_checked"])
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
