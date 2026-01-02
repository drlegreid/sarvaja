"""
Exploratory Audit Framework - LLM + Playwright MCP Integration.

Per user guidance (2026-01-02):
- Robot Framework + Playwright: deterministic E2E UI tests (existing)
- Exploratory UI: LLM + Playwright MCP audits system and finds gaps/inconsistencies
- Reconciliate test best practices with OOP principles + component reusability
- Exploratory heuristics should use LLM navigation to continue from deterministic tests
- Exploratory audit reports should be written as files for test coverage improvement

Architecture:
1. Deterministic tests (Robot Framework) → establish baseline coverage
2. LLM exploratory auditor → continues from where deterministic tests lead
3. Horizontal exploration → breadth-first across features
4. Vertical exploration → depth-first into specific areas
5. Audit reports → saved to evidence/exploratory/ for addressing gaps

Created: 2026-01-02
Per GAP-HEUR-001
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class ExplorationMode(Enum):
    """Exploration strategy mode."""
    HORIZONTAL = "horizontal"  # Breadth-first across features
    VERTICAL = "vertical"      # Depth-first into specific areas


class AuditSeverity(Enum):
    """Severity levels for audit findings."""
    CRITICAL = "CRITICAL"  # Blocking issues
    HIGH = "HIGH"          # Significant gaps
    MEDIUM = "MEDIUM"      # Improvements needed
    LOW = "LOW"            # Minor observations


@dataclass
class AuditFinding:
    """Individual audit finding."""
    finding_id: str
    severity: AuditSeverity
    category: str  # SFDIPOT or CRUCSS aspect
    description: str
    evidence: str
    location: str  # File path or UI location
    related_test: Optional[str] = None
    recommendation: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExploratoryAuditReport:
    """Audit report for exploratory testing session."""
    report_id: str
    session_date: str
    target_area: str  # What was being audited
    exploration_mode: ExplorationMode
    heuristics_used: List[str]  # SFDIPOT.Data, CRUCSS.Security, etc.
    deterministic_baseline: List[str]  # Tests that led to this exploration
    findings: List[AuditFinding] = field(default_factory=list)
    coverage_gaps: List[str] = field(default_factory=list)
    test_improvements: List[str] = field(default_factory=list)
    llm_observations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_finding(self, finding: AuditFinding):
        """Add a finding to the report."""
        self.findings.append(finding)

    def add_coverage_gap(self, gap: str):
        """Add a coverage gap identified during audit."""
        self.coverage_gaps.append(gap)

    def add_test_improvement(self, improvement: str):
        """Add a test improvement suggestion."""
        self.test_improvements.append(improvement)

    def add_llm_observation(self, observation: str):
        """Add an LLM-generated observation."""
        self.llm_observations.append(observation)

    def summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        severity_counts = {s.value: 0 for s in AuditSeverity}
        for f in self.findings:
            severity_counts[f.severity.value] += 1

        return {
            "report_id": self.report_id,
            "target_area": self.target_area,
            "exploration_mode": self.exploration_mode.value,
            "total_findings": len(self.findings),
            "findings_by_severity": severity_counts,
            "coverage_gaps_count": len(self.coverage_gaps),
            "test_improvements_count": len(self.test_improvements),
            "llm_observations_count": len(self.llm_observations),
        }

    def to_dict(self) -> dict:
        """Convert report to dictionary for JSON export."""
        return {
            "report_id": self.report_id,
            "session_date": self.session_date,
            "target_area": self.target_area,
            "exploration_mode": self.exploration_mode.value,
            "heuristics_used": self.heuristics_used,
            "deterministic_baseline": self.deterministic_baseline,
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "severity": f.severity.value,
                    "category": f.category,
                    "description": f.description,
                    "evidence": f.evidence,
                    "location": f.location,
                    "related_test": f.related_test,
                    "recommendation": f.recommendation,
                    "timestamp": f.timestamp,
                }
                for f in self.findings
            ],
            "coverage_gaps": self.coverage_gaps,
            "test_improvements": self.test_improvements,
            "llm_observations": self.llm_observations,
            "timestamp": self.timestamp,
            "summary": self.summary(),
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Exploratory Audit Report: {self.report_id}",
            "",
            f"**Date:** {self.session_date}",
            f"**Target Area:** {self.target_area}",
            f"**Exploration Mode:** {self.exploration_mode.value.capitalize()}",
            f"**Heuristics Used:** {', '.join(self.heuristics_used)}",
            "",
            "## Deterministic Baseline",
            "",
            "Tests that led to this exploratory session:",
            "",
        ]

        for test in self.deterministic_baseline:
            lines.append(f"- `{test}`")

        lines.extend([
            "",
            "## Findings",
            "",
        ])

        if self.findings:
            lines.append("| ID | Severity | Category | Description |")
            lines.append("|----|----------|----------|-------------|")
            for f in self.findings:
                lines.append(f"| {f.finding_id} | {f.severity.value} | {f.category} | {f.description} |")
        else:
            lines.append("*No findings recorded.*")

        lines.extend([
            "",
            "## Coverage Gaps",
            "",
        ])

        if self.coverage_gaps:
            for gap in self.coverage_gaps:
                lines.append(f"- {gap}")
        else:
            lines.append("*No coverage gaps identified.*")

        lines.extend([
            "",
            "## Test Improvements",
            "",
        ])

        if self.test_improvements:
            for imp in self.test_improvements:
                lines.append(f"- {imp}")
        else:
            lines.append("*No test improvements suggested.*")

        lines.extend([
            "",
            "## LLM Observations",
            "",
        ])

        if self.llm_observations:
            for obs in self.llm_observations:
                lines.append(f"> {obs}")
                lines.append("")
        else:
            lines.append("*No LLM observations recorded.*")

        lines.extend([
            "",
            "---",
            "",
            f"*Generated: {self.timestamp}*",
        ])

        return "\n".join(lines)


class ExploratoryAuditor:
    """Coordinates exploratory testing with LLM + Playwright MCP."""

    def __init__(self, evidence_dir: str = "evidence/exploratory"):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.current_report: Optional[ExploratoryAuditReport] = None

    def start_audit(
        self,
        target_area: str,
        mode: ExplorationMode = ExplorationMode.HORIZONTAL,
        heuristics: List[str] = None,
        baseline_tests: List[str] = None,
    ) -> ExploratoryAuditReport:
        """Start a new exploratory audit session."""
        report_id = f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.current_report = ExploratoryAuditReport(
            report_id=report_id,
            session_date=datetime.now().strftime("%Y-%m-%d"),
            target_area=target_area,
            exploration_mode=mode,
            heuristics_used=heuristics or ["SFDIPOT.Function", "CRUCSS.Capability"],
            deterministic_baseline=baseline_tests or [],
        )
        return self.current_report

    def add_finding(
        self,
        severity: AuditSeverity,
        category: str,
        description: str,
        evidence: str,
        location: str,
        related_test: str = None,
        recommendation: str = None,
    ) -> AuditFinding:
        """Add a finding to the current audit."""
        if not self.current_report:
            raise ValueError("No audit in progress. Call start_audit() first.")

        finding_id = f"FIND-{len(self.current_report.findings) + 1:03d}"
        finding = AuditFinding(
            finding_id=finding_id,
            severity=severity,
            category=category,
            description=description,
            evidence=evidence,
            location=location,
            related_test=related_test,
            recommendation=recommendation,
        )
        self.current_report.add_finding(finding)
        return finding

    def save_report(self) -> tuple[Path, Path]:
        """Save report to JSON and Markdown files."""
        if not self.current_report:
            raise ValueError("No audit in progress.")

        json_path = self.evidence_dir / f"{self.current_report.report_id}.json"
        md_path = self.evidence_dir / f"{self.current_report.report_id}.md"

        with open(json_path, "w") as f:
            json.dump(self.current_report.to_dict(), f, indent=2)

        with open(md_path, "w") as f:
            f.write(self.current_report.to_markdown())

        return json_path, md_path


# =============================================================================
# LLM Navigation Prompts for Playwright MCP
# =============================================================================

HORIZONTAL_EXPLORATION_PROMPT = """
You are conducting HORIZONTAL exploratory testing on the Governance Dashboard.

