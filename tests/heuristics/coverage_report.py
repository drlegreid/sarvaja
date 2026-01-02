"""
Heuristic Coverage Report Generator.

Per GAP-HEUR-001: Generates coverage reports showing which heuristics
are being tested across API and UI levels.

Usage:
    from tests.heuristics import HeuristicCoverageReport

    report = HeuristicCoverageReport()
    report.collect()
    print(report.summary())
    report.save_json("results/heuristic_coverage.json")

Created: 2026-01-02
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .sfdipot import get_sfdipot_tests, SFDIPOTAspect, get_coverage_by_aspect as sfdipot_coverage
from .crucss import get_crucss_tests, CRUCSSAspect, get_coverage_by_aspect as crucss_coverage


class HeuristicCoverageReport:
    """Generate coverage report for exploratory heuristics."""

    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.sfdipot_tests = []
        self.crucss_tests = []
        self.sfdipot_coverage = {}
        self.crucss_coverage = {}

    def collect(self):
        """Collect all registered heuristic tests."""
        self.sfdipot_tests = get_sfdipot_tests()
        self.crucss_tests = get_crucss_tests()
        self.sfdipot_coverage = sfdipot_coverage()
        self.crucss_coverage = crucss_coverage()

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 60,
            "HEURISTIC COVERAGE REPORT",
            f"Generated: {self.timestamp}",
            "=" * 60,
            "",
            "SFDIPOT Coverage:",
            "-" * 40,
        ]

        for aspect in SFDIPOTAspect:
            count = self.sfdipot_coverage.get(aspect.name, 0)
            bar = "█" * min(count, 20) + "░" * max(0, 20 - count)
            lines.append(f"  {aspect.value:12} [{bar}] {count}")

        lines.extend([
            "",
            "CRUCSS Coverage:",
            "-" * 40,
        ])

        for aspect in CRUCSSAspect:
            count = self.crucss_coverage.get(aspect.name, 0)
            bar = "█" * min(count, 20) + "░" * max(0, 20 - count)
            lines.append(f"  {aspect.value:12} [{bar}] {count}")

        total_sfdipot = sum(self.sfdipot_coverage.values())
        total_crucss = sum(self.crucss_coverage.values())

        lines.extend([
            "",
            "=" * 60,
            f"Total SFDIPOT tests: {total_sfdipot}",
            f"Total CRUCSS tests: {total_crucss}",
            f"Grand total: {total_sfdipot + total_crucss}",
            "=" * 60,
        ])

        return "\n".join(lines)

    def get_gaps(self) -> Dict[str, List[str]]:
        """Identify coverage gaps (aspects with 0 tests)."""
        gaps = {"SFDIPOT": [], "CRUCSS": []}

        for aspect in SFDIPOTAspect:
            if self.sfdipot_coverage.get(aspect.name, 0) == 0:
                gaps["SFDIPOT"].append(aspect.name)

        for aspect in CRUCSSAspect:
            if self.crucss_coverage.get(aspect.name, 0) == 0:
                gaps["CRUCSS"].append(aspect.name)

        return gaps

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "sfdipot": {
                "coverage": self.sfdipot_coverage,
                "tests": [
                    {
                        "aspect": t.aspect.name,
                        "description": t.description,
                        "api_level": t.api_level,
                        "ui_level": t.ui_level,
                        "entity": t.entity,
                    }
                    for t in self.sfdipot_tests
                ],
            },
            "crucss": {
                "coverage": self.crucss_coverage,
                "tests": [
                    {
                        "aspect": t.aspect.name,
                        "description": t.description,
                        "integration_level": t.integration_level,
                        "e2e_level": t.e2e_level,
                        "entity": t.entity,
                    }
                    for t in self.crucss_tests
                ],
            },
            "gaps": self.get_gaps(),
            "totals": {
                "sfdipot": sum(self.sfdipot_coverage.values()),
                "crucss": sum(self.crucss_coverage.values()),
            },
        }

    def save_json(self, path: str):
        """Save report as JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"[REPORT] Heuristic coverage saved to: {path}")


def pytest_configure(config):
    """Register heuristic marker with pytest."""
    config.addinivalue_line(
        "markers",
        "heuristic(name): mark test with exploratory heuristic (SFDIPOT.*, CRUCSS.*)"
    )


def pytest_collection_modifyitems(session, config, items):
    """Collect heuristic metadata from test items."""
    # This hook runs after test collection, can be used for reporting
    pass


if __name__ == "__main__":
    # Generate sample report
    report = HeuristicCoverageReport()
    report.collect()
    print(report.summary())
