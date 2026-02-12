"""
Unit tests for Compat - Rule Quality Exports.

Per DOC-SIZE-01-v1: Tests for compat/quality.py module.
Tests: governance_analyze_rules, governance_rule_impact, governance_find_issues.
"""

import json
import pytest
from unittest.mock import patch


class TestGovernanceAnalyzeRules:
    """Tests for governance_analyze_rules()."""

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.quality import governance_analyze_rules
        result = json.loads(governance_analyze_rules())
        assert "error" in result

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", True)
    @patch("governance.compat.quality._analyze_rule_quality")
    def test_delegates(self, mock_analyze):
        mock_analyze.return_value = '{"ok": true}'
        from governance.compat.quality import governance_analyze_rules
        result = governance_analyze_rules()
        assert result == '{"ok": true}'
        mock_analyze.assert_called_once()


class TestGovernanceRuleImpact:
    """Tests for governance_rule_impact()."""

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.quality import governance_rule_impact
        result = json.loads(governance_rule_impact("R-1"))
        assert "error" in result

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", True)
    @patch("governance.compat.quality._get_rule_impact")
    def test_delegates(self, mock_impact):
        mock_impact.return_value = '{"impact": "high"}'
        from governance.compat.quality import governance_rule_impact
        result = governance_rule_impact("RULE-001")
        mock_impact.assert_called_with("RULE-001")
        assert json.loads(result)["impact"] == "high"


class TestGovernanceFindIssues:
    """Tests for governance_find_issues()."""

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.quality import governance_find_issues
        result = json.loads(governance_find_issues())
        assert "error" in result

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", True)
    @patch("governance.compat.quality._find_rule_issues")
    def test_with_type(self, mock_find):
        mock_find.return_value = '[]'
        from governance.compat.quality import governance_find_issues
        result = governance_find_issues("orphaned")
        mock_find.assert_called_with("orphaned")

    @patch("governance.compat.quality._RULE_QUALITY_AVAILABLE", True)
    @patch("governance.compat.quality._find_rule_issues")
    def test_without_type(self, mock_find):
        mock_find.return_value = '{"full": true}'
        from governance.compat.quality import governance_find_issues
        result = governance_find_issues(None)
        mock_find.assert_called_with(None)
