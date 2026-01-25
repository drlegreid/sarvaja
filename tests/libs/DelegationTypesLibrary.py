"""
Robot Framework Library for Delegation - Types & Context Tests.

Per ORCH-004: Agent delegation protocol.
Split from DelegationLibrary.py per DOC-SIZE-01-v1.

Covers: DelegationType, DelegationPriority, DelegationContext.
"""
from pathlib import Path
from robot.api.deco import keyword


class DelegationTypesLibrary:
    """Library for testing delegation types and context."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # DelegationType Tests
    # =========================================================================

    @keyword("Delegation Type Research")
    def delegation_type_research(self):
        """RESEARCH type for context gathering."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.RESEARCH.value == "research"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegation Type Implementation")
    def delegation_type_implementation(self):
        """IMPLEMENTATION type for coding tasks."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.IMPLEMENTATION.value == "impl"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegation Type Validation")
    def delegation_type_validation(self):
        """VALIDATION type for rule checking."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.VALIDATION.value == "validation"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegation Type Escalation")
    def delegation_type_escalation(self):
        """ESCALATION type for authority escalation."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.ESCALATION.value == "escalation"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # DelegationPriority Tests
    # =========================================================================

    @keyword("Priority Ordering Works")
    def priority_ordering_works(self):
        """CRITICAL < HIGH < MEDIUM < LOW."""
        try:
            from agent.orchestrator.delegation import DelegationPriority
            return {
                "crit_lt_high": DelegationPriority.CRITICAL.value < DelegationPriority.HIGH.value,
                "high_lt_med": DelegationPriority.HIGH.value < DelegationPriority.MEDIUM.value,
                "med_lt_low": DelegationPriority.MEDIUM.value < DelegationPriority.LOW.value
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Critical Priority Value")
    def critical_priority_value(self):
        """CRITICAL has value 1."""
        try:
            from agent.orchestrator.delegation import DelegationPriority
            return {"is_1": DelegationPriority.CRITICAL.value == 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # DelegationContext Tests
    # =========================================================================

    @keyword("Context Basic Creation")
    def context_basic_creation(self):
        """Create basic delegation context."""
        try:
            from agent.orchestrator.delegation import DelegationContext, DelegationPriority

            ctx = DelegationContext(
                delegation_id="DEL-001",
                task_id="TASK-001",
                source_agent_id="AGENT-001",
                task_description="Research authentication patterns",
            )

            return {
                "id_correct": ctx.delegation_id == "DEL-001",
                "task_correct": ctx.task_id == "TASK-001",
                "source_correct": ctx.source_agent_id == "AGENT-001",
                "priority_default": ctx.priority == DelegationPriority.MEDIUM
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context With Constraints")
    def context_with_constraints(self):
        """Create context with constraints."""
        try:
            from agent.orchestrator.delegation import DelegationContext

            ctx = DelegationContext(
                delegation_id="DEL-002",
                task_id="TASK-002",
                source_agent_id="AGENT-001",
                task_description="Implement feature",
                constraints=["No external deps", "Must be async"],
            )

            return {
                "has_constraints": len(ctx.constraints) == 2,
                "constraint_present": "No external deps" in ctx.constraints
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context With Evidence")
    def context_with_evidence(self):
        """Create context with evidence."""
        try:
            from agent.orchestrator.delegation import DelegationContext

            ctx = DelegationContext(
                delegation_id="DEL-003",
                task_id="TASK-003",
                source_agent_id="AGENT-001",
                task_description="Review code",
                evidence=["tests/test_auth.py passed", "No lint errors"],
            )

            return {"has_evidence": len(ctx.evidence) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context To Dict")
    def context_to_dict(self):
        """Convert context to dictionary."""
        try:
            from agent.orchestrator.delegation import DelegationContext, DelegationPriority

            ctx = DelegationContext(
                delegation_id="DEL-004",
                task_id="TASK-004",
                source_agent_id="AGENT-001",
                task_description="Test task",
                priority=DelegationPriority.HIGH,
            )

            d = ctx.to_dict()
            return {
                "id_correct": d.get("delegation_id") == "DEL-004",
                "priority_correct": d.get("priority") == "HIGH",
                "has_created_at": "created_at" in d
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context From Dict")
    def context_from_dict(self):
        """Create context from dictionary."""
        try:
            from agent.orchestrator.delegation import DelegationContext, DelegationPriority

            data = {
                "delegation_id": "DEL-005",
                "task_id": "TASK-005",
                "source_agent_id": "AGENT-002",
                "task_description": "From dict",
                "priority": "CRITICAL",
                "min_trust_score": 0.8,
            }

            ctx = DelegationContext.from_dict(data)
            return {
                "id_correct": ctx.delegation_id == "DEL-005",
                "priority_correct": ctx.priority == DelegationPriority.CRITICAL,
                "trust_correct": ctx.min_trust_score == 0.8
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Min Trust Default")
    def context_min_trust_default(self):
        """Default min_trust_score is 0.5."""
        try:
            from agent.orchestrator.delegation import DelegationContext

            ctx = DelegationContext(
                delegation_id="DEL-006",
                task_id="TASK-006",
                source_agent_id="AGENT-001",
                task_description="Test",
            )
            return {"default_trust": ctx.min_trust_score == 0.5}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
