"""
RF-004: Robot Framework Library for Summary Compressor.

Wraps tests/evidence/summary_compressor.py for Robot Framework tests.
Per EPIC-TEST-COMPRESS-001: Test results compression.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SummaryCompressorLibrary:
    """Robot Framework library for Summary Compressor testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # CompressedTestSummary Tests
    # =========================================================================

    def format_oneline_all_passed(self) -> Dict[str, Any]:
        """One-line format shows pass rate when all pass."""
        from tests.evidence.summary_compressor import CompressedTestSummary

        summary = CompressedTestSummary(
            total=100,
            passed=100,
            failed=0,
            skipped=0,
            duration_str="5.2s"
        )
        result = summary.format_oneline()
        return {
            "has_count": "100/100" in result,
            "has_percent": "100%" in result,
            "has_duration": "5.2s" in result,
            "no_failed": "FAILED" not in result
        }

    def format_oneline_with_failures(self) -> Dict[str, Any]:
        """One-line format highlights failures."""
        from tests.evidence.summary_compressor import CompressedTestSummary

        summary = CompressedTestSummary(
            total=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_str="5.2s"
        )
        result = summary.format_oneline()
        return {
            "has_count": "95/100" in result,
            "has_failed": "5 FAILED" in result
        }

    def format_compact_shows_failures(self) -> Dict[str, Any]:
        """Compact format includes failure details."""
        from tests.evidence.summary_compressor import CompressedTestSummary

        summary = CompressedTestSummary(
            total=10,
            passed=8,
            failed=2,
            failures=[
                {"name": "test_one", "error": "AssertionError"},
                {"name": "test_two", "error": "TypeError"},
            ],
            duration_str="1.0s"
        )
        result = summary.format_compact()
        return {
            "has_fail_marker": "[FAIL]" in result,
            "has_test_one": "test_one" in result,
            "has_test_two": "test_two" in result,
            "has_assertion_error": "AssertionError" in result
        }

    def format_compact_truncates_failures(self) -> Dict[str, Any]:
        """Compact format truncates to 5 failures."""
        from tests.evidence.summary_compressor import CompressedTestSummary

        failures = [{"name": f"test_{i}", "error": "Error"} for i in range(10)]
        summary = CompressedTestSummary(
            total=10,
            passed=0,
            failed=10,
            failures=failures,
            duration_str="1.0s"
        )
        result = summary.format_compact()
        return {
            "has_test_0": "test_0" in result,
            "has_test_4": "test_4" in result,
            "has_more": "5 more" in result
        }

    def format_toon(self) -> Dict[str, Any]:
        """TOON format is machine-readable."""
        from tests.evidence.summary_compressor import CompressedTestSummary

        summary = CompressedTestSummary(
            total=50,
            passed=48,
            failed=2,
            skipped=0,
            by_category={"unit": {"total": 50, "passed": 48}},
            duration_str="2.0s",
            compression_ratio="75%"
        )
        result = summary.format_toon()
        return {
            "has_tests": "tests[50]" in result,
            "has_stats": "48,2,0" in result,
            "has_duration": "duration: 2.0s" in result,
            "has_compression": "compression: 75%" in result
        }

    def to_dict(self) -> Dict[str, Any]:
        """to_dict includes all fields."""
        from tests.evidence.summary_compressor import CompressedTestSummary

        summary = CompressedTestSummary(
            total=10,
            passed=9,
            failed=1,
            duration_str="1s"
        )
        d = summary.to_dict()
        return {
            "total": d["stats"]["total"],
            "passed": d["stats"]["passed"],
            "success_rate": d["stats"]["success_rate"]
        }

    # =========================================================================
    # SummaryCompressor Tests
    # =========================================================================

    def estimate_tokens(self) -> Dict[str, Any]:
        """Token estimation is approximately 4 chars per token."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        return {
            "100_chars": compressor.estimate_tokens("a" * 100),
            "empty": compressor.estimate_tokens("")
        }

    def format_duration_milliseconds(self) -> Dict[str, Any]:
        """Duration formatting for ms."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        return {
            "500ms": compressor.format_duration(500),
            "50ms": compressor.format_duration(50)
        }

    def format_duration_seconds(self) -> Dict[str, Any]:
        """Duration formatting for seconds."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        return {
            "5000ms": compressor.format_duration(5000),
            "30500ms": compressor.format_duration(30500)
        }

    def format_duration_minutes(self) -> Dict[str, Any]:
        """Duration formatting for minutes."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        return {
            "90000ms": compressor.format_duration(90000),
            "150000ms": compressor.format_duration(150000)
        }

    def compress_test_list_basic(self) -> Dict[str, Any]:
        """Basic test list compression."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        tests = [
            {"test_id": "test_1", "name": "test_1", "status": "passed", "category": "unit"},
            {"test_id": "test_2", "name": "test_2", "status": "passed", "category": "unit"},
            {"test_id": "test_3", "name": "test_3", "status": "failed", "category": "unit", "error": "AssertionError"},
        ]
        summary = compressor.compress_test_list(tests)
        return {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "failure_count": len(summary.failures),
            "failure_error": summary.failures[0]["error"] if summary.failures else None
        }

    def compress_test_list_categories(self) -> Dict[str, Any]:
        """Test list compression groups by category."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        tests = [
            {"test_id": "t1", "status": "passed", "category": "unit"},
            {"test_id": "t2", "status": "passed", "category": "unit"},
            {"test_id": "t3", "status": "passed", "category": "e2e"},
            {"test_id": "t4", "status": "failed", "category": "e2e", "error": "Err"},
        ]
        summary = compressor.compress_test_list(tests)
        return {
            "has_unit": "unit" in summary.by_category,
            "has_e2e": "e2e" in summary.by_category,
            "unit_passed": summary.by_category.get("unit", {}).get("passed", 0),
            "e2e_failed": summary.by_category.get("e2e", {}).get("failed", 0)
        }

    def compress_test_list_truncates_errors(self) -> Dict[str, Any]:
        """Long error messages are truncated."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor(max_error_length=20)
        tests = [
            {"test_id": "t1", "status": "failed", "error": "A" * 100, "category": "unit"},
        ]
        summary = compressor.compress_test_list(tests)
        return {
            "error_truncated": len(summary.failures[0]["error"]) <= 23
        }

    def compress_test_list_limits_failures(self) -> Dict[str, Any]:
        """Number of failures is limited."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor(max_failures=3)
        tests = [
            {"test_id": f"t{i}", "status": "failed", "error": f"Err{i}", "category": "unit"}
            for i in range(10)
        ]
        summary = compressor.compress_test_list(tests)
        return {
            "failure_count": len(summary.failures)
        }

    def compress_calculates_compression_ratio(self) -> Dict[str, Any]:
        """Compression ratio is calculated."""
        from tests.evidence.summary_compressor import SummaryCompressor

        compressor = SummaryCompressor()
        tests = [
            {"test_id": f"test_{i}", "status": "passed", "category": "unit", "duration_ms": 100}
            for i in range(100)
        ]
        summary = compressor.compress_test_list(tests)
        return {
            "has_original_tokens": summary.original_tokens > 0,
            "has_compressed_tokens": summary.compressed_tokens > 0,
            "has_percent": "%" in summary.compression_ratio
        }

    # =========================================================================
    # Convenience Functions Tests
    # =========================================================================

    def compress_tests_function(self) -> Dict[str, Any]:
        """compress_tests returns compact format."""
        from tests.evidence.summary_compressor import compress_tests

        tests = [
            {"test_id": "t1", "status": "passed", "category": "unit"},
            {"test_id": "t2", "status": "failed", "category": "unit", "error": "Err"},
        ]
        result = compress_tests(tests)
        return {
            "has_fail": "[FAIL]" in result,
            "has_count": "1/2" in result
        }

    def oneline_summary_function(self) -> Dict[str, Any]:
        """oneline_summary returns single line."""
        from tests.evidence.summary_compressor import oneline_summary

        tests = [
            {"test_id": "t1", "status": "passed", "category": "unit"},
        ]
        result = oneline_summary(tests)
        return {
            "no_newline": "\n" not in result,
            "has_count": "1/1" in result
        }
