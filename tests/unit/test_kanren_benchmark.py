"""
Unit tests for Kanren Performance Benchmarks.

Per DOC-SIZE-01-v1: Tests for kanren/benchmark.py module.
Tests: BenchmarkResult, benchmark decorator, direct functions, run_all_benchmarks.
"""

import pytest

from governance.kanren.benchmark import (
    BenchmarkResult,
    benchmark,
    direct_trust_level,
    direct_requires_supervisor,
    direct_can_execute,
    direct_task_requires_evidence,
    run_all_benchmarks,
    bench_trust_level,
)


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_basic(self):
        br = BenchmarkResult(
            name="test", iterations=100, total_ms=50.0,
            avg_ms=0.5, min_ms=0.1, max_ms=2.0,
            target_ms=1.0, passed=True,
        )
        assert br.name == "test"
        assert br.passed is True

    def test_summary_pass(self):
        br = BenchmarkResult(
            name="test", iterations=100, total_ms=50.0,
            avg_ms=0.5, min_ms=0.1, max_ms=2.0,
            target_ms=1.0, passed=True,
        )
        summary = br.summary()
        assert "PASS" in summary
        assert "test" in summary

    def test_summary_fail(self):
        br = BenchmarkResult(
            name="slow", iterations=10, total_ms=200.0,
            avg_ms=20.0, min_ms=10.0, max_ms=30.0,
            target_ms=1.0, passed=False,
        )
        summary = br.summary()
        assert "FAIL" in summary


class TestBenchmarkDecorator:
    """Tests for benchmark() decorator."""

    def test_returns_result(self):
        @benchmark(iterations=10, target_ms=100.0)
        def fast_func():
            return 1 + 1

        result = fast_func()
        assert isinstance(result, BenchmarkResult)
        assert result.iterations == 10
        assert result.avg_ms >= 0

    def test_passes_target(self):
        @benchmark(iterations=5, target_ms=1000.0)
        def trivial():
            pass

        result = trivial()
        assert result.passed is True


class TestDirectFunctions:
    """Tests for direct Python equivalents (no Kanren)."""

    def test_direct_trust_level(self):
        assert direct_trust_level(0.95) == "expert"
        assert direct_trust_level(0.8) == "trusted"
        assert direct_trust_level(0.6) == "supervised"
        assert direct_trust_level(0.3) == "restricted"

    def test_direct_requires_supervisor(self):
        assert direct_requires_supervisor("restricted") is True
        assert direct_requires_supervisor("supervised") is True
        assert direct_requires_supervisor("trusted") is False
        assert direct_requires_supervisor("expert") is False

    def test_direct_can_execute(self):
        assert direct_can_execute("expert", "CRITICAL") is True
        assert direct_can_execute("trusted", "CRITICAL") is True
        assert direct_can_execute("supervised", "CRITICAL") is False
        assert direct_can_execute("restricted", "HIGH") is False
        assert direct_can_execute("restricted", "MEDIUM") is True

    def test_direct_task_requires_evidence(self):
        assert direct_task_requires_evidence("CRITICAL") is True
        assert direct_task_requires_evidence("HIGH") is True
        assert direct_task_requires_evidence("MEDIUM") is False
        assert direct_task_requires_evidence("LOW") is False


class TestBenchFunctions:
    """Tests for pre-defined benchmark functions."""

    def test_bench_trust_level_runs(self):
        result = bench_trust_level()
        assert isinstance(result, BenchmarkResult)
        assert result.name == "bench_trust_level"

    def test_run_all_benchmarks(self):
        results = run_all_benchmarks()
        assert len(results) == 11  # 7 kanren + 4 direct
        assert all(isinstance(r, BenchmarkResult) for r in results)
