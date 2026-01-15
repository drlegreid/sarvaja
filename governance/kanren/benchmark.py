"""
Kanren Performance Benchmarks (KAN-005).

Measures overhead of Kanren constraint validation vs direct Python.
Target: <100ms overhead for typical validation operations.

Per RD-KANREN-CONTEXT: Performance benchmarks for real-time use.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from functools import wraps

from .models import AgentContext, TaskContext, RuleContext
from .trust import trust_level, requires_supervisor, can_execute_priority
from .tasks import task_requires_evidence, valid_task_assignment
from .rag import filter_rag_chunks
from .conflicts import find_rule_conflicts


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    total_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    target_ms: float
    passed: bool

    def summary(self) -> str:
        """Generate summary string."""
        status = "PASS" if self.passed else "FAIL"
        return f"{self.name}: {self.avg_ms:.3f}ms avg ({status}, target <{self.target_ms}ms)"


def benchmark(iterations: int = 1000, target_ms: float = 100.0):
    """Decorator to benchmark a function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> BenchmarkResult:
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                func(*args, **kwargs)
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms

            total = sum(times)
            return BenchmarkResult(
                name=func.__name__,
                iterations=iterations,
                total_ms=total,
                avg_ms=total / iterations,
                min_ms=min(times),
                max_ms=max(times),
                target_ms=target_ms,
                passed=(total / iterations) < target_ms
            )
        return wrapper
    return decorator


# =============================================================================
# Kanren Benchmark Functions
# =============================================================================

@benchmark(iterations=1000, target_ms=1.0)
def bench_trust_level():
    """Benchmark trust_level calculation."""
    trust_level(0.85)


@benchmark(iterations=1000, target_ms=1.0)
def bench_requires_supervisor():
    """Benchmark requires_supervisor Kanren query."""
    requires_supervisor("trusted")


@benchmark(iterations=1000, target_ms=1.0)
def bench_can_execute_priority():
    """Benchmark can_execute_priority Kanren query."""
    can_execute_priority("trusted", "CRITICAL")


@benchmark(iterations=1000, target_ms=1.0)
def bench_task_requires_evidence():
    """Benchmark task_requires_evidence Kanren query."""
    task_requires_evidence("CRITICAL")


@benchmark(iterations=500, target_ms=5.0)
def bench_valid_task_assignment():
    """Benchmark full task assignment validation."""
    agent = AgentContext("AGENT-001", "Test", 0.85, "claude-code")
    task = TaskContext("TASK-001", "CRITICAL", True)
    valid_task_assignment(agent, task)


@benchmark(iterations=500, target_ms=5.0)
def bench_filter_rag_chunks():
    """Benchmark RAG chunk filtering."""
    chunks = [
        {"source": "typedb", "verified": True, "type": "rule"},
        {"source": "chromadb", "verified": True, "type": "evidence"},
        {"source": "external", "verified": False, "type": "unknown"},
    ] * 10  # 30 chunks
    filter_rag_chunks(chunks)


@benchmark(iterations=200, target_ms=10.0)
def bench_find_rule_conflicts():
    """Benchmark rule conflict detection."""
    rules = [
        RuleContext(f"RULE-{i:03d}", "HIGH", "ACTIVE", "governance")
        for i in range(10)
    ]
    find_rule_conflicts(rules)


# =============================================================================
# Direct Python Comparison Functions
# =============================================================================

def direct_trust_level(score: float) -> str:
    """Direct Python trust level (no Kanren)."""
    if score >= 0.9:
        return "expert"
    elif score >= 0.7:
        return "trusted"
    elif score >= 0.5:
        return "supervised"
    else:
        return "restricted"


def direct_requires_supervisor(trust: str) -> bool:
    """Direct Python supervisor check (no Kanren)."""
    return trust in ("restricted", "supervised")


def direct_can_execute(trust: str, priority: str) -> bool:
    """Direct Python execution check (no Kanren)."""
    if priority == "CRITICAL":
        return trust in ("expert", "trusted")
    elif priority == "HIGH":
        return trust != "restricted"
    return True


def direct_task_requires_evidence(priority: str) -> bool:
    """Direct Python evidence check (no Kanren)."""
    return priority in ("CRITICAL", "HIGH")


@benchmark(iterations=1000, target_ms=0.1)
def bench_direct_trust_level():
    """Benchmark direct Python trust level."""
    direct_trust_level(0.85)


@benchmark(iterations=1000, target_ms=0.1)
def bench_direct_requires_supervisor():
    """Benchmark direct Python supervisor check."""
    direct_requires_supervisor("trusted")


