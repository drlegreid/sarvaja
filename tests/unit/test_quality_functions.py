"""
Unit tests for Rule Quality Convenience Functions.

Per DOC-SIZE-01-v1: Tests for quality/functions.py module.
Tests: analyze_rule_quality, get_rule_impact, find_rule_issues.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestAnalyzeRuleQuality:
    """Tests for analyze_rule_quality()."""

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_returns_json(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_report = MagicMock()
        mock_report.to_json.return_value = '{"summary": "ok"}'
        mock_inst.analyze.return_value = mock_report
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import analyze_rule_quality
        result = analyze_rule_quality()
        assert result == '{"summary": "ok"}'

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_calls_close(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_report = MagicMock()
        mock_report.to_json.return_value = "{}"
        mock_inst.analyze.return_value = mock_report
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import analyze_rule_quality
        analyze_rule_quality()
        mock_inst.close.assert_called_once()

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_close_on_error(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.analyze.side_effect = RuntimeError("fail")
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import analyze_rule_quality
        with pytest.raises(RuntimeError):
            analyze_rule_quality()
        mock_inst.close.assert_called_once()


class TestGetRuleImpact:
    """Tests for get_rule_impact()."""

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_returns_json(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.get_rule_impact.return_value = {"impact": "high"}
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import get_rule_impact
        result = get_rule_impact("RULE-001")
        parsed = json.loads(result)
        assert parsed["impact"] == "high"

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_passes_rule_id(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.get_rule_impact.return_value = {}
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import get_rule_impact
        get_rule_impact("SESSION-EVID-01-v1")
        mock_inst.get_rule_impact.assert_called_with("SESSION-EVID-01-v1")

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_calls_close(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.get_rule_impact.return_value = {}
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import get_rule_impact
        get_rule_impact("R-1")
        mock_inst.close.assert_called_once()


class TestFindRuleIssues:
    """Tests for find_rule_issues()."""

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_orphaned(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_issue = MagicMock()
        mock_issue.to_dict.return_value = {"type": "orphaned", "rule_id": "R-1"}
        mock_inst.find_orphaned_rules.return_value = [mock_issue]
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        result = find_rule_issues("orphaned")
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["type"] == "orphaned"

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_shallow(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.find_shallow_rules.return_value = []
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        result = find_rule_issues("shallow")
        assert json.loads(result) == []

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_over_connected(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.find_over_connected_rules.return_value = []
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        result = find_rule_issues("over_connected")
        assert json.loads(result) == []

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_circular(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.find_circular_dependencies.return_value = []
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        result = find_rule_issues("circular")
        assert json.loads(result) == []

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_under_documented(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.find_under_documented_rules.return_value = []
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        result = find_rule_issues("under_documented")
        assert json.loads(result) == []

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_no_type_runs_full_analysis(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_report = MagicMock()
        mock_report.to_json.return_value = '{"full": true}'
        mock_inst.analyze.return_value = mock_report
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        result = find_rule_issues(None)
        assert result == '{"full": true}'

    @patch("governance.quality.functions.RuleQualityAnalyzer")
    def test_calls_close(self, MockAnalyzer):
        mock_inst = MagicMock()
        mock_inst.find_orphaned_rules.return_value = []
        MockAnalyzer.return_value = mock_inst

        from governance.quality.functions import find_rule_issues
        find_rule_issues("orphaned")
        mock_inst.close.assert_called_once()
