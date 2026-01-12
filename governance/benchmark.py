"""
Governance Performance Benchmarks (DEPRECATED - use governance.benchmark package)
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.benchmark instead:

    from governance.benchmark import GovernanceBenchmark
    from governance.benchmark import BenchmarkResult, BenchmarkSuite

Per RULE-010: Evidence-Based Wisdom - measure before optimize.
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.benchmark import (
    BenchmarkResult,
    BenchmarkSuite,
    BenchmarkBase,
    GovernanceBenchmark,
    TypeDBBenchmarks,
    ChromaDBBenchmarks,
    HybridBenchmarks,
)

__all__ = [
    "BenchmarkResult",
    "BenchmarkSuite",
    "BenchmarkBase",
    "GovernanceBenchmark",
    "TypeDBBenchmarks",
    "ChromaDBBenchmarks",
    "HybridBenchmarks",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.benchmark (single file) is deprecated. "
    "Use 'from governance.benchmark import GovernanceBenchmark' instead.",
    DeprecationWarning,
    stacklevel=2
)


def main():
    """CLI entry point (deprecated - use python -m governance.benchmark)."""
    from governance.benchmark.__main__ import main as _main
    _main()


if __name__ == "__main__":
    main()
