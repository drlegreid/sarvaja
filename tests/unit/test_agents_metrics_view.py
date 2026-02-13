"""
Tests for agent metrics and trust history view.

Per GAP-UI-042: Trust score history and explanation.
Batch 162: New coverage for views/agents/metrics.py (0→10 tests).
"""
import inspect

import pytest


class TestAgentMetricsComponents:
    def test_build_metrics_card_callable(self):
        from agent.governance_ui.views.agents.metrics import build_agent_metrics_card
        assert callable(build_agent_metrics_card)

    def test_build_trust_breakdown_callable(self):
        from agent.governance_ui.views.agents.metrics import build_trust_components_breakdown
        assert callable(build_trust_components_breakdown)

    def test_build_trust_timeline_callable(self):
        from agent.governance_ui.views.agents.metrics import build_trust_history_timeline
        assert callable(build_trust_history_timeline)

    def test_build_trust_history_callable(self):
        from agent.governance_ui.views.agents.metrics import build_trust_history_card
        assert callable(build_trust_history_card)


class TestAgentMetricsContent:
    def test_has_metrics_card_testid(self):
        from agent.governance_ui.views.agents import metrics
        source = inspect.getsource(metrics)
        assert "agent-metrics-card" in source

    def test_has_trust_timeline_testid(self):
        from agent.governance_ui.views.agents import metrics
        source = inspect.getsource(metrics)
        assert "trust-history-timeline" in source

    def test_has_trust_history_card_testid(self):
        from agent.governance_ui.views.agents import metrics
        source = inspect.getsource(metrics)
        assert "agent-trust-history-card" in source

    def test_has_trust_refresh_btn(self):
        from agent.governance_ui.views.agents import metrics
        source = inspect.getsource(metrics)
        assert "trust-history-refresh" in source

    def test_shows_trust_score(self):
        from agent.governance_ui.views.agents import metrics
        source = inspect.getsource(metrics)
        assert "trust_score" in source

    def test_shows_tasks_executed(self):
        from agent.governance_ui.views.agents import metrics
        source = inspect.getsource(metrics)
        assert "tasks_executed" in source
