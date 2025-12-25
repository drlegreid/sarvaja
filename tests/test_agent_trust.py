"""
Agent Trust Dashboard Tests (P9.5)
Created: 2024-12-25

Tests for RULE-011 compliance metrics and agent trust tracking.
Strategic Goal: Monitor and enforce multi-agent governance.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"


class TestAgentTrustModule:
    """Verify P9.5 agent trust module exists."""

    @pytest.mark.unit
    def test_agent_trust_module_exists(self):
        """Agent trust module must exist."""
        trust_file = AGENT_DIR / "agent_trust.py"
        assert trust_file.exists(), "agent/agent_trust.py not found"

    @pytest.mark.unit
    def test_agent_trust_class(self):
        """AgentTrustDashboard class must be importable."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        assert dashboard is not None

    @pytest.mark.unit
    def test_dashboard_has_required_methods(self):
        """Dashboard must have required methods."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()

        assert hasattr(dashboard, 'get_trust_score')
        assert hasattr(dashboard, 'get_compliance_status')
        assert hasattr(dashboard, 'record_action')
        assert hasattr(dashboard, 'get_trust_history')


class TestTrustScoring:
    """Tests for trust score calculation."""

    @pytest.mark.unit
    def test_get_trust_score(self):
        """Should return trust score for an agent."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        score = dashboard.get_trust_score("agent-001")

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    @pytest.mark.unit
    def test_default_trust_score(self):
        """New agents should have default trust score."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        score = dashboard.get_trust_score("new-agent-xyz")

        assert score == dashboard.default_trust_score

    @pytest.mark.unit
    def test_get_all_trust_scores(self):
        """Should return trust scores for all known agents."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        scores = dashboard.get_all_trust_scores()

        assert isinstance(scores, dict)


class TestComplianceTracking:
    """Tests for RULE-011 compliance tracking."""

    @pytest.mark.unit
    def test_get_compliance_status(self):
        """Should return compliance status for agent."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        status = dashboard.get_compliance_status("agent-001")

        assert isinstance(status, dict)
        assert 'compliant' in status

    @pytest.mark.unit
    def test_compliance_includes_rule_011(self):
        """Compliance should specifically track RULE-011."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        status = dashboard.get_compliance_status("agent-001")

        # Should reference RULE-011
        assert 'rules' in status or 'RULE-011' in str(status)

    @pytest.mark.unit
    def test_get_compliance_summary(self):
        """Should return system-wide compliance summary."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        summary = dashboard.get_compliance_summary()

        assert isinstance(summary, dict)


class TestActionRecording:
    """Tests for recording agent actions."""

    @pytest.mark.unit
    def test_record_action(self):
        """Should record an agent action."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        result = dashboard.record_action(
            agent_id="agent-001",
            action="query_rules",
            compliant=True
        )

        assert isinstance(result, dict)
        assert result.get('success', True)

    @pytest.mark.unit
    def test_record_non_compliant_action(self):
        """Should record non-compliant action and adjust trust."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()

        # Get initial score
        initial_score = dashboard.get_trust_score("agent-test")

        # Record non-compliant action
        dashboard.record_action(
            agent_id="agent-test",
            action="unauthorized_access",
            compliant=False
        )

        # Check score decreased
        new_score = dashboard.get_trust_score("agent-test")
        assert new_score < initial_score

    @pytest.mark.unit
    def test_record_compliant_action_increases_trust(self):
        """Compliant actions should increase trust (slowly)."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()

        # Set a lower initial score
        dashboard._trust_scores["agent-good"] = 50.0

        # Record many compliant actions
        for _ in range(10):
            dashboard.record_action(
                agent_id="agent-good",
                action="normal_operation",
                compliant=True
            )

        # Trust should have increased
        new_score = dashboard.get_trust_score("agent-good")
        assert new_score > 50.0


class TestTrustHistory:
    """Tests for trust history tracking."""

    @pytest.mark.unit
    def test_get_trust_history(self):
        """Should return trust history for agent."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        history = dashboard.get_trust_history("agent-001")

        assert isinstance(history, list)

    @pytest.mark.unit
    def test_history_includes_actions(self):
        """History should include recorded actions."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()

        # Record an action
        dashboard.record_action(
            agent_id="agent-history-test",
            action="test_action",
            compliant=True
        )

        history = dashboard.get_trust_history("agent-history-test")
        assert len(history) > 0


class TestTrustThresholds:
    """Tests for trust threshold enforcement."""

    @pytest.mark.unit
    def test_is_trusted(self):
        """Should check if agent meets trust threshold."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        is_trusted = dashboard.is_trusted("agent-001")

        assert isinstance(is_trusted, bool)

    @pytest.mark.unit
    def test_get_trust_level(self):
        """Should return trust level category."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        level = dashboard.get_trust_level("agent-001")

        assert level in ['HIGH', 'MEDIUM', 'LOW', 'UNTRUSTED']


class TestAgentMetrics:
    """Tests for agent metrics."""

    @pytest.mark.unit
    def test_get_agent_metrics(self):
        """Should return metrics for an agent."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        metrics = dashboard.get_agent_metrics("agent-001")

        assert isinstance(metrics, dict)
        assert 'trust_score' in metrics

    @pytest.mark.unit
    def test_get_system_metrics(self):
        """Should return system-wide metrics."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()
        metrics = dashboard.get_system_metrics()

        assert isinstance(metrics, dict)


class TestTrustIntegration:
    """Integration tests for agent trust dashboard."""

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory function should create dashboard."""
        from agent.agent_trust import create_trust_dashboard

        dashboard = create_trust_dashboard()
        assert dashboard is not None

    @pytest.mark.unit
    def test_trust_persistence(self):
        """Trust data should be retrievable."""
        from agent.agent_trust import AgentTrustDashboard

        dashboard = AgentTrustDashboard()

        # Record action
        dashboard.record_action("agent-persist", "action", True)

        # Should have data
        score = dashboard.get_trust_score("agent-persist")
        assert score is not None
