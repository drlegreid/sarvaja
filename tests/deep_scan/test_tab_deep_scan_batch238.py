"""Batch 238 — UI views layer defense tests.

Validates fixes for:
- BUG-238-WP-001: phases_completed.join() on null array
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-238-WP-001: Guard phases_completed in workflow proposals ─────

class TestWorkflowProposalsPhasesGuard:
    """phases_completed must have || [] guard before .join()."""

    def test_phases_completed_has_guard(self):
        src = (SRC / "agent/governance_ui/views/workflow_proposals.py").read_text()
        assert "(proposal_result.phases_completed || []).join" in src

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/workflow_proposals.py").read_text()
        assert "BUG-238-WP-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch238Imports:
    def test_workflow_proposals_importable(self):
        import agent.governance_ui.views.workflow_proposals
        assert agent.governance_ui.views.workflow_proposals is not None

    def test_trust_panels_importable(self):
        import agent.governance_ui.views.trust.panels
        assert agent.governance_ui.views.trust.panels is not None

    def test_trust_agent_detail_importable(self):
        import agent.governance_ui.views.trust.agent_detail
        assert agent.governance_ui.views.trust.agent_detail is not None

    def test_agents_metrics_importable(self):
        import agent.governance_ui.views.agents.metrics
        assert agent.governance_ui.views.agents.metrics is not None

    def test_executive_metrics_importable(self):
        import agent.governance_ui.views.executive.metrics
        assert agent.governance_ui.views.executive.metrics is not None

    def test_sessions_tool_calls_importable(self):
        import agent.governance_ui.views.sessions.tool_calls
        assert agent.governance_ui.views.sessions.tool_calls is not None

    def test_tasks_execution_importable(self):
        import agent.governance_ui.views.tasks.execution
        assert agent.governance_ui.views.tasks.execution is not None

    def test_session_transcript_importable(self):
        import agent.governance_ui.views.sessions.session_transcript
        assert agent.governance_ui.views.sessions.session_transcript is not None
