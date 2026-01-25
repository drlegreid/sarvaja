"""
Robot Framework Library for Rule Quality Analyzer Tests.

TDD tests per RULE-004: Exploratory Testing & Executable Specification.
Per: Evidence-Based Wisdom (RULE-010).
Migrated from tests/test_rule_quality.py
"""
import json
from robot.api.deco import keyword


class RuleQualityLibrary:
    """Library for testing rule quality analyzer."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Unit Tests - Classes
    # =============================================================================

    @keyword("Rule Quality Analyzer Class Exists")
    def rule_quality_analyzer_class_exists(self):
        """RuleQualityAnalyzer class exists and is importable."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer
            return {"exists": RuleQualityAnalyzer is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Issue Severity Enum Exists")
    def issue_severity_enum_exists(self):
        """IssueSeverity enum has expected values."""
        try:
            from governance.rule_quality import IssueSeverity
            return {
                "critical": IssueSeverity.CRITICAL.value == "CRITICAL",
                "high": IssueSeverity.HIGH.value == "HIGH",
                "medium": IssueSeverity.MEDIUM.value == "MEDIUM",
                "low": IssueSeverity.LOW.value == "LOW"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Issue Type Enum Exists")
    def issue_type_enum_exists(self):
        """IssueType enum has expected values."""
        try:
            from governance.rule_quality import IssueType
            return {
                "orphaned": IssueType.ORPHANED.value == "orphaned",
                "shallow": IssueType.SHALLOW.value == "shallow",
                "over_connected": IssueType.OVER_CONNECTED.value == "over_connected",
                "circular": IssueType.CIRCULAR_DEPENDENCY.value == "circular"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # RuleIssue Dataclass Tests
    # =============================================================================

    @keyword("Rule Issue Creation")
    def rule_issue_creation(self):
        """RuleIssue dataclass creates correctly."""
        try:
            from governance.rule_quality import RuleIssue, IssueType, IssueSeverity
            issue = RuleIssue(
                rule_id="RULE-001",
                issue_type=IssueType.ORPHANED,
                severity=IssueSeverity.MEDIUM,
                description="Test description",
                impact="Test impact",
                remediation="Test remediation"
            )
            return {
                "rule_id_correct": issue.rule_id == "RULE-001",
                "type_correct": issue.issue_type == IssueType.ORPHANED,
                "severity_correct": issue.severity == IssueSeverity.MEDIUM
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Issue To Dict")
    def rule_issue_to_dict(self):
        """RuleIssue converts to dictionary."""
        try:
            from governance.rule_quality import RuleIssue, IssueType, IssueSeverity
            issue = RuleIssue(
                rule_id="RULE-002",
                issue_type=IssueType.SHALLOW,
                severity=IssueSeverity.HIGH,
                description="Missing directive",
                impact="Unclear enforcement",
                remediation="Add directive"
            )
            d = issue.to_dict()
            return {
                "rule_id_correct": d["rule_id"] == "RULE-002",
                "issue_type_correct": d["issue_type"] == "shallow",
                "severity_correct": d["severity"] == "HIGH"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # RuleHealthReport Tests
    # =============================================================================

    @keyword("Rule Health Report Creation")
    def rule_health_report_creation(self):
        """RuleHealthReport dataclass creates correctly."""
        try:
            from governance.rule_quality import RuleHealthReport
            report = RuleHealthReport(
                total_rules=10,
                issues_count=3,
                critical_count=1,
                high_count=1,
                medium_count=1,
                low_count=0,
                issues=[],
                healthy_rules=["RULE-001", "RULE-002"],
                timestamp="2024-12-24T12:00:00"
            )
            return {
                "total_correct": report.total_rules == 10,
                "issues_correct": report.issues_count == 3,
                "healthy_correct": len(report.healthy_rules) == 2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Health Report To JSON")
    def rule_health_report_to_json(self):
        """RuleHealthReport converts to JSON."""
        try:
            from governance.rule_quality import RuleHealthReport
            report = RuleHealthReport(
                total_rules=5,
                issues_count=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                issues=[],
                healthy_rules=["RULE-001"],
                timestamp="2024-12-24T12:00:00"
            )
            json_str = report.to_json()
            parsed = json.loads(json_str)
            return {
                "total_correct": parsed["total_rules"] == 5,
                "issues_correct": parsed["issues_count"] == 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Orphaned Rule Detection Tests
    # =============================================================================

    @keyword("Find Orphaned Rules Excludes Foundational")
    def find_orphaned_rules_excludes_foundational(self):
        """Foundational rules (RULE-001, RULE-002) are not flagged as orphaned."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer
            analyzer = RuleQualityAnalyzer()
            analyzer._rules_cache = {
                "RULE-001": {"id": "RULE-001", "name": "Session Evidence", "status": "ACTIVE"},
                "RULE-002": {"id": "RULE-002", "name": "Architecture", "status": "ACTIVE"}
            }
            analyzer._dependencies_cache = {}
            analyzer._dependents_cache = {}
            issues = analyzer.find_orphaned_rules()
            orphan_ids = [i.rule_id for i in issues]
            return {
                "rule_001_not_orphan": "RULE-001" not in orphan_ids,
                "rule_002_not_orphan": "RULE-002" not in orphan_ids
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Find Orphaned Rules Flags Non Foundational")
    def find_orphaned_rules_flags_non_foundational(self):
        """Non-foundational rules with no dependents are flagged."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer, IssueType
            analyzer = RuleQualityAnalyzer()
            analyzer._rules_cache = {
                "RULE-001": {"id": "RULE-001", "name": "Session", "status": "ACTIVE"},
                "RULE-099": {"id": "RULE-099", "name": "Orphan", "status": "ACTIVE"}
            }
            analyzer._dependencies_cache = {"RULE-099": set()}
            analyzer._dependents_cache = {}
            issues = analyzer.find_orphaned_rules()
            return {
                "one_issue": len(issues) == 1,
                "correct_id": issues[0].rule_id == "RULE-099" if issues else False,
                "correct_type": issues[0].issue_type == IssueType.ORPHANED if issues else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Shallow Rule Detection Tests
    # =============================================================================

    @keyword("Find Shallow Rules Detects Missing Attrs")
    def find_shallow_rules_detects_missing_attrs(self):
        """Rules missing required attributes are flagged."""
        try:
            from governance.rule_quality import RuleQualityAnalyzer, IssueType
            analyzer = RuleQualityAnalyzer()
            analyzer._rules_cache = {
                "RULE-001": {
                    "id": "RULE-001",
                    "name": "Complete Rule",
                    "directive": "Do something",
                    "category": "governance",
                    "priority": "HIGH",
                    "status": "ACTIVE"
                },
                "RULE-002": {
                    "id": "RULE-002",
                    "name": "Incomplete Rule",
                    "status": "ACTIVE"
                }
            }
            issues = analyzer.find_shallow_rules()
            return {
                "one_issue": len(issues) == 1,
                "correct_id": issues[0].rule_id == "RULE-002" if issues else False,
                "correct_type": issues[0].issue_type == IssueType.SHALLOW if issues else False,
                "has_missing": "directive" in issues[0].metadata.get("missing_attributes", []) if issues else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

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
        """Simple A→B→A cycle is detected."""
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
