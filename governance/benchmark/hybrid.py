"""
Hybrid and MCP Benchmarks
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Benchmarks for hybrid queries (TypeDB + ChromaDB) and MCP tools.
"""
from typing import List

from governance.benchmark.base import BenchmarkBase
from governance.benchmark.models import BenchmarkResult


class HybridBenchmarks(BenchmarkBase):
    """Hybrid and MCP performance benchmarks."""

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
            return self._create_error_result(
                "hybrid_query",
                "Hybrid query",
                "HybridVectorDb not available"
            )

    def benchmark_mcp_health(self) -> BenchmarkResult:
        """Benchmark MCP governance health check."""
        try:
            from governance.mcp_server_core import governance_health

            result = self._measure(
                "mcp_health",
                "Governance MCP health check",
                governance_health
            )
            result.metadata["target"] = "<50ms"
            return result

        except ImportError:
            return self._create_error_result(
                "mcp_health",
                "MCP health check",
                "MCP server not available"
            )

    def run_suite(self) -> List[BenchmarkResult]:
        """Run all hybrid benchmarks."""
        print("\n=== Hybrid Benchmark Suite ===")
        results = []

        benchmarks = [
            ("Hybrid Query", self.benchmark_hybrid_query),
            ("MCP Health", self.benchmark_mcp_health),
        ]

        for name, func in benchmarks:
            print(f"  Running: {name}...", end=" ")
            result = func()
            results.append(result)
            print(f"{result.mean_time_ms:.2f}ms (p95: {result.p95_time_ms:.2f}ms)")

        return results
