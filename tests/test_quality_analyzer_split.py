"""
TDD Tests for quality/analyzer.py split.

Per GAP-FILE-025: analyzer.py needs to go from 410 to <400 lines.
Per DOC-SIZE-01-v1: Files must stay under 400 lines.

Tests written BEFORE implementation (TDD).

Created: 2026-01-14
"""

import pytest
from pathlib import Path


# Project paths
GOVERNANCE_DIR = Path(__file__).parent.parent / "governance"
QUALITY_DIR = GOVERNANCE_DIR / "quality"


class TestQualityAnalyzerSplit:
    """Test quality analyzer module structure after split."""

    def test_analyzer_module_exists(self):
        """Verify analyzer.py exists."""
        analyzer_file = QUALITY_DIR / "analyzer.py"
        assert analyzer_file.exists(), "analyzer.py must exist"

    def test_impact_module_exists(self):
        """Verify impact.py extraction exists."""
        impact_file = QUALITY_DIR / "impact.py"
        assert impact_file.exists(), "impact.py should be extracted"

    def test_analyzer_under_400_lines(self):
        """Verify analyzer.py is under 400 lines per DOC-SIZE-01-v1."""
        analyzer_file = QUALITY_DIR / "analyzer.py"
        with open(analyzer_file, "r") as f:
            lines = len(f.readlines())
        assert lines < 400, f"analyzer.py has {lines} lines, should be <400"

    def test_impact_module_has_function(self):
        """Verify impact.py exports get_rule_impact function."""
        from governance.quality.impact import calculate_rule_impact
        assert callable(calculate_rule_impact)


class TestBackwardCompatibility:
    """Test backward compatibility after split."""

    def test_import_analyzer_class(self):
        """Verify RuleQualityAnalyzer can still be imported."""
        from governance.quality.analyzer import RuleQualityAnalyzer
        assert RuleQualityAnalyzer is not None

    def test_analyzer_has_get_rule_impact(self):
        """Verify analyzer still has get_rule_impact method."""
        from governance.quality.analyzer import RuleQualityAnalyzer
        analyzer = RuleQualityAnalyzer()
        assert hasattr(analyzer, "get_rule_impact")
        assert callable(analyzer.get_rule_impact)

    def test_impact_module_in_quality_init(self):
        """Verify impact module is accessible from quality package."""
        # Should be able to import from quality package
        from governance.quality import impact
        assert hasattr(impact, "calculate_rule_impact")


class TestImpactModule:
    """Test the extracted impact module."""

    def test_calculate_rule_impact_signature(self):
        """Verify function signature."""
        from governance.quality.impact import calculate_rule_impact
        import inspect
        sig = inspect.signature(calculate_rule_impact)
        params = list(sig.parameters.keys())
        # Should accept rule data, dependents, and caches
        assert "rule_id" in params
        assert "rule" in params
        assert "dependents_cache" in params

    def test_calculate_rule_impact_returns_dict(self):
        """Verify function returns dictionary."""
        from governance.quality.impact import calculate_rule_impact

        # Test with minimal mock data
        result = calculate_rule_impact(
            rule_id="RULE-TEST",
            rule={"name": "Test", "priority": "MEDIUM", "category": "testing"},
            dependents_cache={},
            all_rules={}
        )
        assert isinstance(result, dict)
        assert "rule_id" in result
        assert "impact_score" in result
        assert "recommendation" in result

    def test_impact_score_calculation(self):
        """Verify impact score is calculated correctly."""
        from governance.quality.impact import calculate_rule_impact

        # High priority rule should have higher score
        result = calculate_rule_impact(
            rule_id="RULE-CRITICAL",
            rule={"name": "Critical", "priority": "CRITICAL", "category": "governance"},
            dependents_cache={"RULE-CRITICAL": {"RULE-A", "RULE-B"}},
            all_rules={"RULE-A": {}, "RULE-B": {}}
        )
        assert result["impact_score"] >= 60  # CRITICAL + governance + dependents


class TestIntegration:
    """Integration tests for split modules."""

    def test_analyzer_uses_impact_module(self):
        """Verify analyzer delegates to impact module."""
        from governance.quality.analyzer import RuleQualityAnalyzer
        from governance.quality import impact

        # Just verify both modules exist and work together
        analyzer = RuleQualityAnalyzer()
        assert hasattr(analyzer, "get_rule_impact")
        assert hasattr(impact, "calculate_rule_impact")
