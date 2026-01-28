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

