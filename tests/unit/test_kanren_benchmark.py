"""
Unit tests for Kanren Performance Benchmarks.

Per DOC-SIZE-01-v1: Tests for kanren/benchmark.py module.
Tests: BenchmarkResult, benchmark decorator, direct_ functions, run_all_benchmarks.
"""

import pytest
pytest.importorskip("kanren")  # BUG-014: skip if kanren not installed

from governance.kanren.benchmark import (
    BenchmarkResult,
    benchmark,
    direct_trust_level,
    direct_requires_supervisor,
    direct_can_execute,
    direct_task_requires_evidence,
    run_all_benchmarks,
)


class TestBenchmarkResult:
    def test_summary_pass(self):
        r = BenchmarkResult("test", 100, 10.0, 0.1, 0.05, 0.2, 1.0, True)
        s = r.summary()
        assert "PASS" in s
        assert "test" in s

    def test_summary_fail(self):
        r = BenchmarkResult("test", 100, 200.0, 2.0, 1.5, 3.0, 1.0, False)
        s = r.summary()
        assert "FAIL" in s


class TestBenchmarkDecorator:
    def test_returns_result(self):
        @benchmark(iterations=10, target_ms=1000.0)
        def quick_func():
            pass

        result = quick_func()
        assert isinstance(result, BenchmarkResult)
        assert result.iterations == 10
        assert result.name == "quick_func"
        assert result.passed is True  # trivial func should be well under 1s

    def test_preserves_name(self):
        @benchmark(iterations=5)
        def my_named_func():
            pass

        assert my_named_func.__name__ == "my_named_func"


class TestDirectFunctions:
    def test_trust_level(self):
        assert direct_trust_level(0.95) == "expert"
        assert direct_trust_level(0.85) == "trusted"
        assert direct_trust_level(0.6) == "supervised"
        assert direct_trust_level(0.3) == "restricted"

    def test_requires_supervisor(self):
        assert direct_requires_supervisor("restricted") is True
        assert direct_requires_supervisor("supervised") is True
        assert direct_requires_supervisor("trusted") is False
        assert direct_requires_supervisor("expert") is False

    def test_can_execute(self):
        assert direct_can_execute("expert", "CRITICAL") is True
        assert direct_can_execute("trusted", "CRITICAL") is True
        assert direct_can_execute("supervised", "CRITICAL") is False
        assert direct_can_execute("restricted", "HIGH") is False
        assert direct_can_execute("restricted", "MEDIUM") is True

    def test_requires_evidence(self):
        assert direct_task_requires_evidence("CRITICAL") is True
        assert direct_task_requires_evidence("HIGH") is True
        assert direct_task_requires_evidence("MEDIUM") is False
        assert direct_task_requires_evidence("LOW") is False


class TestRunAllBenchmarks:
    def test_returns_results(self):
        results = run_all_benchmarks()
        assert len(results) == 11
        assert all(isinstance(r, BenchmarkResult) for r in results)
