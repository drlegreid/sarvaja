"""
Tests for impact analysis view components.

Per GAP-FILE-001: Modularization of governance_dashboard.py.
Batch 164: New coverage for views/impact/analysis.py (0->10 tests).
"""
import inspect

import pytest


class TestImpactAnalysisComponents:
    def test_build_risk_summary_card_callable(self):
        from agent.governance_ui.views.impact.analysis import build_risk_summary_card
        assert callable(build_risk_summary_card)

    def test_build_recommendation_card_callable(self):
        from agent.governance_ui.views.impact.analysis import build_recommendation_card
        assert callable(build_recommendation_card)

    def test_build_analysis_results_callable(self):
        from agent.governance_ui.views.impact.analysis import build_analysis_results
        assert callable(build_analysis_results)


class TestRiskSummaryContent:
    def test_has_risk_card_testid(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "impact-risk-card" in source

    def test_has_risk_chip(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "impact-risk-chip" in source

    def test_has_affected_count(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "impact-total-affected" in source

    def test_has_risk_levels(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "CRITICAL" in source
        assert "HIGH" in source
        assert "MEDIUM" in source


class TestRecommendationContent:
    def test_has_recommendation_card_testid(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "impact-recommendation-card" in source

    def test_has_recommendation_testid(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "impact-recommendation" in source

    def test_has_critical_rules(self):
        from agent.governance_ui.views.impact import analysis
        source = inspect.getsource(analysis)
        assert "impact-critical-rules" in source
