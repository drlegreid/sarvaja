"""
Unit tests for SummaryCompressor.

Per EPIC-TEST-COMPRESS-001: Test results compression.
"""

import pytest
from tests.evidence.summary_compressor import (
    SummaryCompressor,
    CompressedTestSummary,
    compress_tests,
    compress_pytest,
    oneline_summary,
)


class TestCompressedTestSummary:
    """Tests for CompressedTestSummary dataclass."""

    def test_format_oneline_all_passed(self):
        """One-line format shows pass rate when all pass."""
        summary = CompressedTestSummary(
            total=100,
            passed=100,
            failed=0,
            skipped=0,
            duration_str="5.2s"
        )
        result = summary.format_oneline()
        assert "100/100" in result
        assert "100%" in result
        assert "5.2s" in result
        assert "FAILED" not in result

    def test_format_oneline_with_failures(self):
        """One-line format highlights failures."""
        summary = CompressedTestSummary(
            total=100,
            passed=95,
            failed=5,
            skipped=0,
            duration_str="5.2s"
        )
        result = summary.format_oneline()
        assert "95/100" in result
        assert "5 FAILED" in result

    def test_format_compact_shows_failures(self):
        """Compact format includes failure details."""
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
        assert "[FAIL]" in result
        assert "test_one" in result
        assert "test_two" in result
        assert "AssertionError" in result

    def test_format_compact_truncates_failures(self):
        """Compact format truncates to 5 failures."""
        failures = [{"name": f"test_{i}", "error": "Error"} for i in range(10)]
        summary = CompressedTestSummary(
            total=10,
            passed=0,
            failed=10,
            failures=failures,
            duration_str="1.0s"
        )
        result = summary.format_compact()
        assert "test_0" in result
        assert "test_4" in result
        assert "5 more" in result

    def test_format_toon(self):
        """TOON format is machine-readable."""
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
        assert "tests[50]" in result
        assert "48,2,0" in result
        assert "duration: 2.0s" in result
        assert "compression: 75%" in result

    def test_to_dict(self):
        """to_dict includes all fields."""
        summary = CompressedTestSummary(
            total=10,
            passed=9,
            failed=1,
            duration_str="1s"
        )
        d = summary.to_dict()
        assert d["stats"]["total"] == 10
        assert d["stats"]["passed"] == 9
        assert d["stats"]["success_rate"] == "90%"


class TestSummaryCompressor:
    """Tests for SummaryCompressor class."""

    def test_estimate_tokens(self):
        """Token estimation is approximately 4 chars per token."""
        compressor = SummaryCompressor()
        assert compressor.estimate_tokens("a" * 100) == 25
        assert compressor.estimate_tokens("") == 0

    def test_format_duration_milliseconds(self):
        """Duration formatting for ms."""
        compressor = SummaryCompressor()
        assert compressor.format_duration(500) == "500ms"
        assert compressor.format_duration(50) == "50ms"

    def test_format_duration_seconds(self):
        """Duration formatting for seconds."""
        compressor = SummaryCompressor()
        assert compressor.format_duration(5000) == "5.0s"
        assert compressor.format_duration(30500) == "30.5s"

    def test_format_duration_minutes(self):
        """Duration formatting for minutes."""
        compressor = SummaryCompressor()
        assert compressor.format_duration(90000) == "1m30s"
        assert compressor.format_duration(150000) == "2m30s"

    def test_compress_test_list_basic(self):
        """Basic test list compression."""
        compressor = SummaryCompressor()
        tests = [
            {"test_id": "test_1", "name": "test_1", "status": "passed", "category": "unit"},
            {"test_id": "test_2", "name": "test_2", "status": "passed", "category": "unit"},
            {"test_id": "test_3", "name": "test_3", "status": "failed", "category": "unit", "error": "AssertionError"},
        ]
        summary = compressor.compress_test_list(tests)
        assert summary.total == 3
        assert summary.passed == 2
        assert summary.failed == 1
        assert len(summary.failures) == 1
        assert summary.failures[0]["error"] == "AssertionError"

    def test_compress_test_list_categories(self):
        """Test list compression groups by category."""
        compressor = SummaryCompressor()
        tests = [
            {"test_id": "t1", "status": "passed", "category": "unit"},
            {"test_id": "t2", "status": "passed", "category": "unit"},
            {"test_id": "t3", "status": "passed", "category": "e2e"},
            {"test_id": "t4", "status": "failed", "category": "e2e", "error": "Err"},
        ]
        summary = compressor.compress_test_list(tests)
        assert "unit" in summary.by_category
        assert "e2e" in summary.by_category
        assert summary.by_category["unit"]["passed"] == 2
        assert summary.by_category["e2e"]["failed"] == 1

    def test_compress_test_list_truncates_errors(self):
        """Long error messages are truncated."""
        compressor = SummaryCompressor(max_error_length=20)
        tests = [
            {"test_id": "t1", "status": "failed", "error": "A" * 100, "category": "unit"},
        ]
        summary = compressor.compress_test_list(tests)
        assert len(summary.failures[0]["error"]) <= 23  # 20 + "..."

    def test_compress_test_list_limits_failures(self):
        """Number of failures is limited."""
        compressor = SummaryCompressor(max_failures=3)
        tests = [
            {"test_id": f"t{i}", "status": "failed", "error": f"Err{i}", "category": "unit"}
            for i in range(10)
        ]
        summary = compressor.compress_test_list(tests)
        assert len(summary.failures) == 3

    def test_compress_calculates_compression_ratio(self):
        """Compression ratio is calculated."""
        compressor = SummaryCompressor()
        tests = [
            {"test_id": f"test_{i}", "status": "passed", "category": "unit", "duration_ms": 100}
            for i in range(100)
        ]
        summary = compressor.compress_test_list(tests)
        assert summary.original_tokens > 0
        assert summary.compressed_tokens > 0
        assert "%" in summary.compression_ratio

    def test_compress_pytest_output(self):
        """Pytest output parsing."""
        compressor = SummaryCompressor()
        output = """
============================= test session starts ==============================
collected 50 items

tests/test_example.py ............................................... [ 94%]
tests/test_more.py ...                                                  [100%]

============================== 50 passed in 2.34s ==============================
"""
        summary = compressor.compress_pytest_output(output)
        assert summary.passed == 50
        assert summary.total == 50
        assert summary.duration_ms == pytest.approx(2340, rel=0.01)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_compress_tests(self):
        """compress_tests returns compact format."""
        tests = [
            {"test_id": "t1", "status": "passed", "category": "unit"},
            {"test_id": "t2", "status": "failed", "category": "unit", "error": "Err"},
        ]
        result = compress_tests(tests)
        assert "[FAIL]" in result
        assert "1/2" in result

    def test_oneline_summary(self):
        """oneline_summary returns single line."""
        tests = [
            {"test_id": "t1", "status": "passed", "category": "unit"},
        ]
        result = oneline_summary(tests)
        assert "\n" not in result
        assert "1/1" in result
