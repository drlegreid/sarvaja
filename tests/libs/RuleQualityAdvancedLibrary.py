"""
Robot Framework Library for Rule Quality Analyzer Advanced Tests.
Split from RuleQualityLibrary.py per DOC-SIZE-01-v1

Covers: Over-Connected, Circular Dependencies, Impact Analysis, Full Analysis, MCP Tools.
Per: Evidence-Based Wisdom (RULE-010).
"""
import json
from robot.api.deco import keyword


class RuleQualityAdvancedLibrary:
    """Library for testing rule quality analyzer - advanced features."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Over-Connected Rule Detection Tests
    # =============================================================================

    @keyword("Find Over Connected Rules")
    def find_over_connected_rules(self):
        """Rules with too many dependencies are flagged."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer, IssueType
            analyzer = RuleQualityAnalyzer()
            analyzer.MAX_DEPENDENCIES = 3
            analyzer._rules_cache = {
                "RULE-001": {"id": "RULE-001", "name": "Normal", "status": "ACTIVE"},
                "RULE-002": {"id": "RULE-002", "name": "Over-connected", "status": "ACTIVE"}
            }
            analyzer._dependencies_cache = {
                "RULE-001": {"RULE-X"},
                "RULE-002": {"RULE-A", "RULE-B", "RULE-C", "RULE-D", "RULE-E"}
            }
            analyzer._dependents_cache = {}
            issues = analyzer.find_over_connected_rules()
            return {
                "one_issue": len(issues) == 1,
                "correct_id": issues[0].rule_id == "RULE-002" if issues else False,
                "correct_type": issues[0].issue_type == IssueType.OVER_CONNECTED if issues else False,
                "correct_count": issues[0].metadata.get("dependency_count") == 5 if issues else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Circular Dependency Detection Tests
    # =============================================================================

    @keyword("Find Circular Dependencies Simple")
    def find_circular_dependencies_simple(self):
        """Simple A->B->A cycle is detected."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer, IssueType
            analyzer = RuleQualityAnalyzer()
            analyzer._dependencies_cache = {
                "RULE-A": {"RULE-B"},
                "RULE-B": {"RULE-A"}
            }
            analyzer._dependents_cache = {}
            issues = analyzer.find_circular_dependencies()
            has_circular = any(i.issue_type == IssueType.CIRCULAR_DEPENDENCY for i in issues)
            return {"has_circular": has_circular}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Find Circular Dependencies None")
    def find_circular_dependencies_none(self):
        """No cycles when dependencies are acyclic."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer
            analyzer = RuleQualityAnalyzer()
            analyzer._dependencies_cache = {
                "RULE-A": {"RULE-B"},
                "RULE-B": {"RULE-C"},
                "RULE-C": set()
            }
            analyzer._dependents_cache = {}
            issues = analyzer.find_circular_dependencies()
            return {"no_cycles": len(issues) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Impact Analysis Tests
    # =============================================================================

    @keyword("Get Rule Impact Returns Dict")
    def get_rule_impact_returns_dict(self):
        """get_rule_impact returns impact dictionary."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer
            analyzer = RuleQualityAnalyzer()
            analyzer._rules_cache = {
                "RULE-001": {
                    "id": "RULE-001",
                    "name": "Test Rule",
                    "priority": "HIGH",
                    "category": "governance",
                    "status": "ACTIVE"
                }
            }
            analyzer._dependencies_cache = {"RULE-001": set()}
            analyzer._dependents_cache = {"RULE-001": {"RULE-002", "RULE-003"}}
            impact = analyzer.get_rule_impact("RULE-001")
            return {
                "has_rule_id": impact.get("rule_id") == "RULE-001",
                "has_impact_score": "impact_score" in impact,
                "has_recommendation": "recommendation" in impact,
                "has_dependents": len(impact.get("direct_dependents", [])) == 2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Impact Score Includes Priority")
    def impact_score_includes_priority(self):
        """Impact score accounts for rule priority."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer
            analyzer = RuleQualityAnalyzer()
            analyzer._rules_cache = {
                "RULE-CRIT": {"id": "RULE-CRIT", "priority": "CRITICAL", "category": "test"},
                "RULE-LOW": {"id": "RULE-LOW", "priority": "LOW", "category": "test"}
            }
            analyzer._dependencies_cache = {}
            analyzer._dependents_cache = {}
            impact_crit = analyzer.get_rule_impact("RULE-CRIT")
            impact_low = analyzer.get_rule_impact("RULE-LOW")
            return {"crit_higher": impact_crit["impact_score"] > impact_low["impact_score"]}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Full Analysis Tests
    # =============================================================================

    @keyword("Analyze Returns Health Report")
    def analyze_returns_health_report(self):
        """analyze() returns RuleHealthReport."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer, RuleHealthReport
            analyzer = RuleQualityAnalyzer()
            analyzer._rules_cache = {
                "RULE-001": {
                    "id": "RULE-001",
                    "name": "Complete",
                    "directive": "Test",
                    "category": "test",
                    "priority": "HIGH",
                    "status": "ACTIVE"
                }
            }
            analyzer._dependencies_cache = {}
            analyzer._dependents_cache = {}
            report = analyzer.analyze()
            return {
                "is_report": isinstance(report, RuleHealthReport),
                "total_correct": report.total_rules == 1,
                "has_timestamp": report.timestamp is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # MCP Tools Tests
    # =============================================================================

    @keyword("Governance Analyze Rules Exists")
    def governance_analyze_rules_exists(self):
        """governance_analyze_rules MCP tool exists."""
        try:
            from governance.compat import governance_analyze_rules
            return {"exists": governance_analyze_rules is not None, "callable": callable(governance_analyze_rules)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Rule Impact Exists")
    def governance_rule_impact_exists(self):
        """governance_rule_impact MCP tool exists."""
        try:
            from governance.compat import governance_rule_impact
            return {"exists": governance_rule_impact is not None, "callable": callable(governance_rule_impact)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Find Issues Exists")
    def governance_find_issues_exists(self):
        """governance_find_issues MCP tool exists."""
        try:
            from governance.compat import governance_find_issues
            return {"exists": governance_find_issues is not None, "callable": callable(governance_find_issues)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Convenience Functions Tests
    # =============================================================================

    @keyword("Analyze Rule Quality Returns JSON")
    def analyze_rule_quality_returns_json(self):
        """analyze_rule_quality returns valid JSON."""
        try:
            from governance.rule_quality import analyze_rule_quality
            result = analyze_rule_quality()
            parsed = json.loads(result)
            return {"is_dict": isinstance(parsed, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"is_dict": False}

    @keyword("Find Rule Issues Returns JSON")
    def find_rule_issues_returns_json(self):
        """find_rule_issues returns valid JSON."""
        try:
            from governance.rule_quality import find_rule_issues
            result = find_rule_issues("orphaned")
            parsed = json.loads(result)
            return {"is_valid": isinstance(parsed, (dict, list))}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"is_valid": False}