@benchmark(iterations=1000, target_ms=0.1)
def bench_direct_can_execute():
    """Benchmark direct Python execution check."""
    direct_can_execute("trusted", "CRITICAL")


@benchmark(iterations=1000, target_ms=0.1)
def bench_direct_requires_evidence():
    """Benchmark direct Python evidence check."""
    direct_task_requires_evidence("CRITICAL")


# =============================================================================
# Benchmark Runner
# =============================================================================

def run_all_benchmarks() -> List[BenchmarkResult]:
    """Run all benchmarks and return results."""
    benchmarks = [
        # Kanren benchmarks
        bench_trust_level,
        bench_requires_supervisor,
        bench_can_execute_priority,
        bench_task_requires_evidence,
        bench_valid_task_assignment,
        bench_filter_rag_chunks,
        bench_find_rule_conflicts,
        # Direct Python benchmarks
        bench_direct_trust_level,
        bench_direct_requires_supervisor,
        bench_direct_can_execute,
        bench_direct_requires_evidence,
    ]

    results = []
    for bench_func in benchmarks:
        result = bench_func()
        results.append(result)

    return results


def compare_kanren_vs_direct() -> Dict[str, Any]:
    """
    Compare Kanren vs direct Python performance.

    Returns:
        Dict with comparison metrics and overhead calculations
    """
    # Run benchmarks
    kanren_trust = bench_trust_level()
    direct_trust = bench_direct_trust_level()

    kanren_supervisor = bench_requires_supervisor()
    direct_supervisor = bench_direct_requires_supervisor()

    kanren_execute = bench_can_execute_priority()
    direct_execute = bench_direct_can_execute()

    kanren_evidence = bench_task_requires_evidence()
    direct_evidence = bench_direct_requires_evidence()

    # Calculate overhead
    def overhead(kanren: BenchmarkResult, direct: BenchmarkResult) -> float:
        if direct.avg_ms > 0:
            return ((kanren.avg_ms - direct.avg_ms) / direct.avg_ms) * 100
        return 0.0

    return {
        "trust_level": {
            "kanren_ms": kanren_trust.avg_ms,
            "direct_ms": direct_trust.avg_ms,
            "overhead_pct": overhead(kanren_trust, direct_trust),
        },
        "requires_supervisor": {
            "kanren_ms": kanren_supervisor.avg_ms,
            "direct_ms": direct_supervisor.avg_ms,
            "overhead_pct": overhead(kanren_supervisor, direct_supervisor),
        },
        "can_execute": {
            "kanren_ms": kanren_execute.avg_ms,
            "direct_ms": direct_execute.avg_ms,
            "overhead_pct": overhead(kanren_execute, direct_execute),
        },
        "requires_evidence": {
            "kanren_ms": kanren_evidence.avg_ms,
            "direct_ms": direct_evidence.avg_ms,
            "overhead_pct": overhead(kanren_evidence, direct_evidence),
        },
        "summary": {
            "all_kanren_passed": all([
                kanren_trust.passed,
                kanren_supervisor.passed,
                kanren_execute.passed,
                kanren_evidence.passed,
            ]),
            "total_kanren_avg_ms": sum([
                kanren_trust.avg_ms,
                kanren_supervisor.avg_ms,
                kanren_execute.avg_ms,
                kanren_evidence.avg_ms,
            ]),
        }
    }


def print_benchmark_report():
    """Print formatted benchmark report."""
    print("=" * 60)
    print("KANREN PERFORMANCE BENCHMARKS (KAN-005)")
    print("=" * 60)

    results = run_all_benchmarks()

    print("\n--- Individual Results ---")
    for result in results:
        print(result.summary())

    print("\n--- Kanren vs Direct Comparison ---")
    comparison = compare_kanren_vs_direct()
    for name, data in comparison.items():
        if name != "summary":
            print(f"{name}:")
            print(f"  Kanren: {data['kanren_ms']:.4f}ms")
            print(f"  Direct: {data['direct_ms']:.4f}ms")
            print(f"  Overhead: {data['overhead_pct']:.1f}%")

    summary = comparison["summary"]
    print(f"\n--- Summary ---")
    print(f"All Kanren benchmarks passed: {summary['all_kanren_passed']}")
    print(f"Total Kanren avg time: {summary['total_kanren_avg_ms']:.3f}ms")
    print(f"Target: <100ms per operation")

    all_passed = all(r.passed for r in results)
    print(f"\n{'BENCHMARK SUITE PASSED' if all_passed else 'BENCHMARK SUITE FAILED'}")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    print_benchmark_report()
