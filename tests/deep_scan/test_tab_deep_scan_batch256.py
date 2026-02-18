"""Batch 256 — UI views null guard and operator precedence tests.

Validates fixes for:
- BUG-256-UI-001: trust_score color binding null guard
- BUG-256-UI-002: compliance/accuracy rate operator precedence
- BUG-256-UI-003: event_type null guard before charAt
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-256-UI-001: trust_score color binding ────────────────────────

class TestTrustScoreColorGuard:
    """agent_detail.py color binding must guard against null trust_score."""

    def test_color_binding_has_guard(self):
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        # Color binding should use (selected_agent.trust_score || 0) >= 0.8
        assert "(selected_agent.trust_score || 0) >= 0.8" in src

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        assert "BUG-256-UI-001" in src


# ── BUG-256-UI-002: compliance/accuracy operator precedence ──────────

class TestComplianceRatePrecedence:
    """compliance_rate and accuracy_rate must guard before multiplication."""

    def test_compliance_rate_guard_before_multiply(self):
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        # Correct: ((rate || 0) * 100)  Wrong: (rate * 100 || 0)
        assert "((selected_agent.compliance_rate || 0) * 100)" in src

    def test_accuracy_rate_guard_before_multiply(self):
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        assert "((selected_agent.accuracy_rate || 0) * 100)" in src

    def test_no_wrong_precedence(self):
        """The wrong pattern (rate * 100 || 0) must not appear."""
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        assert "compliance_rate * 100 || 0" not in src
        assert "accuracy_rate * 100 || 0" not in src

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/trust/agent_detail.py").read_text()
        assert "BUG-256-UI-002" in src


# ── BUG-256-UI-003: event_type null guard ─────────────────────────────

class TestEventTypeNullGuard:
    """execution.py must guard event_type before charAt."""

    def test_event_type_guard_present(self):
        src = (SRC / "agent/governance_ui/views/tasks/execution.py").read_text()
        # Must have a ternary guard: event.event_type ? (...) : 'Unknown'
        assert "event.event_type ?" in src
        assert "'Unknown'" in src

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/tasks/execution.py").read_text()
        assert "BUG-256-UI-003" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch256Imports:
    def test_agent_detail_importable(self):
        import agent.governance_ui.views.trust.agent_detail
        assert agent.governance_ui.views.trust.agent_detail is not None

    def test_execution_importable(self):
        import agent.governance_ui.views.tasks.execution
        assert agent.governance_ui.views.tasks.execution is not None

    def test_trust_panels_importable(self):
        import agent.governance_ui.views.trust.panels
        assert agent.governance_ui.views.trust.panels is not None

    def test_agent_metrics_importable(self):
        import agent.governance_ui.views.agents.metrics
        assert agent.governance_ui.views.agents.metrics is not None

    def test_workflow_proposals_importable(self):
        import agent.governance_ui.views.workflow_proposals
        assert agent.governance_ui.views.workflow_proposals is not None
