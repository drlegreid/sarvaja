"""Batch 223 — UI views defense tests.

Validates fixes for:
- BUG-223-TRUST-001: trust/panels.py null trust_score guard
- BUG-223-TRUST-002: trust/agent_detail.py null trust_score guard
- BUG-223-VOTES-001: workflow_proposals.py null votes guard
- BUG-223-DECISION-001: workflow_proposals.py null decision guard
- BUG-223-COMPLIANCE-001: executive/metrics.py invalid 'compliance' view
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-223-TRUST-001+002: Trust score null guards ──────────────────

class TestTrustScoreNullGuards:
    """Trust score displays must guard against null values."""

    def test_panels_has_null_guard(self):
        src = (SRC / "agent/governance_ui/views/trust/panels.py").read_text()
        assert "agent.trust_score || 0" in src

    def test_agent_detail_has_null_guard(self):
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        assert "selected_agent.trust_score || 0" in src


# ── BUG-223-VOTES-001: Votes null guard ──────────────────────────────

class TestVotesNullGuard:
    """Proposal votes must guard against null values."""

    def test_votes_for_has_guard(self):
        src = (SRC / "agent/governance_ui/views/workflow_proposals.py").read_text()
        assert "votes_for || 0" in src

    def test_votes_against_has_guard(self):
        src = (SRC / "agent/governance_ui/views/workflow_proposals.py").read_text()
        assert "votes_against || 0" in src


# ── BUG-223-DECISION-001: Decision null guard ────────────────────────

class TestDecisionNullGuard:
    """Proposal decision must guard against null toUpperCase()."""

    def test_decision_has_guard(self):
        src = (SRC / "agent/governance_ui/views/workflow_proposals.py").read_text()
        assert "p.decision || 'pending'" in src


# ── BUG-223-COMPLIANCE-001: Invalid view navigation ─────────────────

class TestComplianceViewFix:
    """Executive metrics compliance card must navigate to 'rules' not 'compliance'."""

    def test_no_compliance_view_nav(self):
        src = (SRC / "agent/governance_ui/views/executive/metrics.py").read_text()
        assert "active_view = 'compliance'" not in src

    def test_navigates_to_rules(self):
        src = (SRC / "agent/governance_ui/views/executive/metrics.py").read_text()
        assert "active_view = 'rules'" in src


# ── Views defense tests ──────────────────────────────────────────────

class TestViewModuleImports:
    """Defense tests for UI view modules."""

    def test_trust_panels_importable(self):
        from agent.governance_ui.views.trust.panels import build_trust_leaderboard
        assert callable(build_trust_leaderboard)

    def test_trust_agent_detail_importable(self):
        from agent.governance_ui.views.trust.agent_detail import build_agent_detail_view
        assert callable(build_agent_detail_view)

    def test_workflow_proposals_importable(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_form
        assert callable(build_proposal_form)

    def test_executive_metrics_importable(self):
        from agent.governance_ui.views.executive.metrics import build_metrics_summary
        assert callable(build_metrics_summary)

    def test_sessions_list_importable(self):
        from agent.governance_ui.views.sessions.list import build_sessions_list_view
        assert callable(build_sessions_list_view)

    def test_sessions_content_importable(self):
        from agent.governance_ui.views.sessions.content import build_session_info_card
        assert callable(build_session_info_card)

    def test_sessions_detail_importable(self):
        from agent.governance_ui.views.sessions.detail import build_session_detail_view
        assert callable(build_session_detail_view)

    def test_backlog_view_importable(self):
        from agent.governance_ui.views.backlog_view import build_backlog_view
        assert callable(build_backlog_view)

    def test_monitor_view_importable(self):
        from agent.governance_ui.views.monitor_view import build_monitor_view
        assert callable(build_monitor_view)

    def test_tasks_list_importable(self):
        from agent.governance_ui.views.tasks.list import build_tasks_list_view
        assert callable(build_tasks_list_view)

    def test_rules_list_importable(self):
        from agent.governance_ui.views.rules_view import build_rules_list_view
        assert callable(build_rules_list_view)

    def test_agents_list_importable(self):
        from agent.governance_ui.views.agents.list import build_agents_list_view
        assert callable(build_agents_list_view)

    def test_decisions_list_importable(self):
        from agent.governance_ui.views.decisions.list import build_decisions_list_view
        assert callable(build_decisions_list_view)

    def test_chat_messages_importable(self):
        from agent.governance_ui.views.chat.messages import build_chat_messages
        assert callable(build_chat_messages)

    def test_impact_analysis_importable(self):
        from agent.governance_ui.views.impact.analysis import build_analysis_results
        assert callable(build_analysis_results)
