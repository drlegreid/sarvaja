"""
Benchmark Base Class
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Base class with measurement utilities for governance benchmarks.
"""
import time
import statistics
from typing import List, Callable

from governance.benchmark.models import BenchmarkResult


class BenchmarkBase:
    """
    Base class for governance benchmarks.

    Provides measurement utilities used by all benchmark types.
    """

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

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

    def _create_error_result(self, name: str, operation: str, error_msg: str) -> BenchmarkResult:
        """Create a result for failed benchmark setup."""
        return BenchmarkResult(
            name=name,
            operation=operation,
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
            errors=[error_msg]
        )
