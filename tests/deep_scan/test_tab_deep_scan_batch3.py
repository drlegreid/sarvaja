"""
Unit tests for Tab Deep Scan Batch 3 fixes.

Covers: rules.py and decisions.py trace additions.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect


class TestRulesTraces:
    def test_rules_imports_add_error_trace(self):
        """rules.py should import add_error_trace."""
        from agent.governance_ui.controllers import rules

        source = inspect.getsource(rules)
        assert "add_error_trace" in source

    def test_rules_submit_has_trace(self):
        """submit_rule_form exception handler should trace."""
        from agent.governance_ui.controllers import rules

        source = inspect.getsource(rules)
        assert "Save rule failed" in source

    def test_rules_delete_has_trace(self):
        """delete_rule exception handler should trace."""
        from agent.governance_ui.controllers import rules

        source = inspect.getsource(rules)
        assert "Delete rule failed" in source

    def test_rules_load_has_trace(self):
        """load_rules exception handler should trace."""
        from agent.governance_ui.controllers import rules

        source = inspect.getsource(rules)
        assert "Load rules failed" in source


class TestDecisionsTraces:
    def test_decisions_imports_add_error_trace(self):
        """decisions.py should import add_error_trace."""
        from agent.governance_ui.controllers import decisions

        source = inspect.getsource(decisions)
        assert "add_error_trace" in source

    def test_decisions_submit_has_trace(self):
        """submit_decision_form exception handler should trace."""
        from agent.governance_ui.controllers import decisions

        source = inspect.getsource(decisions)
        assert "Save decision failed" in source

    def test_decisions_delete_has_trace(self):
        """delete_decision exception handler should trace."""
        from agent.governance_ui.controllers import decisions

        source = inspect.getsource(decisions)
        assert "Delete decision failed" in source
