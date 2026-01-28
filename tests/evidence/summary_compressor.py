"""
Test Summary Compressor - Compressed test results for LLM context efficiency.

Per EPIC-TEST-COMPRESS-001: Test results compression for reporting.

This module provides:
- Compressed summary format for batch test results
- Show-failures-only mode (success implied)
- Category grouping (unit/integration/e2e)
- Token estimation and compression ratios
- Compatible with pytest, Robot Framework, and MCP tools

Usage:
    compressor = SummaryCompressor()

    # From pytest results
    summary = compressor.compress_pytest_results(results)

    # From Robot Framework
    summary = compressor.compress_robot_results(output_xml)

    # Format for LLM context
    compact = compressor.format_compact(summary)

Created: 2026-01-25
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class CompressedTestSummary:
    """Compressed test run summary optimized for LLM context."""

    # Core stats (always shown)
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0

    # Duration
    duration_ms: float = 0.0
    duration_str: str = ""

    # Categories
    by_category: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Failures only (compressed - no need to list passing tests)
    failures: List[Dict[str, Any]] = field(default_factory=list)

    # Compression stats
    original_tokens: int = 0
    compressed_tokens: int = 0
    compression_ratio: str = "0%"

    # Metadata
    run_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stats": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "success_rate": f"{(self.passed / self.total * 100):.0f}%" if self.total > 0 else "0%",
            },
            "duration": self.duration_str or f"{self.duration_ms:.0f}ms",
            "by_category": self.by_category,
            "failures": self.failures,
            "compression": {
                "original_tokens": self.original_tokens,
                "compressed_tokens": self.compressed_tokens,
                "ratio": self.compression_ratio,
            },
        }

    def format_oneline(self) -> str:
        """One-line summary for progress reporting."""
        rate = f"{(self.passed / self.total * 100):.0f}%" if self.total > 0 else "0%"
        if self.failed == 0:
            return f"Tests: {self.passed}/{self.total} passed ({rate}) in {self.duration_str}"
        return f"Tests: {self.passed}/{self.total} passed, {self.failed} FAILED ({rate}) in {self.duration_str}"

    def format_compact(self) -> str:
        """Compact multi-line format for LLM context."""
        lines = []

        # Header line
        rate = f"{(self.passed / self.total * 100):.0f}%" if self.total > 0 else "0%"
        status = "PASS" if self.failed == 0 else "FAIL"
        lines.append(f"[{status}] {self.passed}/{self.total} ({rate}) | {self.duration_str}")

        # Category breakdown if multiple categories
        if len(self.by_category) > 1:
            cats = " | ".join(
                f"{cat}: {stats.get('passed', 0)}/{stats.get('total', 0)}"
                for cat, stats in self.by_category.items()
            )
            lines.append(f"  {cats}")

        # Failures (most important for debugging)
        if self.failures:
            lines.append(f"  Failures ({len(self.failures)}):")
            for f in self.failures[:5]:  # Show max 5
                name = f.get("name", f.get("test_id", "unknown"))
                error = f.get("error", "")[:80]  # Truncate error
                if error:
                    lines.append(f"    - {name}: {error}")
                else:
                    lines.append(f"    - {name}")
            if len(self.failures) > 5:
                lines.append(f"    ... and {len(self.failures) - 5} more")

        return "\n".join(lines)

    def format_toon(self) -> str:
        """TOON format (Text Output Optimized Notation)."""
        lines = []
        rate = f"{(self.passed / self.total * 100):.0f}%" if self.total > 0 else "0%"

        lines.append(f"tests[{self.total}]{{passed,failed,skipped,rate}}:")
        lines.append(f"  {self.passed},{self.failed},{self.skipped},{rate}")

        if self.by_category:
            cats = ",".join(self.by_category.keys())
            lines.append(f"categories[{len(self.by_category)}]: {cats}")

        if self.failures:
            lines.append(f"failures[{len(self.failures)}]{{name,error}}:")
            for f in self.failures[:5]:
                name = f.get("name", "?")[:30]
                error = f.get("error", "")[:50]
                lines.append(f"  {name},{error}")
            if len(self.failures) > 5:
                lines.append(f"  _truncated: {len(self.failures) - 5} more")

        lines.append(f"duration: {self.duration_str}")
        lines.append(f"compression: {self.compression_ratio}")

        return "\n".join(lines)


class SummaryCompressor:
    """
    Compresses test results for efficient LLM context usage.

    Design principles:
    - Success is implied (don't enumerate passing tests)
    - Failures are prioritized (most useful for debugging)
    - Category grouping reduces redundancy
    - Token estimation tracks savings
    """

    def __init__(self, max_failures: int = 10, max_error_length: int = 100):
        """Initialize compressor.

        Args:
            max_failures: Maximum number of failures to include
            max_error_length: Maximum error message length
        """
        self.max_failures = max_failures
        self.max_error_length = max_error_length

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (~4 chars per token for code)."""
        return len(text) // 4 if text else 0

    def format_duration(self, ms: float) -> str:
        """Format duration in human-readable form."""
        if ms < 1000:
            return f"{ms:.0f}ms"
        seconds = ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        remaining = seconds % 60
        return f"{minutes}m{remaining:.0f}s"

    def compress_test_list(
        self,
        tests: List[Dict[str, Any]],
        run_id: Optional[str] = None,
    ) -> CompressedTestSummary:
        """Compress a list of test results.

        Args:
            tests: List of test result dictionaries
            run_id: Optional run identifier

        Returns:
            CompressedTestSummary
        """
        # Estimate original size
        original_tokens = self.estimate_tokens(str(tests))

        # Calculate stats (normalize to lowercase for case-insensitive matching)
        total = len(tests)
        passed = sum(1 for t in tests if t.get("status", "").lower() in ("passed", "pass"))
        failed = sum(1 for t in tests if t.get("status", "").lower() in ("failed", "fail"))
        skipped = sum(1 for t in tests if t.get("status", "").lower() in ("skipped", "skip"))

        # Duration
        duration_ms = sum(t.get("duration_ms", 0) for t in tests)

        # Group by category
        by_category: Dict[str, Dict[str, int]] = {}
        for t in tests:
            cat = t.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            by_category[cat]["total"] += 1
            status = t.get("status", "").lower()
            if status in ("passed", "pass"):
                by_category[cat]["passed"] += 1
            elif status in ("failed", "fail"):
                by_category[cat]["failed"] += 1
            elif status in ("skipped", "skip"):
                by_category[cat]["skipped"] += 1

        # Extract failures (compressed)
        failures = []
        for t in tests:
            if t.get("status", "").lower() in ("failed", "fail"):
                failure = {
                    "test_id": t.get("test_id", t.get("nodeid", "")),
                    "name": t.get("name", t.get("test_id", "").split("::")[-1]),
                    "category": t.get("category", "unknown"),
                }
                # Truncate error message
                error = t.get("error_message", t.get("error", ""))
                if error:
                    failure["error"] = error[:self.max_error_length]
                    if len(error) > self.max_error_length:
                        failure["error"] += "..."
                # Include rules if available
                rules = t.get("linked_rules", [])
                if rules:
                    failure["rules"] = rules[:3]  # Max 3 rules
                failures.append(failure)

        # Limit failures
        if len(failures) > self.max_failures:
            failures = failures[:self.max_failures]

        # Build summary
        summary = CompressedTestSummary(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=duration_ms,
            duration_str=self.format_duration(duration_ms),
            by_category=by_category,
            failures=failures,
            run_id=run_id,
            original_tokens=original_tokens,
        )

        # Calculate compressed size
        summary.compressed_tokens = self.estimate_tokens(summary.format_compact())
        if original_tokens > 0:
            ratio = (1 - summary.compressed_tokens / original_tokens) * 100
            summary.compression_ratio = f"{ratio:.0f}%"

        return summary

    def compress_pytest_output(
        self,
        output: str,
        run_id: Optional[str] = None,
    ) -> CompressedTestSummary:
        """Compress pytest console output.

        Parses pytest output format:
        - "X passed" / "X failed" / "X skipped"
        - Duration line
        - Failure traceback (shortened)

        Args:
            output: Raw pytest output string
            run_id: Optional run identifier

        Returns:
            CompressedTestSummary
        """
        import re

        original_tokens = self.estimate_tokens(output)

        # Parse summary line: "=== X passed, Y failed in Z.ZZs ==="
        summary_match = re.search(
            r'(\d+)\s+passed.*?(\d+)\s+failed.*?(\d+)\s+skipped.*?in\s+([\d.]+)s',
            output,
            re.IGNORECASE
        )
        if not summary_match:
            # Try simpler pattern
            summary_match = re.search(
                r'(\d+)\s+passed.*?in\s+([\d.]+)s',
                output,
                re.IGNORECASE
            )

        passed = 0
        failed = 0
        skipped = 0
        duration_s = 0.0

        if summary_match:
            groups = summary_match.groups()
            if len(groups) >= 4:
                passed = int(groups[0])
                failed = int(groups[1])
                skipped = int(groups[2])
                duration_s = float(groups[3])
            elif len(groups) >= 2:
                passed = int(groups[0])
                duration_s = float(groups[1])

        # Parse failures
        failures = []
        failure_pattern = re.compile(
            r'FAILED\s+([\w/.:]+)\s*-\s*(.+?)(?=\n(?:FAILED|===|$))',
            re.DOTALL
        )
        for match in failure_pattern.finditer(output):
            test_id = match.group(1)
            error = match.group(2).strip()[:self.max_error_length]
            failures.append({
                "test_id": test_id,
                "name": test_id.split("::")[-1] if "::" in test_id else test_id,
                "error": error,
            })

        summary = CompressedTestSummary(
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=duration_s * 1000,
            duration_str=self.format_duration(duration_s * 1000),
            failures=failures[:self.max_failures],
            run_id=run_id,
            original_tokens=original_tokens,
        )

        summary.compressed_tokens = self.estimate_tokens(summary.format_compact())
        if original_tokens > 0:
            ratio = (1 - summary.compressed_tokens / original_tokens) * 100
            summary.compression_ratio = f"{ratio:.0f}%"

        return summary

    def compress_robot_output(
        self,
        output_xml_path: str,
        run_id: Optional[str] = None,
    ) -> CompressedTestSummary:
        """Compress Robot Framework output.xml.

        Args:
            output_xml_path: Path to output.xml
            run_id: Optional run identifier

        Returns:
            CompressedTestSummary
        """
        from pathlib import Path
        import xml.etree.ElementTree as ET

        path = Path(output_xml_path)
        if not path.exists():
            return CompressedTestSummary(run_id=run_id)

        original_tokens = self.estimate_tokens(path.read_text())

        tree = ET.parse(path)
        root = tree.getroot()

        # Get statistics
        statistics = root.find(".//statistics/total/stat[@name='All Tests']")
        passed = int(statistics.get("pass", 0)) if statistics is not None else 0
        failed = int(statistics.get("fail", 0)) if statistics is not None else 0

        # Get duration from robot tag
        robot = root.find(".")
        start_time = robot.get("generated", "")

        # Find failed tests
        failures = []
        for test in root.findall(".//test[@status='FAIL']"):
            name = test.get("name", "unknown")
            msg_elem = test.find(".//msg[@level='FAIL']")
            error = msg_elem.text[:self.max_error_length] if msg_elem is not None and msg_elem.text else ""
            failures.append({
                "test_id": test.get("id", name),
                "name": name,
                "error": error,
            })

        summary = CompressedTestSummary(
            total=passed + failed,
            passed=passed,
            failed=failed,
            failures=failures[:self.max_failures],
            run_id=run_id,
            original_tokens=original_tokens,
        )

        summary.compressed_tokens = self.estimate_tokens(summary.format_compact())
        if original_tokens > 0:
            ratio = (1 - summary.compressed_tokens / original_tokens) * 100
            summary.compression_ratio = f"{ratio:.0f}%"

        return summary


# Convenience functions

def compress_tests(tests: List[Dict[str, Any]]) -> str:
    """Quick compress test results to compact format."""
    compressor = SummaryCompressor()
    summary = compressor.compress_test_list(tests)
    return summary.format_compact()


def compress_pytest(output: str) -> str:
    """Quick compress pytest output."""
    compressor = SummaryCompressor()
    summary = compressor.compress_pytest_output(output)
    return summary.format_compact()


def oneline_summary(tests: List[Dict[str, Any]]) -> str:
    """Get one-line summary of test results."""
    compressor = SummaryCompressor()
    summary = compressor.compress_test_list(tests)
    return summary.format_oneline()
