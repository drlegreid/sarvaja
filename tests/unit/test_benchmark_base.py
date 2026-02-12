"""
Unit tests for Benchmark Base Class and Models.

Per DOC-SIZE-01-v1: Tests for governance/benchmark/base.py and models.py.
Tests: BenchmarkResult, BenchmarkSuite.to_dict, BenchmarkBase._measure,
       BenchmarkBase._create_error_result.
"""

from governance.benchmark.models import BenchmarkResult, BenchmarkSuite
from governance.benchmark.base import BenchmarkBase


# ── BenchmarkResult ────────────────────────────────────────


class TestBenchmarkResult:
    def test_defaults(self):
        r = BenchmarkResult(
            name="test", operation="op", iterations=10,
            total_time_ms=100.0, mean_time_ms=10.0, median_time_ms=9.5,
            min_time_ms=5.0, max_time_ms=20.0, std_dev_ms=3.0,
            p95_time_ms=18.0, p99_time_ms=19.5, success_rate=1.0,
        )
        assert r.errors == []
        assert r.metadata == {}

    def test_with_errors(self):
        r = BenchmarkResult(
            name="t", operation="o", iterations=1,
            total_time_ms=0, mean_time_ms=0, median_time_ms=0,
            min_time_ms=0, max_time_ms=0, std_dev_ms=0,
            p95_time_ms=0, p99_time_ms=0, success_rate=0,
            errors=["err1", "err2"],
        )
        assert r.errors == ["err1", "err2"]


# ── BenchmarkSuite ─────────────────────────────────────────


class TestBenchmarkSuite:
    def test_defaults(self):
        suite = BenchmarkSuite(suite_name="s", timestamp="2026-02-11", host="localhost")
        assert suite.results == []
        assert suite.summary == {}

    def test_to_dict(self):
        r = BenchmarkResult(
            name="test", operation="op", iterations=5,
            total_time_ms=50.0, mean_time_ms=10.0, median_time_ms=10.0,
            min_time_ms=8.0, max_time_ms=12.0, std_dev_ms=1.5,
            p95_time_ms=11.5, p99_time_ms=11.9, success_rate=1.0,
        )
        suite = BenchmarkSuite(
            suite_name="perf", timestamp="2026-02-11T10:00:00",
            host="test-host", results=[r], summary={"total": 1},
        )
        d = suite.to_dict()
        assert d["suite_name"] == "perf"
        assert d["host"] == "test-host"
        assert len(d["results"]) == 1
        assert d["results"][0]["name"] == "test"
        assert d["summary"] == {"total": 1}


# ── BenchmarkBase._measure ─────────────────────────────────


class TestMeasure:
    def test_successful_function(self):
        bench = BenchmarkBase(iterations=5)
        counter = {"n": 0}

        def increment():
            counter["n"] += 1

        result = bench._measure("test", "increment", increment)
        assert counter["n"] == 5
        assert result.name == "test"
        assert result.operation == "increment"
        assert result.iterations == 5
        assert result.success_rate == 1.0
        assert result.total_time_ms > 0
        assert result.mean_time_ms > 0
        assert result.errors == []

    def test_failing_function(self):
        bench = BenchmarkBase(iterations=3)

        def fail():
            raise ValueError("oops")

        result = bench._measure("fail_test", "fail", fail)
        assert result.success_rate == 0.0
        assert len(result.errors) == 3
        assert "oops" in result.errors[0]

    def test_partial_failures(self):
        bench = BenchmarkBase(iterations=4)
        call_count = {"n": 0}

        def sometimes_fail():
            call_count["n"] += 1
            if call_count["n"] % 2 == 0:
                raise RuntimeError("even fail")

        result = bench._measure("partial", "op", sometimes_fail)
        assert result.success_rate == 0.5
        assert len(result.errors) == 2

    def test_with_args(self):
        bench = BenchmarkBase(iterations=2)
        results_list = []

        def add(a, b):
            results_list.append(a + b)

        result = bench._measure("add_test", "add", add, 3, 4)
        assert results_list == [7, 7]
        assert result.success_rate == 1.0

    def test_with_kwargs(self):
        bench = BenchmarkBase(iterations=1)
        captured = {}

        def func(x=0, y=0):
            captured["sum"] = x + y

        bench._measure("kw", "op", func, x=10, y=20)
        assert captured["sum"] == 30

    def test_statistics(self):
        bench = BenchmarkBase(iterations=10)

        def noop():
            pass

        result = bench._measure("stats", "op", noop)
        assert result.min_time_ms <= result.mean_time_ms
        assert result.mean_time_ms <= result.max_time_ms
        assert result.min_time_ms <= result.median_time_ms
        assert result.p95_time_ms <= result.max_time_ms
        assert result.p99_time_ms <= result.max_time_ms

    def test_errors_capped_at_5(self):
        bench = BenchmarkBase(iterations=10)

        def fail():
            raise Exception("err")

        result = bench._measure("capped", "op", fail)
        assert len(result.errors) == 5  # first 5 only


# ── BenchmarkBase._create_error_result ─────────────────────


class TestCreateErrorResult:
    def test_returns_zero_result(self):
        bench = BenchmarkBase()
        result = bench._create_error_result("err_test", "setup", "Connection failed")
        assert result.name == "err_test"
        assert result.operation == "setup"
        assert result.iterations == 0
        assert result.total_time_ms == 0
        assert result.success_rate == 0
        assert result.errors == ["Connection failed"]

    def test_all_times_zero(self):
        bench = BenchmarkBase()
        result = bench._create_error_result("t", "o", "err")
        assert result.mean_time_ms == 0
        assert result.median_time_ms == 0
        assert result.min_time_ms == 0
        assert result.max_time_ms == 0
        assert result.std_dev_ms == 0
        assert result.p95_time_ms == 0
        assert result.p99_time_ms == 0


# ── BenchmarkBase init ─────────────────────────────────────


class TestBenchmarkBaseInit:
    def test_default_iterations(self):
        bench = BenchmarkBase()
        assert bench.iterations == 100
        assert bench.results == []

    def test_custom_iterations(self):
        bench = BenchmarkBase(iterations=50)
        assert bench.iterations == 50
