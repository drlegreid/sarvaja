"""
Tests for trust dashboard stats components.

Per RULE-011: Multi-Agent Governance Protocol.
Batch 165: New coverage for views/trust/stats.py (0->10 tests).
"""
import inspect

import pytest


class TestTrustStatsComponents:
    def test_build_trust_header_callable(self):
        from agent.governance_ui.views.trust.stats import build_trust_header
        assert callable(build_trust_header)

    def test_build_governance_stats_callable(self):
        from agent.governance_ui.views.trust.stats import build_governance_stats
        assert callable(build_governance_stats)


class TestTrustHeaderContent:
    def test_has_refresh_btn(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "trust-refresh-btn" in source

    def test_has_refresh_icon(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "mdi-refresh" in source


class TestGovernanceStatsContent:
    def test_has_agents_stat(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "trust-stat-agents" in source

    def test_has_avg_trust(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "trust-stat-avg" in source

    def test_has_pending_stat(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "trust-stat-pending" in source

    def test_has_escalated_stat(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "trust-stat-escalated" in source

    def test_has_total_agents_label(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "Total Agents" in source

    def test_has_avg_trust_label(self):
        from agent.governance_ui.views.trust import stats
        source = inspect.getsource(stats)
        assert "Avg Trust Score" in source
