"""
Benchmark Data Models
Created: 2024-12-25 (P3.5)
Modularized: 2026-01-02 (RULE-032)

Dataclasses for benchmark results and suites.
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict


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
