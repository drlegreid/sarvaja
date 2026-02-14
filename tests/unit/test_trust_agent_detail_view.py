"""
Tests for trust agent detail view components.

Per P9.5: Trust Dashboard implementation.
Batch 164: New coverage for views/trust/agent_detail.py (0->10 tests).
"""
import inspect

import pytest


class TestTrustAgentDetailComponents:
    def test_build_agent_detail_metrics_callable(self):
        from agent.governance_ui.views.trust.agent_detail import build_agent_detail_metrics
        assert callable(build_agent_detail_metrics)

    def test_build_trust_formula_card_callable(self):
        from agent.governance_ui.views.trust.agent_detail import build_trust_formula_card
        assert callable(build_trust_formula_card)

    def test_build_agent_detail_view_callable(self):
        from agent.governance_ui.views.trust.agent_detail import build_agent_detail_view
        assert callable(build_agent_detail_view)


class TestAgentDetailMetricsContent:
    def test_has_trust_score_testid(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "agent-trust-score" in source

    def test_has_compliance_testid(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "agent-compliance" in source

    def test_has_accuracy_testid(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "agent-accuracy" in source

    def test_has_tenure_testid(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "agent-tenure" in source


class TestTrustFormulaContent:
    def test_has_formula_testid(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "agent-trust-formula" in source

    def test_has_rule_011_reference(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "RULE-011" in source

    def test_has_trust_formula_weights(self):
        from agent.governance_ui.views.trust import agent_detail
        source = inspect.getsource(agent_detail)
        assert "0.4" in source
        assert "0.3" in source
        assert "0.2" in source
        assert "0.1" in source
