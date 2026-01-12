"""
ChromaDB Benchmarks
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Benchmarks for ChromaDB semantic search operations.
"""
from typing import List

from governance.benchmark.base import BenchmarkBase
from governance.benchmark.models import BenchmarkResult


class ChromaDBBenchmarks(BenchmarkBase):
    """ChromaDB performance benchmarks."""

    def benchmark_query(self) -> BenchmarkResult:
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
            return self._create_error_result(
                "chromadb_query",
                "Semantic search",
                f"ChromaDB error: {str(e)}"
            )

    def run_suite(self) -> List[BenchmarkResult]:
        """Run all ChromaDB benchmarks."""
        print("\n=== ChromaDB Benchmark Suite ===")
        results = []

        print("  Running: Semantic Query...", end=" ")
        result = self.benchmark_query()
        results.append(result)
        print(f"{result.mean_time_ms:.2f}ms (p95: {result.p95_time_ms:.2f}ms)")

        return results
