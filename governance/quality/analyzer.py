"""
Rule Quality Analyzer
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Main analyzer class for rule quality checks.
Per: RULE-010 (Evidence-Based Wisdom), RULE-013 (Rules Applicability)
"""

import os
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, Optional, Set, List

from governance.quality.models import (
    IssueSeverity,
    IssueType,
    RuleIssue,
    RuleHealthReport,
)

# Import TypeDB client
try:
    from governance.client import TypeDBClient
    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False


class RuleQualityAnalyzer:
    """
    Analyzes rule quality and detects issues.

    Usage:
        analyzer = RuleQualityAnalyzer()
        report = analyzer.analyze()

        # Check specific issues
        orphans = analyzer.find_orphaned_rules()
        shallow = analyzer.find_shallow_rules()
    """

    # Thresholds for issue detection
    MAX_DEPENDENCIES = 5  # Over-connected if more than this
    MIN_DEPENDENTS = 0    # Orphaned if less than this (for non-foundational rules)
    FOUNDATIONAL_RULES = {"RULE-001", "RULE-002"}  # Allowed to have no dependents

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None
    ):
        """
        Initialize analyzer with TypeDB connection.

        Args:
            host: TypeDB host (default: from env or localhost)
            port: TypeDB port (default: from env or 1729)
            database: TypeDB database (default: from env or sim-ai-governance)
        """
        self.host = host or os.getenv("TYPEDB_HOST", "localhost")
        self.port = port or int(os.getenv("TYPEDB_PORT", "1729"))
        self.database = database or os.getenv("TYPEDB_DATABASE", "sim-ai-governance")

        self._client: Optional[TypeDBClient] = None
        self._rules_cache: Dict[str, Dict] = {}
        self._dependencies_cache: Dict[str, Set[str]] = {}
        self._dependents_cache: Dict[str, Set[str]] = {}

    def _get_client(self) -> Optional[TypeDBClient]:
        """Get or create TypeDB client."""
        if not TYPEDB_AVAILABLE:
            return None

        if self._client is None:
            self._client = TypeDBClient(
                host=self.host,
                port=self.port,
                database=self.database
            )
            if not self._client.connect():
                self._client = None

        return self._client

    def _load_rules(self) -> Dict[str, Dict]:
        """Load all rules from TypeDB."""
        if self._rules_cache:
            return self._rules_cache

        client = self._get_client()
        if not client:
            return {}

        rules = client.get_all_rules()
        self._rules_cache = {r.id: asdict(r) for r in rules}
        return self._rules_cache

    def _load_dependencies(self) -> None:
        """Load all rule dependencies from TypeDB."""
        if self._dependencies_cache:
            return

        client = self._get_client()
        if not client:
            return

        rules = self._load_rules()

        for rule_id in rules:
            deps = client.get_rule_dependencies(rule_id)
            self._dependencies_cache[rule_id] = set(deps)

            # Build reverse mapping (dependents)
            for dep in deps:
                if dep not in self._dependents_cache:
                    self._dependents_cache[dep] = set()
                self._dependents_cache[dep].add(rule_id)

    def find_orphaned_rules(self) -> List[RuleIssue]:
        """
        Find rules with no dependents (nothing depends on them).

        Excludes foundational rules which are allowed to have no dependents.
        """
        issues = []
        self._load_dependencies()
        rules = self._load_rules()

        for rule_id, rule in rules.items():
            # Skip foundational rules
            if rule_id in self.FOUNDATIONAL_RULES:
                continue

            # Skip non-active rules
            if rule.get("status") != "ACTIVE":
                continue

            dependents = self._dependents_cache.get(rule_id, set())

            if len(dependents) == 0:
                issues.append(RuleIssue(
                    rule_id=rule_id,
                    issue_type=IssueType.ORPHANED,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Rule {rule_id} has no dependents - nothing depends on it",
                    impact="Rule may be unnecessary or under-utilized. Could indicate missing integrations.",
                    remediation="Either: (1) Add dependencies from other rules, (2) Deprecate if truly unused, (3) Mark as foundational if it's a base rule",
                    metadata={"dependents_count": 0, "dependencies_count": len(self._dependencies_cache.get(rule_id, set()))}
                ))

        return issues

    def find_shallow_rules(self) -> List[RuleIssue]:
        """
        Find rules missing important attributes.

        Required: rule-id, rule-name, directive, category, priority, status
        """
        issues = []
        rules = self._load_rules()
        required_attrs = {"id", "name", "directive", "category", "priority", "status"}

        for rule_id, rule in rules.items():
            missing = []
            for attr in required_attrs:
                if not rule.get(attr):
                    missing.append(attr)

            if missing:
                severity = IssueSeverity.HIGH if "directive" in missing else IssueSeverity.MEDIUM
                issues.append(RuleIssue(
                    rule_id=rule_id,
                    issue_type=IssueType.SHALLOW,
                    severity=severity,
                    description=f"Rule {rule_id} missing attributes: {', '.join(missing)}",
                    impact="Incomplete rule definition reduces clarity and enforcement capability",
                    remediation=f"Add missing attributes to rule definition: {', '.join(missing)}",
                    metadata={"missing_attributes": missing}
                ))

        return issues

    def find_over_connected_rules(self) -> List[RuleIssue]:
        """
        Find rules with too many dependencies.

        May indicate:
        - Rule is too broad
        - Need to split into smaller rules
        - Design smell
        """
        issues = []
        self._load_dependencies()
        rules = self._load_rules()

        for rule_id, rule in rules.items():
            deps = self._dependencies_cache.get(rule_id, set())

            if len(deps) > self.MAX_DEPENDENCIES:
                issues.append(RuleIssue(
                    rule_id=rule_id,
                    issue_type=IssueType.OVER_CONNECTED,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Rule {rule_id} has {len(deps)} dependencies (threshold: {self.MAX_DEPENDENCIES})",
                    impact="High coupling makes rule changes risky. May indicate rule is too broad.",
                    remediation="Consider: (1) Split into smaller rules, (2) Review if all dependencies are necessary, (3) Create intermediate abstraction rules",
                    related_rules=list(deps),
                    metadata={"dependency_count": len(deps), "threshold": self.MAX_DEPENDENCIES}
                ))

        return issues

    def find_under_documented_rules(self) -> List[RuleIssue]:
        """
        Find rules not referenced by any document.

        Uses TypeDB query for document-references-rule relation.
        """
        issues = []
        client = self._get_client()
        if not client:
            return issues

        # Query for rules not referenced by documents
        query = """
            match
                $r isa rule-entity, has rule-id $id, has status "ACTIVE";
                not { (referenced-rule: $r) isa document-references-rule; };
            get $id;
        """

        try:
            results = client.execute_query(query)
            for result in results:
                rule_id = result.get("id")
                if rule_id:
                    issues.append(RuleIssue(
                        rule_id=rule_id,
                        issue_type=IssueType.UNDER_DOCUMENTED,
                        severity=IssueSeverity.LOW,
                        description=f"Rule {rule_id} is not referenced by any document",
                        impact="Rule may be hard to discover. Documentation may be incomplete.",
                        remediation="Add reference to rule in relevant documentation (RULES-*.md, README, etc.)",
                        metadata={"referenced_by_documents": 0}
                    ))
        except Exception:
            # Query may fail if no documents exist
            pass

        return issues

    def find_circular_dependencies(self) -> List[RuleIssue]:
        """
        Find circular dependency chains.

        A→B→C→A is a circular dependency.
        """
        issues = []
        self._load_dependencies()

        visited = set()
        rec_stack = set()

        def has_cycle(rule_id: str, path: List[str]) -> Optional[List[str]]:
            visited.add(rule_id)
            rec_stack.add(rule_id)

            for dep in self._dependencies_cache.get(rule_id, set()):
                if dep not in visited:
                    cycle = has_cycle(dep, path + [dep])
                    if cycle:
                        return cycle
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep) if dep in path else 0
                    return path[cycle_start:] + [dep]

            rec_stack.remove(rule_id)
            return None

        for rule_id in self._dependencies_cache:
            if rule_id not in visited:
                cycle = has_cycle(rule_id, [rule_id])
                if cycle:
                    cycle_str = " → ".join(cycle)
                    issues.append(RuleIssue(
                        rule_id=rule_id,
                        issue_type=IssueType.CIRCULAR_DEPENDENCY,
                        severity=IssueSeverity.CRITICAL,
                        description=f"Circular dependency detected: {cycle_str}",
                        impact="Circular dependencies create infinite loops in inference. Must be resolved.",
                        remediation="Break the cycle by removing one dependency. Consider which rule is truly foundational.",
                        related_rules=cycle,
                        metadata={"cycle_length": len(cycle)}
                    ))

        return issues

    def get_rule_impact(self, rule_id: str) -> Dict[str, Any]:
        """
        Analyze impact if a rule is modified or deprecated.

        Returns:
            Dictionary with:
            - affected_rules: Rules that depend on this rule
            - affected_decisions: Decisions that reference this rule
            - total_impact_score: 0-100 score
            - recommendation: Suggested approach
        """
        self._load_dependencies()

        # Get direct and transitive dependents
        direct_dependents = self._dependents_cache.get(rule_id, set())

        # Get transitive dependents (rules that depend on dependents)
        all_dependents = set(direct_dependents)
        to_process = list(direct_dependents)

        while to_process:
            current = to_process.pop()
            for dep in self._dependents_cache.get(current, set()):
                if dep not in all_dependents:
                    all_dependents.add(dep)
                    to_process.append(dep)

        # Calculate impact score
        rules = self._load_rules()
        rule = rules.get(rule_id, {})

        impact_score = 0

        # Base impact from priority
        priority_scores = {"CRITICAL": 40, "HIGH": 30, "MEDIUM": 20, "LOW": 10}
        impact_score += priority_scores.get(rule.get("priority", "MEDIUM"), 20)

        # Impact from dependents
        impact_score += min(len(all_dependents) * 10, 40)

        # Impact from category
        critical_categories = {"governance", "strategic", "architecture"}
        if rule.get("category") in critical_categories:
            impact_score += 20

        impact_score = min(impact_score, 100)

        # Recommendation based on score
        if impact_score >= 70:
            recommendation = "HIGH RISK: Requires thorough review and stakeholder approval before any changes"
        elif impact_score >= 40:
            recommendation = "MEDIUM RISK: Plan changes carefully, update all dependent rules"
        else:
            recommendation = "LOW RISK: Can proceed with standard change process"

        return {
            "rule_id": rule_id,
            "rule_name": rule.get("name", "Unknown"),
            "direct_dependents": list(direct_dependents),
            "all_affected_rules": list(all_dependents),
            "impact_score": impact_score,
            "priority": rule.get("priority"),
            "category": rule.get("category"),
            "recommendation": recommendation
        }

    def analyze(self) -> RuleHealthReport:
        """
        Run full rule quality analysis.

        Returns:
            RuleHealthReport with all detected issues
        """
        rules = self._load_rules()
        all_issues: List[RuleIssue] = []

        # Run all checks
        all_issues.extend(self.find_orphaned_rules())
        all_issues.extend(self.find_shallow_rules())
        all_issues.extend(self.find_over_connected_rules())
        all_issues.extend(self.find_under_documented_rules())
        all_issues.extend(self.find_circular_dependencies())

        # Count by severity
        critical_count = sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH)
        medium_count = sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM)
        low_count = sum(1 for i in all_issues if i.severity == IssueSeverity.LOW)

        # Find healthy rules
        issue_rule_ids = {i.rule_id for i in all_issues}
        healthy_rules = [r for r in rules if r not in issue_rule_ids]

        return RuleHealthReport(
            total_rules=len(rules),
            issues_count=len(all_issues),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            issues=all_issues,
            healthy_rules=healthy_rules,
            timestamp=datetime.now().isoformat()
        )

    def close(self) -> None:
        """Close TypeDB connection."""
        if self._client:
            self._client.close()
            self._client = None
