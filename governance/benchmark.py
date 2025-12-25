"""
Governance Performance Benchmarks
Created: 2024-12-25 (P3.5)

PURPOSE:
Measure and track performance of governance operations:
- TypeDB queries (rules, dependencies, inference)
- ChromaDB queries (semantic search)
- Hybrid queries (combined routing)
- MCP tool invocations

USAGE:
    python -m governance.benchmark [--iterations 100] [--output json]

Per RULE-010: Evidence-Based Wisdom - measure before optimize.
"""
import time
import statistics
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    name: str
    operation: str
    iterations: int
    total_time_ms: float
    mean_time_ms: float
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    p95_time_ms: float
    p99_time_ms: float
    success_rate: float
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    suite_name: str
    timestamp: str
    host: str
    results: List[BenchmarkResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "suite_name": self.suite_name,
            "timestamp": self.timestamp,
            "host": self.host,
            "results": [asdict(r) for r in self.results],
            "summary": self.summary
        }


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
        self._typedb_client = None
        self._chromadb_client = None

    def _measure(
        self,
        name: str,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Execute and measure a function."""
        times: List[float] = []
        errors: List[str] = []
        successes = 0

        for i in range(self.iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
                successes += 1
            except Exception as e:
                errors.append(f"Iteration {i}: {str(e)}")
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        # Calculate statistics
        times_sorted = sorted(times)
        p95_idx = int(len(times_sorted) * 0.95)
        p99_idx = int(len(times_sorted) * 0.99)

        return BenchmarkResult(
            name=name,
            operation=operation,
            iterations=self.iterations,
            total_time_ms=sum(times),
            mean_time_ms=statistics.mean(times) if times else 0,
            median_time_ms=statistics.median(times) if times else 0,
            min_time_ms=min(times) if times else 0,
            max_time_ms=max(times) if times else 0,
            std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
            p95_time_ms=times_sorted[p95_idx] if times else 0,
            p99_time_ms=times_sorted[p99_idx] if times else 0,
            success_rate=successes / self.iterations if self.iterations > 0 else 0,
            errors=errors[:5]  # Keep first 5 errors
        )

    # =========================================================================
    # TypeDB Benchmarks
    # =========================================================================

    def benchmark_typedb_connect(self) -> BenchmarkResult:
        """Benchmark TypeDB connection."""
        from governance.client import TypeDBClient

        def connect_and_close():
            client = TypeDBClient()
            client.connect()
            client.close()

        result = self._measure(
            "typedb_connect",
            "Connect + close TypeDB",
            connect_and_close
        )
        result.metadata["target"] = "<100ms"
        return result

    def benchmark_typedb_health(self) -> BenchmarkResult:
        """Benchmark TypeDB health check."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        client.connect()

        result = self._measure(
            "typedb_health",
            "Health check query",
            client.health_check
        )
        result.metadata["target"] = "<10ms"

        client.close()
        return result

    def benchmark_typedb_get_rules(self) -> BenchmarkResult:
        """Benchmark fetching all rules."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return BenchmarkResult(
                name="typedb_get_rules",
                operation="Get all rules",
                iterations=0,
                total_time_ms=0,
                mean_time_ms=0,
                median_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=["Failed to connect to TypeDB"]
            )

        result = self._measure(
            "typedb_get_rules",
            "Get all 22 rules",
            client.get_all_rules
        )
        result.metadata["target"] = "<50ms for 22 rules"
        result.metadata["rule_count"] = 22

        client.close()
        return result

    def benchmark_typedb_get_rule_by_id(self) -> BenchmarkResult:
        """Benchmark fetching single rule by ID."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return BenchmarkResult(
                name="typedb_get_rule_by_id",
                operation="Get rule by ID",
                iterations=0,
                total_time_ms=0,
                mean_time_ms=0,
                median_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=["Failed to connect to TypeDB"]
            )

        result = self._measure(
            "typedb_get_rule_by_id",
            "Get RULE-001 by ID",
            client.get_rule_by_id,
            "RULE-001"
        )
        result.metadata["target"] = "<20ms"

        client.close()
        return result

    def benchmark_typedb_inference(self) -> BenchmarkResult:
        """Benchmark inference query (rule dependencies)."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return BenchmarkResult(
                name="typedb_inference",
                operation="Get rule dependencies with inference",
                iterations=0,
                total_time_ms=0,
                mean_time_ms=0,
                median_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=["Failed to connect to TypeDB"]
            )

        result = self._measure(
            "typedb_inference",
            "Get RULE-021 dependencies (inference)",
            client.get_rule_dependencies,
            "RULE-021"
        )
        result.metadata["target"] = "<100ms with inference"

        client.close()
        return result

    # =========================================================================
    # ChromaDB Benchmarks
    # =========================================================================

    def benchmark_chromadb_query(self) -> BenchmarkResult:
        """Benchmark ChromaDB semantic query."""
        try:
            import chromadb
            client = chromadb.HttpClient(host="localhost", port=8001)

            # Get or create test collection
            collection = client.get_or_create_collection("sim_ai_rules")

            def query_rules():
                collection.query(
                    query_texts=["authentication security"],
                    n_results=5
                )

            result = self._measure(
                "chromadb_query",
                "Semantic search (5 results)",
                query_rules
            )
            result.metadata["target"] = "<50ms"
            return result

        except Exception as e:
            return BenchmarkResult(
                name="chromadb_query",
                operation="Semantic search",
                iterations=0,
                total_time_ms=0,
                mean_time_ms=0,
                median_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=[f"ChromaDB error: {str(e)}"]
            )

    # =========================================================================
    # Hybrid Benchmarks
    # =========================================================================

    def benchmark_hybrid_query(self) -> BenchmarkResult:
        """Benchmark hybrid query (TypeDB + ChromaDB routing)."""
        try:
            from governance.memory_sync import HybridVectorDb

            hybrid = HybridVectorDb()

            result = self._measure(
                "hybrid_query",
                "Hybrid semantic + inference query",
                hybrid.search,
                "governance rules for authentication"
            )
            result.metadata["target"] = "<150ms combined"
            return result

        except ImportError:
            return BenchmarkResult(
                name="hybrid_query",
                operation="Hybrid query",
                iterations=0,
                total_time_ms=0,
                mean_time_ms=0,
                median_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=["HybridVectorDb not available"]
            )

    # =========================================================================
    # MCP Tool Benchmarks
    # =========================================================================

    def benchmark_mcp_health(self) -> BenchmarkResult:
        """Benchmark MCP governance health check."""
        try:
            from governance.mcp_server import governance_health

            result = self._measure(
                "mcp_health",
                "Governance MCP health check",
                governance_health
            )
            result.metadata["target"] = "<50ms"
            return result

        except ImportError:
            return BenchmarkResult(
                name="mcp_health",
                operation="MCP health check",
                iterations=0,
                total_time_ms=0,
                mean_time_ms=0,
                median_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                std_dev_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=["MCP server not available"]
            )

    # =========================================================================
    # Suite Runners
    # =========================================================================

    def run_typedb_suite(self) -> List[BenchmarkResult]:
        """Run all TypeDB benchmarks."""
        print("\n=== TypeDB Benchmark Suite ===")
        results = []

        benchmarks = [
            ("Connect", self.benchmark_typedb_connect),
            ("Health", self.benchmark_typedb_health),
            ("Get Rules", self.benchmark_typedb_get_rules),
            ("Get Rule By ID", self.benchmark_typedb_get_rule_by_id),
            ("Inference", self.benchmark_typedb_inference),
        ]

        for name, func in benchmarks:
            print(f"  Running: {name}...", end=" ")
            result = func()
            results.append(result)
            print(f"{result.mean_time_ms:.2f}ms (p95: {result.p95_time_ms:.2f}ms)")

        return results

    def run_chromadb_suite(self) -> List[BenchmarkResult]:
        """Run all ChromaDB benchmarks."""
        print("\n=== ChromaDB Benchmark Suite ===")
        results = []

        print("  Running: Semantic Query...", end=" ")
        result = self.benchmark_chromadb_query()
        results.append(result)
        print(f"{result.mean_time_ms:.2f}ms (p95: {result.p95_time_ms:.2f}ms)")

        return results

    def run_hybrid_suite(self) -> List[BenchmarkResult]:
        """Run all hybrid benchmarks."""
        print("\n=== Hybrid Benchmark Suite ===")
        results = []

        print("  Running: Hybrid Query...", end=" ")
        result = self.benchmark_hybrid_query()
        results.append(result)
        print(f"{result.mean_time_ms:.2f}ms (p95: {result.p95_time_ms:.2f}ms)")

        return results

    def run_all(self) -> BenchmarkSuite:
        """Run all benchmark suites."""
        print(f"\nGovernance Performance Benchmarks")
        print(f"Iterations per test: {self.iterations}")
        print("=" * 50)

        all_results = []
        all_results.extend(self.run_typedb_suite())
        all_results.extend(self.run_chromadb_suite())
        all_results.extend(self.run_hybrid_suite())

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


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run governance benchmarks")
    parser.add_argument("--iterations", "-i", type=int, default=100,
                        help="Number of iterations per benchmark")
    parser.add_argument("--output", "-o", type=str,
                        help="Output file for JSON results")
    parser.add_argument("--suite", "-s", choices=["all", "typedb", "chromadb", "hybrid"],
                        default="all", help="Benchmark suite to run")

    args = parser.parse_args()

    benchmark = GovernanceBenchmark(iterations=args.iterations)

    if args.suite == "typedb":
        benchmark.run_typedb_suite()
    elif args.suite == "chromadb":
        benchmark.run_chromadb_suite()
    elif args.suite == "hybrid":
        benchmark.run_hybrid_suite()
    else:
        suite = benchmark.run_all()
        if args.output:
            with open(args.output, "w") as f:
                json.dump(suite.to_dict(), f, indent=2)
            print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