Target Area: {target_area}
Baseline Tests: {baseline_tests}
Heuristics: {heuristics}

Your goal is BREADTH-FIRST exploration:
1. Identify all navigation paths from the current location
2. Visit each major section briefly
3. Note any missing features, broken links, or UI inconsistencies
4. Compare actual behavior with expected per SFDIPOT heuristics

For each section, check:
- STRUCTURE: Does the component hierarchy make sense?
- FUNCTION: Do buttons/links work as expected?
- DATA: Are required fields present and valid?
- INTERFACES: Are navigation flows intuitive?

Report findings using AuditSeverity levels:
- CRITICAL: Blocking issues (page won't load, data loss)
- HIGH: Significant gaps (missing features, wrong data)
- MEDIUM: Improvements needed (UX issues, minor bugs)
- LOW: Minor observations (cosmetic, edge cases)

Use Playwright MCP to navigate and verify behaviors.
"""

VERTICAL_EXPLORATION_PROMPT = """
You are conducting VERTICAL exploratory testing on the Governance Dashboard.

Target Area: {target_area}
Baseline Tests: {baseline_tests}
Heuristics: {heuristics}

Your goal is DEPTH-FIRST exploration:
1. Focus deeply on the specific target area
2. Test all edge cases and boundary conditions
3. Verify data integrity at every step
4. Check error handling and recovery

For the target area, thoroughly check:
- DATA: Field validation, null handling, data types
- OPERATIONS: Error handling, user feedback
- TIME: Response latency, loading states
- PLATFORM: Browser compatibility, responsive design

Per CRUCSS heuristics:
- RELIABILITY: Does it handle failures gracefully?
- SECURITY: Are inputs sanitized? Auth enforced?
- USABILITY: Is the feature easy to use correctly?

Report findings with detailed evidence.
Use Playwright MCP to interact and capture screenshots.
"""


def get_exploration_prompt(mode: ExplorationMode, **kwargs) -> str:
    """Get the appropriate LLM prompt for exploration mode."""
    if mode == ExplorationMode.HORIZONTAL:
        return HORIZONTAL_EXPLORATION_PROMPT.format(**kwargs)
    else:
        return VERTICAL_EXPLORATION_PROMPT.format(**kwargs)
