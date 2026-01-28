"""
Certification Report Generator - Comprehensive test evidence for milestones.

Per RD-TESTING-STRATEGY TEST-005: GitHub milestone certification reporting.

This module generates:
- Full test trace documentation
- BDD evidence summaries
- Rule coverage reports
- Gap resolution tracking
- Trace-level evidence with compression stats

Usage:
    generator = CertificationReportGenerator(evidence_dir="evidence/tests")
    report = generator.generate_report(run_id="2026-01-21_150000")
    generator.write_markdown_report(report, "MILESTONE-CERTIFICATION.md")

Created: 2026-01-21
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CertTestResult:
    """Single test result for certification."""

    __test__ = False  # Prevent pytest collection

    test_id: str
    name: str
    category: str  # unit, integration, e2e
    status: str  # passed, failed, skipped
    duration_ms: float
    intent: Optional[str] = None
    linked_rules: List[str] = field(default_factory=list)
    linked_gaps: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    bdd_steps: List[Dict[str, Any]] = field(default_factory=list)
    trace_summary: Optional[Dict[str, Any]] = None

# Alias for backwards compatibility
TestResult = CertTestResult


@dataclass
class CertificationReport:
    """Complete certification report for a milestone."""

    report_id: str
    milestone: Optional[str] = None
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    commit_sha: Optional[str] = None

    # Test statistics
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    success_rate: str = "0%"

    # Duration
    total_duration_ms: float = 0.0
    total_duration_str: str = "0s"

    # Coverage
    rules_covered: List[str] = field(default_factory=list)
    gaps_addressed: List[str] = field(default_factory=list)
    rule_coverage_count: int = 0
    gap_coverage_count: int = 0

    # By category
    unit_tests: int = 0
    integration_tests: int = 0
    e2e_tests: int = 0

    # Test details
    tests: List[TestResult] = field(default_factory=list)
    failed_tests: List[TestResult] = field(default_factory=list)

    # Trace statistics
    trace_stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "milestone": self.milestone,
            "generated_at": self.generated_at,
            "commit_sha": self.commit_sha,
            "statistics": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "success_rate": self.success_rate,
                "total_duration_ms": self.total_duration_ms,
                "total_duration_str": self.total_duration_str,
            },
            "coverage": {
                "rules_covered": self.rules_covered,
                "gaps_addressed": self.gaps_addressed,
                "rule_coverage_count": self.rule_coverage_count,
                "gap_coverage_count": self.gap_coverage_count,
            },
            "by_category": {
                "unit": self.unit_tests,
                "integration": self.integration_tests,
                "e2e": self.e2e_tests,
            },
            "trace_stats": self.trace_stats,
            "failed_tests": [
                {
                    "test_id": t.test_id,
                    "name": t.name,
                    "error": t.error_message,
                    "linked_rules": t.linked_rules,
                }
                for t in self.failed_tests
            ],
        }


class CertificationReportGenerator:
    """
    Generates comprehensive certification reports from test evidence.

    Integrates with:
    - BDDEvidenceCollector output (evidence/tests/{run_id}/)
    - TraceCapture summaries
    - Rule/gap coverage tracking
    """

    def __init__(
        self,
        evidence_dir: str = "evidence/tests",
        milestone: Optional[str] = None,
        commit_sha: Optional[str] = None,
    ):
        """Initialize report generator.

        Args:
            evidence_dir: Base directory for evidence files
            milestone: GitHub milestone name/number
            commit_sha: Git commit SHA for this certification
        """
        self.evidence_dir = Path(evidence_dir)
        self.milestone = milestone
        self.commit_sha = commit_sha

    def generate_report(self, run_id: Optional[str] = None) -> CertificationReport:
        """Generate certification report from test evidence.

        Args:
            run_id: Specific run ID to report on (uses latest if not specified)

        Returns:
            Complete CertificationReport
        """
        # Find run directory
        run_dir = self._find_run_dir(run_id)
        if not run_dir:
            return CertificationReport(
                report_id=f"CERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                milestone=self.milestone,
                commit_sha=self.commit_sha,
            )

        # Load summary if available
        summary_path = run_dir / "summary.json"
        summary = self._load_json(summary_path) if summary_path.exists() else {}

        # Load all test evidence files
        tests = self._load_test_evidence(run_dir)

        # Build report
        report = CertificationReport(
            report_id=f"CERT-{run_dir.name}",
            milestone=self.milestone,
            commit_sha=self.commit_sha,
        )

        # Populate statistics
        report.total_tests = len(tests)
        report.passed = sum(1 for t in tests if t.status == "passed")
        report.failed = sum(1 for t in tests if t.status == "failed")
        report.skipped = sum(1 for t in tests if t.status == "skipped")
        report.success_rate = (
            f"{(report.passed / report.total_tests * 100):.1f}%"
            if report.total_tests > 0
            else "0%"
        )

        # Duration
        report.total_duration_ms = sum(t.duration_ms for t in tests)
        report.total_duration_str = self._format_duration(report.total_duration_ms)

        # Coverage
        all_rules = set()
        all_gaps = set()
        for t in tests:
            all_rules.update(t.linked_rules)
            all_gaps.update(t.linked_gaps)
        report.rules_covered = sorted(all_rules)
        report.gaps_addressed = sorted(all_gaps)
        report.rule_coverage_count = len(all_rules)
        report.gap_coverage_count = len(all_gaps)

        # By category
        report.unit_tests = sum(1 for t in tests if t.category == "unit")
        report.integration_tests = sum(1 for t in tests if t.category == "integration")
        report.e2e_tests = sum(1 for t in tests if t.category == "e2e")

        # Tests
        report.tests = tests
        report.failed_tests = [t for t in tests if t.status == "failed"]

        # Trace stats from summary
        if summary:
            report.trace_stats = {
                "session_id": summary.get("session_id"),
                "started_at": summary.get("started_at"),
                "completed_at": summary.get("completed_at"),
                "duration_seconds": summary.get("duration_seconds"),
            }

        return report

    def _find_run_dir(self, run_id: Optional[str] = None) -> Optional[Path]:
        """Find the run directory."""
        if not self.evidence_dir.exists():
            return None

        if run_id:
            run_dir = self.evidence_dir / run_id
            return run_dir if run_dir.exists() else None

        # Find most recent run
        run_dirs = [
            d for d in self.evidence_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
        if not run_dirs:
            return None

        return max(run_dirs, key=lambda d: d.stat().st_mtime)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_test_evidence(self, run_dir: Path) -> List[TestResult]:
        """Load all test evidence from run directory."""
        tests = []

        for category in ["unit", "integration", "e2e"]:
            category_dir = run_dir / category
            if not category_dir.exists():
                continue

            for json_file in category_dir.glob("*.json"):
                data = self._load_json(json_file)
                if not data:
                    continue

                test = TestResult(
                    test_id=data.get("test_id", json_file.stem),
                    name=data.get("name", json_file.stem),
                    category=category,
                    status=data.get("status", "unknown"),
                    duration_ms=data.get("duration_ms", 0.0),
                    intent=data.get("intent"),
                    linked_rules=data.get("linked_rules", []),
                    linked_gaps=data.get("linked_gaps", []),
                    error_message=data.get("error_message"),
                    bdd_steps=data.get("bdd_steps", []),
                    trace_summary=data.get("trace_summary"),
                )
                tests.append(test)

        return tests

    def _format_duration(self, ms: float) -> str:
        """Format duration in human-readable form."""
        seconds = ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"

    def write_markdown_report(
        self,
        report: CertificationReport,
        output_path: str,
    ) -> Path:
        """Write certification report as markdown.

        Args:
            report: CertificationReport to write
            output_path: Output file path

        Returns:
            Path to written file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = []

        # Header
        lines.append("# Certification Report")
        lines.append("")
        lines.append(f"**Report ID:** {report.report_id}")
        if report.milestone:
            lines.append(f"**Milestone:** {report.milestone}")
        if report.commit_sha:
            lines.append(f"**Commit:** `{report.commit_sha[:8]}`")
        lines.append(f"**Generated:** {report.generated_at}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Tests | {report.total_tests} |")
        lines.append(f"| Passed | {report.passed} ✅ |")
        lines.append(f"| Failed | {report.failed} ❌ |")
        lines.append(f"| Skipped | {report.skipped} ⏭️ |")
        lines.append(f"| Success Rate | {report.success_rate} |")
        lines.append(f"| Duration | {report.total_duration_str} |")
        lines.append("")

        # By Category
        lines.append("## Tests by Category")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| Unit | {report.unit_tests} |")
        lines.append(f"| Integration | {report.integration_tests} |")
        lines.append(f"| E2E | {report.e2e_tests} |")
        lines.append("")

        # Coverage
        lines.append("## Coverage")
        lines.append("")
        lines.append(f"**Rules Covered:** {report.rule_coverage_count}")
        if report.rules_covered:
            lines.append(f"- {', '.join(report.rules_covered[:20])}")
            if len(report.rules_covered) > 20:
                lines.append(f"  - ... and {len(report.rules_covered) - 20} more")
        lines.append("")
        lines.append(f"**Gaps Addressed:** {report.gap_coverage_count}")
        if report.gaps_addressed:
            lines.append(f"- {', '.join(report.gaps_addressed[:20])}")
            if len(report.gaps_addressed) > 20:
                lines.append(f"  - ... and {len(report.gaps_addressed) - 20} more")
        lines.append("")

        # Failed Tests
        if report.failed_tests:
            lines.append("## Failed Tests")
            lines.append("")
            lines.append("| Test | Error | Rules |")
            lines.append("|------|-------|-------|")
            for t in report.failed_tests[:10]:
                error_preview = (t.error_message or "")[:50]
                if len(t.error_message or "") > 50:
                    error_preview += "..."
                rules = ", ".join(t.linked_rules[:3]) if t.linked_rules else "-"
                lines.append(f"| {t.name} | {error_preview} | {rules} |")
            if len(report.failed_tests) > 10:
                lines.append(f"| ... | {len(report.failed_tests) - 10} more failed tests | |")
            lines.append("")

        # Trace Stats
        if report.trace_stats:
            lines.append("## Trace Evidence")
            lines.append("")
            for key, value in report.trace_stats.items():
                if value:
                    lines.append(f"- **{key}:** {value}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Per RD-TESTING-STRATEGY TEST-005: GitHub milestone certification*")
        lines.append("*Per RULE-020: LLM-Driven E2E Test Generation*")
        lines.append("")

        # Write file
        content = "\n".join(lines)
        with open(path, "w") as f:
            f.write(content)

        return path

    def write_json_report(
        self,
        report: CertificationReport,
        output_path: str,
    ) -> Path:
        """Write certification report as JSON.

        Args:
            report: CertificationReport to write
            output_path: Output file path

        Returns:
            Path to written file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        return path


# CLI-compatible function for use in GitHub Actions
def generate_certification(
    evidence_dir: str = "evidence/tests",
    output_dir: str = "results",
    milestone: Optional[str] = None,
    commit_sha: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate certification report from evidence.

    This function can be called from CI/CD pipelines.

    Args:
        evidence_dir: Directory containing test evidence
        output_dir: Directory for output files
        milestone: GitHub milestone name
        commit_sha: Git commit SHA
        run_id: Specific run ID to report on

    Returns:
        Dictionary with report summary and file paths
    """
    generator = CertificationReportGenerator(
        evidence_dir=evidence_dir,
        milestone=milestone,
        commit_sha=commit_sha,
    )

    report = generator.generate_report(run_id=run_id)

    # Write reports
    output_path = Path(output_dir)
    md_path = generator.write_markdown_report(
        report, str(output_path / "CERTIFICATION-REPORT.md")
    )
    json_path = generator.write_json_report(
        report, str(output_path / "certification-report.json")
    )

    return {
        "report_id": report.report_id,
        "success_rate": report.success_rate,
        "total_tests": report.total_tests,
        "passed": report.passed,
        "failed": report.failed,
        "rules_covered": report.rule_coverage_count,
        "gaps_addressed": report.gap_coverage_count,
        "markdown_report": str(md_path),
        "json_report": str(json_path),
    }


# Entry point for CLI
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Generate certification report from test evidence"
    )
    parser.add_argument(
        "--evidence-dir",
        default="evidence/tests",
        help="Directory containing test evidence",
    )
    parser.add_argument(
        "--output-dir", default="results", help="Directory for output files"
    )
    parser.add_argument("--milestone", help="GitHub milestone name")
    parser.add_argument(
        "--commit-sha",
        default=os.environ.get("GITHUB_SHA"),
        help="Git commit SHA",
    )
    parser.add_argument("--run-id", help="Specific run ID to report on")

    args = parser.parse_args()

    result = generate_certification(
        evidence_dir=args.evidence_dir,
        output_dir=args.output_dir,
        milestone=args.milestone,
        commit_sha=args.commit_sha,
        run_id=args.run_id,
    )

    print(f"Certification Report Generated: {result['report_id']}")
    print(f"  Success Rate: {result['success_rate']}")
    print(f"  Tests: {result['passed']}/{result['total_tests']} passed")
    print(f"  Rules Covered: {result['rules_covered']}")
    print(f"  Gaps Addressed: {result['gaps_addressed']}")
    print(f"  Reports: {result['markdown_report']}, {result['json_report']}")
