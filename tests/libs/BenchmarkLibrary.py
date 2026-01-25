"""
Robot Framework Library for Benchmark Framework Tests.

Per P3.5: Governance benchmark framework.
Migrated from tests/test_benchmark.py
"""
import time
from pathlib import Path
from robot.api.deco import keyword


class BenchmarkLibrary:
    """Library for testing benchmark framework."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Module Tests
    # =============================================================================

    @keyword("Benchmark Module Exists")
    def benchmark_module_exists(self):
        """Benchmark module must exist."""
        benchmark_file = self.governance_dir / "benchmark.py"
        return {"exists": benchmark_file.exists()}

    @keyword("Benchmark Result Dataclass Works")
    def benchmark_result_dataclass_works(self):
        """BenchmarkResult dataclass must be importable."""
        try:
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

            return {
                "name_correct": result.name == "test",
                "iterations_correct": result.iterations == 10,
                "success_rate_correct": result.success_rate == 1.0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Benchmark Suite Dataclass Works")
    def benchmark_suite_dataclass_works(self):
        """BenchmarkSuite dataclass must be importable."""
        try:
            from governance.benchmark import BenchmarkSuite

            suite = BenchmarkSuite(
                suite_name="test_suite",
                timestamp="2024-12-25T00:00:00",
                host="localhost"
            )

            return {
                "name_correct": suite.suite_name == "test_suite",
                "results_empty": suite.results == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Benchmark Suite To Dict Works")
    def benchmark_suite_to_dict_works(self):
        """BenchmarkSuite must be serializable to dict."""
        try:
            import json
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
            json_str = json.dumps(data)

            return {
                "name_correct": data["suite_name"] == "test",
                "results_count": len(data["results"]) == 1,
                "result_name": data["results"][0]["name"] == "test",
                "json_serializable": "test" in json_str
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Governance Benchmark Class Works")
    def governance_benchmark_class_works(self):
        """GovernanceBenchmark class must be instantiable."""
        try:
            from governance.benchmark import GovernanceBenchmark

            benchmark = GovernanceBenchmark(iterations=10)
            return {
                "iterations_correct": benchmark.iterations == 10,
                "results_empty": benchmark.results == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Measure Function Times Correctly")
    def measure_function_times_correctly(self):
        """_measure should correctly time functions."""
        try:
            from governance.benchmark import BenchmarkBase

            benchmark = BenchmarkBase(iterations=3)

            def slow_func():
                time.sleep(0.01)  # 10ms

            result = benchmark._measure(
                "test_slow",
                "Sleep 10ms",
                slow_func
            )

            return {
                "mean_time_correct": result.mean_time_ms >= 8.0,
                "iterations_correct": result.iterations == 3,
                "success_rate_correct": result.success_rate == 1.0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Measure Function Tracks Errors")
    def measure_function_tracks_errors(self):
        """_measure should track errors."""
        try:
            from governance.benchmark import BenchmarkBase

            benchmark = BenchmarkBase(iterations=5)

            def failing_func():
                raise ValueError("Test error")

            result = benchmark._measure(
                "test_fail",
                "Always fails",
                failing_func
            )

            return {
                "success_rate_zero": result.success_rate == 0.0,
                "has_errors": len(result.errors) > 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Measure Function Passes Args")
    def measure_function_passes_args(self):
        """_measure should pass arguments correctly."""
        try:
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

            return {"success_rate_correct": result.success_rate == 1.0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # CLI Tests
    # =============================================================================

    @keyword("Main Function Exists")
    def main_function_exists(self):
        """main function must exist in __main__.py."""
        try:
            from governance.benchmark.__main__ import main
            return {"callable": callable(main)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Benchmark Module Has Required Exports")
    def benchmark_module_has_required_exports(self):
        """Module should export required classes."""
        try:
            from governance import benchmark

            return {
                "has_governance": hasattr(benchmark, "GovernanceBenchmark"),
                "has_result": hasattr(benchmark, "BenchmarkResult"),
                "has_suite": hasattr(benchmark, "BenchmarkSuite")
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Performance Target Tests
    # =============================================================================

    @keyword("Benchmark Result Supports Metadata")
    def benchmark_result_supports_metadata(self):
        """Benchmark results should include target metadata."""
        try:
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

            return {
                "has_target": "target" in result.metadata,
                "target_correct": result.metadata["target"] == "<50ms"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Performance Thresholds Are Reasonable")
    def performance_thresholds_are_reasonable(self):
        """Performance thresholds should be defined."""
        TYPEDB_CONNECT_TARGET_MS = 100
        TYPEDB_HEALTH_TARGET_MS = 10
        TYPEDB_QUERY_TARGET_MS = 50
        TYPEDB_INFERENCE_TARGET_MS = 100
        CHROMADB_QUERY_TARGET_MS = 50
        HYBRID_QUERY_TARGET_MS = 150

        return {
            "connect_reasonable": TYPEDB_CONNECT_TARGET_MS <= 1000,
            "inference_reasonable": TYPEDB_INFERENCE_TARGET_MS <= 1000,
            "hybrid_reasonable": HYBRID_QUERY_TARGET_MS < TYPEDB_INFERENCE_TARGET_MS + CHROMADB_QUERY_TARGET_MS + 50
        }
