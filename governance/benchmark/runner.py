"""
Benchmark Suite Runner
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Main runner that orchestrates all benchmark suites.
"""
import json
import statistics
from datetime import datetime
from typing import List

from governance.benchmark.models import BenchmarkResult, BenchmarkSuite
from governance.benchmark.typedb import TypeDBBenchmarks
from governance.benchmark.chromadb import ChromaDBBenchmarks
from governance.benchmark.hybrid import HybridBenchmarks


class GovernanceBenchmark:
    """
    Performance benchmark runner for governance operations.

    Example:
        benchmark = GovernanceBenchmark()
        benchmark.run_all()
        benchmark.export_results("benchmark_results.json")
    """

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

        # Initialize sub-benchmarks
        self._typedb = TypeDBBenchmarks(iterations)
        self._chromadb = ChromaDBBenchmarks(iterations)
        self._hybrid = HybridBenchmarks(iterations)

    def run_typedb_suite(self) -> List[BenchmarkResult]:
        """Run all TypeDB benchmarks."""
        return self._typedb.run_suite()

    def run_chromadb_suite(self) -> List[BenchmarkResult]:
        """Run all ChromaDB benchmarks."""
        return self._chromadb.run_suite()

    def run_hybrid_suite(self) -> List[BenchmarkResult]:
        """Run all hybrid benchmarks."""
        return self._hybrid.run_suite()

    def run_all(self) -> BenchmarkSuite:
        """Run all benchmark suites."""
        print("\nGovernance Performance Benchmarks")
        print(f"Iterations per test: {self.iterations}")
        print("=" * 50)

        all_results = []
        all_results.extend(self.run_typedb_suite())
        all_results.extend(self.run_chromadb_suite())
        all_results.extend(self.run_hybrid_suite())

        # Store results
        self.results = all_results

        # Calculate summary
        successful = [r for r in all_results if r.success_rate > 0.9]
        failed = [r for r in all_results if r.success_rate <= 0.9]

        suite = BenchmarkSuite(
            suite_name="governance_full",
            timestamp=datetime.now().isoformat(),
            host="localhost",
            results=all_results,
            summary={
                "total_benchmarks": len(all_results),
                "successful": len(successful),
                "failed": len(failed),
                "avg_mean_time_ms": statistics.mean([r.mean_time_ms for r in successful]) if successful else 0,
                "worst_p99_ms": max([r.p99_time_ms for r in successful]) if successful else 0,
            }
        )

        self._print_summary(suite)
        return suite

    def _print_summary(self, suite: BenchmarkSuite):
        """Print benchmark summary."""
        print("\n" + "=" * 50)
        print("BENCHMARK SUMMARY")
        print("=" * 50)
        print(f"Total benchmarks: {suite.summary['total_benchmarks']}")
        print(f"Successful: {suite.summary['successful']}")
        print(f"Failed: {suite.summary['failed']}")
        print(f"Avg mean time: {suite.summary['avg_mean_time_ms']:.2f}ms")
        print(f"Worst p99: {suite.summary['worst_p99_ms']:.2f}ms")

        # Performance targets
        print("\n--- Performance Targets ---")
        for result in suite.results:
            target = result.metadata.get("target", "N/A")
            status = "PASS" if result.success_rate > 0.9 else "FAIL"
            print(f"  {result.name}: {result.mean_time_ms:.2f}ms (target: {target}) [{status}]")

    def export_results(self, filepath: str):
        """Export results to JSON file."""
        suite = BenchmarkSuite(
            suite_name="governance_export",
            timestamp=datetime.now().isoformat(),
            host="localhost",
            results=self.results
        )

        with open(filepath, "w") as f:
            json.dump(suite.to_dict(), f, indent=2)

        print(f"Results exported to: {filepath}")
