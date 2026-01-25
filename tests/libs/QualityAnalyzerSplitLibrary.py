"""
RF-004: Robot Framework Library for Quality Analyzer Split Tests.

Wraps tests/test_quality_analyzer_split.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Files under 400 lines.
"""

import sys
import inspect
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

QUALITY_DIR = PROJECT_ROOT / "governance" / "quality"


class QualityAnalyzerSplitLibrary:
    """Robot Framework library for Quality Analyzer Split tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def get_quality_dir(self) -> str:
        """Get the quality directory path."""
        return str(QUALITY_DIR)

    def analyzer_module_exists(self) -> bool:
        """Check if analyzer.py exists."""
        return (QUALITY_DIR / "analyzer.py").exists()

    def impact_module_exists(self) -> bool:
        """Check if impact.py exists."""
        return (QUALITY_DIR / "impact.py").exists()

    def get_file_line_count(self, filename: str) -> int:
        """Get line count for a file in the quality directory."""
        filepath = QUALITY_DIR / filename
        if not filepath.exists():
            return -1
        with open(filepath, "r") as f:
            return len(f.readlines())

    def file_under_limit(self, filename: str, limit: int = 400) -> Dict[str, Any]:
        """Check if file is under line limit."""
        lines = self.get_file_line_count(filename)
        return {
            "filename": filename,
            "lines": lines,
            "limit": limit,
            "under_limit": lines >= 0 and lines < limit
        }

    def import_rule_quality_analyzer(self) -> bool:
        """Try to import RuleQualityAnalyzer class."""
        try:
            from governance.quality.analyzer import RuleQualityAnalyzer
            return RuleQualityAnalyzer is not None
        except ImportError:
            return False

    def import_calculate_rule_impact(self) -> bool:
        """Try to import calculate_rule_impact function."""
        try:
            from governance.quality.impact import calculate_rule_impact
            return callable(calculate_rule_impact)
        except ImportError:
            return False

    def analyzer_has_get_rule_impact(self) -> bool:
        """Check if RuleQualityAnalyzer has get_rule_impact method."""
        try:
            from governance.quality.analyzer import RuleQualityAnalyzer
            analyzer = RuleQualityAnalyzer()
            return hasattr(analyzer, "get_rule_impact") and callable(analyzer.get_rule_impact)
        except (ImportError, Exception):
            return False

    def impact_module_in_quality_init(self) -> bool:
        """Check if impact module is accessible from quality package."""
        try:
            from governance.quality import impact
            return hasattr(impact, "calculate_rule_impact")
        except ImportError:
            return False

    def get_calculate_rule_impact_params(self) -> Dict[str, Any]:
        """Get function signature parameters."""
        try:
            from governance.quality.impact import calculate_rule_impact
            sig = inspect.signature(calculate_rule_impact)
            params = list(sig.parameters.keys())
            return {
                "params": params,
                "has_rule_id": "rule_id" in params,
                "has_rule": "rule" in params,
                "has_dependents_cache": "dependents_cache" in params
            }
        except (ImportError, Exception) as e:
            return {"error": str(e), "params": []}

    def calculate_rule_impact_returns_dict(self) -> Dict[str, Any]:
        """Test calculate_rule_impact returns dictionary with required keys."""
        try:
            from governance.quality.impact import calculate_rule_impact
            result = calculate_rule_impact(
                rule_id="RULE-TEST",
                rule={"name": "Test", "priority": "MEDIUM", "category": "testing"},
                dependents_cache={},
                all_rules={}
            )
            return {
                "is_dict": isinstance(result, dict),
                "has_rule_id": "rule_id" in result if isinstance(result, dict) else False,
                "has_impact_score": "impact_score" in result if isinstance(result, dict) else False,
                "has_recommendation": "recommendation" in result if isinstance(result, dict) else False
            }
        except Exception as e:
            return {"error": str(e), "is_dict": False}

    def test_critical_rule_impact_score(self) -> Dict[str, Any]:
        """Test high priority rule has higher impact score."""
        try:
            from governance.quality.impact import calculate_rule_impact
            result = calculate_rule_impact(
                rule_id="RULE-CRITICAL",
                rule={"name": "Critical", "priority": "CRITICAL", "category": "governance"},
                dependents_cache={"RULE-CRITICAL": {"RULE-A", "RULE-B"}},
                all_rules={"RULE-A": {}, "RULE-B": {}}
            )
            return {
                "impact_score": result.get("impact_score", 0),
                "meets_threshold": result.get("impact_score", 0) >= 60
            }
        except Exception as e:
            return {"error": str(e), "impact_score": 0, "meets_threshold": False}

    def verify_integration(self) -> Dict[str, bool]:
        """Verify analyzer and impact modules work together."""
        return {
            "analyzer_import_ok": self.import_rule_quality_analyzer(),
            "impact_import_ok": self.import_calculate_rule_impact(),
            "analyzer_has_method": self.analyzer_has_get_rule_impact(),
            "impact_in_package": self.impact_module_in_quality_init()
        }
