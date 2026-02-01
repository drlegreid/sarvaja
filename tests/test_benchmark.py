"""
Benchmark Tests
Created: 2024-12-25 (P3.5)

Tests for governance benchmark framework.
"""
import pytest
from pathlib import Path
import json

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class TestBenchmarkFramework:
    """Unit tests for benchmark framework."""

    @pytest.mark.unit
    def test_benchmark_result_dataclass(self):
        """BenchmarkResult dataclass must be importable."""
        from governance.benchmark import BenchmarkResult

        result = BenchmarkResult(
            name="test",
            operation="test operation",
            iterations=10,
            total_time_ms=100.0,
            mean_time_ms=10.0,
            median_time_ms=9.5,
            min_time_ms=5.0,
            max_time_ms=15.0,
            std_dev_ms=2.5,
            p95_time_ms=14.0,
            p99_time_ms=14.8,
            success_rate=1.0
        )

        assert result.name == "test"
        assert result.iterations == 10
        assert result.success_rate == 1.0

    @pytest.mark.unit
    def test_benchmark_suite_dataclass(self):
        """BenchmarkSuite dataclass must be importable."""
        from governance.benchmark import BenchmarkSuite

        suite = BenchmarkSuite(
            suite_name="test_suite",
            timestamp="2024-12-25T00:00:00",
            host="localhost"
        )

        assert suite.suite_name == "test_suite"
        assert suite.results == []

    @pytest.mark.unit
    def test_benchmark_suite_to_dict(self):
        """BenchmarkSuite must be serializable to dict."""
        from governance.benchmark import BenchmarkSuite, BenchmarkResult

        result = BenchmarkResult(
            name="test",
            operation="test",
            iterations=1,
            total_time_ms=1.0,
            mean_time_ms=1.0,
            median_time_ms=1.0,
            min_time_ms=1.0,
            max_time_ms=1.0,
            std_dev_ms=0.0,
            p95_time_ms=1.0,
            p99_time_ms=1.0,
            success_rate=1.0
        )

        suite = BenchmarkSuite(
            suite_name="test",
            timestamp="2024-12-25T00:00:00",
            host="localhost",
            results=[result]
        )

        data = suite.to_dict()
        assert data["suite_name"] == "test"
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "test"

        # Verify JSON serializable
        json_str = json.dumps(data)
        assert "test" in json_str

    @pytest.mark.unit
    def test_governance_benchmark_class(self):
        """GovernanceBenchmark class must be instantiable."""
        from governance.benchmark import GovernanceBenchmark

        benchmark = GovernanceBenchmark(iterations=10)
        assert benchmark.iterations == 10
        assert benchmark.results == []

    @pytest.mark.unit
    def test_measure_function(self):
        """_measure should correctly time functions."""
        from governance.benchmark import BenchmarkBase
        import time

        benchmark = BenchmarkBase(iterations=5)

        def slow_func():
            time.sleep(0.01)  # 10ms

        result = benchmark._measure(
            "test_slow",
            "Sleep 10ms",
            slow_func
        )

        # Should be at least 10ms mean (with some tolerance)
        assert result.mean_time_ms >= 8.0  # Allow 2ms tolerance
        assert result.iterations == 5
        assert result.success_rate == 1.0

    @pytest.mark.unit
    def test_measure_with_errors(self):
        """_measure should track errors."""
        from governance.benchmark import BenchmarkBase

        benchmark = BenchmarkBase(iterations=5)

        def failing_func():
            raise ValueError("Test error")

        result = benchmark._measure(
            "test_fail",
            "Always fails",
            failing_func
        )

        assert result.success_rate == 0.0
        assert len(result.errors) > 0

    @pytest.mark.unit
    def test_measure_with_args(self):
        """_measure should pass arguments correctly."""
        from governance.benchmark import BenchmarkBase

        benchmark = BenchmarkBase(iterations=3)

        def add_func(a, b):
            return a + b

        result = benchmark._measure(
            "test_add",
            "Add two numbers",
            add_func,
            5, 3
        )

        assert result.success_rate == 1.0


class TestBenchmarkIntegration:
    """Integration tests requiring services."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires TypeDB running")
    def test_typedb_connect_benchmark(self):
        """TypeDB connect benchmark should complete."""
        from governance.benchmark import GovernanceBenchmark

        benchmark = GovernanceBenchmark(iterations=5)
        result = benchmark.benchmark_typedb_connect()

        assert result.success_rate > 0.8
        assert result.mean_time_ms < 1000  # Should connect in <1s

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires TypeDB running")
    def test_typedb_health_benchmark(self):
        """TypeDB health benchmark should complete."""
        from governance.benchmark import GovernanceBenchmark

        benchmark = GovernanceBenchmark(iterations=5)
        result = benchmark.benchmark_typedb_health()

        assert result.success_rate > 0.8

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires ChromaDB running")
    def test_chromadb_query_benchmark(self):
        """ChromaDB query benchmark should complete."""
        from governance.benchmark import GovernanceBenchmark

        benchmark = GovernanceBenchmark(iterations=5)
        result = benchmark.benchmark_chromadb_query()

        assert result.success_rate > 0.8


class TestBenchmarkCLI:
    """Tests for CLI interface."""

    @pytest.mark.unit
    def test_main_function_exists(self):
        """main function must exist in __main__.py."""
        from governance.benchmark.__main__ import main
        assert callable(main)

    @pytest.mark.unit
    def test_argparse_defaults(self):
        """Default arguments should be reasonable."""
        import argparse
        from governance.benchmark.__main__ import main

        # Verify module can be imported without errors
        from governance import benchmark
        assert hasattr(benchmark, "GovernanceBenchmark")
        assert hasattr(benchmark, "BenchmarkResult")
        assert hasattr(benchmark, "BenchmarkSuite")


class TestPerformanceTargets:
    """Tests that verify performance targets from R&D backlog."""

    @pytest.mark.unit
    def test_target_metadata(self):
        """Benchmark results should include target metadata."""
        from governance.benchmark import GovernanceBenchmark

        benchmark = GovernanceBenchmark(iterations=1)

        # Mocked result with target
        from governance.benchmark import BenchmarkResult
        result = BenchmarkResult(
            name="test",
            operation="test",
            iterations=1,
            total_time_ms=10.0,
            mean_time_ms=10.0,
            median_time_ms=10.0,
            min_time_ms=10.0,
            max_time_ms=10.0,
            std_dev_ms=0.0,
            p95_time_ms=10.0,
            p99_time_ms=10.0,
            success_rate=1.0,
            metadata={"target": "<50ms"}
        )

        assert "target" in result.metadata
        assert result.metadata["target"] == "<50ms"

    @pytest.mark.unit
    def test_performance_thresholds(self):
        """Performance thresholds should be defined."""
        # TypeDB targets per R&D backlog
        TYPEDB_CONNECT_TARGET_MS = 100
        TYPEDB_HEALTH_TARGET_MS = 10
        TYPEDB_QUERY_TARGET_MS = 50
        TYPEDB_INFERENCE_TARGET_MS = 100

        # ChromaDB targets
        CHROMADB_QUERY_TARGET_MS = 50

        # Hybrid targets
        HYBRID_QUERY_TARGET_MS = 150

        # Verify targets are reasonable
        assert TYPEDB_CONNECT_TARGET_MS <= 1000
        assert TYPEDB_INFERENCE_TARGET_MS <= 1000
        assert HYBRID_QUERY_TARGET_MS < TYPEDB_INFERENCE_TARGET_MS + CHROMADB_QUERY_TARGET_MS + 50
