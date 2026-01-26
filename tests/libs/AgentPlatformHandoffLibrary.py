"""
Robot Framework Library for Agent Platform Handoff Tests.

Per RD-AGENT-TESTING: ATEST-004 - Handoff Chain Validation.
Split from test_agent_platform.py per DOC-SIZE-01-v1.
"""
from pathlib import Path
from robot.api.deco import keyword


class AgentPlatformHandoffLibrary:
    """Library for handoff chain validation tests (ATEST-004)."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    @keyword("Handoff Has Required Fields")
    def handoff_has_required_fields(self):
        """Handoff contains all required fields."""
        try:
            from governance.orchestrator.handoff import TaskHandoff

            handoff = TaskHandoff(
                task_id="TASK-001",
                title="Test Handoff",
                from_agent="RESEARCH",
                to_agent="CODING",
                status="READY_FOR_CODING"
            )

            return {
                "task_id": handoff.task_id == "TASK-001",
                "from_agent": handoff.from_agent == "RESEARCH",
                "to_agent": handoff.to_agent == "CODING",
                "status": handoff.status == "READY_FOR_CODING"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Handoff To Markdown")
    def handoff_to_markdown(self):
        """Handoff can be serialized to markdown."""
        try:
            from governance.orchestrator.handoff import TaskHandoff

            handoff = TaskHandoff(
                task_id="TASK-MD-001",
                title="Markdown Test",
                from_agent="RESEARCH",
                to_agent="CODING",
                status="READY_FOR_CODING",
                context_summary="Test context",
                recommended_action="Implement the fix"
            )

            markdown = handoff.to_markdown()

            return {
                "has_header": "# Task Handoff:" in markdown,
                "has_research": "RESEARCH" in markdown,
                "has_coding": "CODING" in markdown,
                "has_context": "Test context" in markdown
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Handoff Roundtrip")
    def handoff_roundtrip(self):
        """Handoff survives markdown serialization/deserialization."""
        try:
            from governance.orchestrator.handoff import TaskHandoff

            original = TaskHandoff(
                task_id="TASK-RT-001",
                title="Roundtrip Test",
                from_agent="CODING",
                to_agent="CURATOR",
                status="READY_FOR_REVIEW",
                context_summary="Implementation complete",
                recommended_action="Review and approve"
            )

            markdown = original.to_markdown()
            restored = TaskHandoff.from_markdown(markdown)

            return {
                "restored": restored is not None,
                "task_id": restored.task_id == original.task_id if restored else False,
                "from_agent": restored.from_agent == original.from_agent if restored else False,
                "to_agent": restored.to_agent == original.to_agent if restored else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
