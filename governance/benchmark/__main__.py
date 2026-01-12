"""
Benchmark CLI Entry Point
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Usage:
    python -m governance.benchmark [--iterations 100] [--suite all]
"""
import argparse
import json

from governance.benchmark.runner import GovernanceBenchmark


def main():
    """CLI entry point."""
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
