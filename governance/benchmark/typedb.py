"""
TypeDB Benchmarks
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Benchmarks for TypeDB operations: connect, health, rules, inference.
"""
from typing import List

from governance.benchmark.base import BenchmarkBase
from governance.benchmark.models import BenchmarkResult


class TypeDBBenchmarks(BenchmarkBase):
    """TypeDB performance benchmarks."""

    def benchmark_connect(self) -> BenchmarkResult:
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

    def benchmark_health(self) -> BenchmarkResult:
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

    def benchmark_get_rules(self) -> BenchmarkResult:
        """Benchmark fetching all rules."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return self._create_error_result(
                "typedb_get_rules",
                "Get all rules",
                "Failed to connect to TypeDB"
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

    def benchmark_get_rule_by_id(self) -> BenchmarkResult:
        """Benchmark fetching single rule by ID."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return self._create_error_result(
                "typedb_get_rule_by_id",
                "Get rule by ID",
                "Failed to connect to TypeDB"
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

    def benchmark_inference(self) -> BenchmarkResult:
        """Benchmark inference query (rule dependencies)."""
        from governance.client import TypeDBClient

        client = TypeDBClient()
        if not client.connect():
            return self._create_error_result(
                "typedb_inference",
                "Get rule dependencies with inference",
                "Failed to connect to TypeDB"
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

    def run_suite(self) -> List[BenchmarkResult]:
        """Run all TypeDB benchmarks."""
        print("\n=== TypeDB Benchmark Suite ===")
        results = []

        benchmarks = [
            ("Connect", self.benchmark_connect),
            ("Health", self.benchmark_health),
            ("Get Rules", self.benchmark_get_rules),
            ("Get Rule By ID", self.benchmark_get_rule_by_id),
            ("Inference", self.benchmark_inference),
        ]

        for name, func in benchmarks:
            print(f"  Running: {name}...", end=" ")
            result = func()
            results.append(result)
            print(f"{result.mean_time_ms:.2f}ms (p95: {result.p95_time_ms:.2f}ms)")

        return results
