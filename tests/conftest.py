"""
Pytest configuration and fixtures for Sim.ai PoC tests.

GAP-TEST-002: Test Reporting Modes
- MINIMAL: Dots only (. F S) - smallest context footprint
- MEDIUM (default): Progress bar + summary counts
- TRACE: Full logs for DEV isolated test runs
- CERTIFICATION: Collects all evidence in /results directory

Usage:
    pytest tests/ --report-minimal           # Minimal mode (dots only)
    pytest tests/ --report-trace             # Trace mode (verbose -vv)
    pytest tests/ --report-cert              # Certification mode
    pytest tests/ --report-cert --results-dir=custom  # Custom results dir
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
import httpx

# Service endpoints
LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000")
CHROMADB_URL = os.getenv("CHROMADB_URL", "http://localhost:8001")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
AGENTS_URL = os.getenv("AGENTS_URL", "http://localhost:7777")
OPIK_URL = os.getenv("OPIK_URL", "http://localhost:5173")
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
LITELLM_API_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-dev-key")


# =============================================================================
# GAP-TEST-002: Test Reporting Mode Classes
# =============================================================================

class MinimalReporter:
    """Minimal reporter: dots only (. F S) - smallest context footprint."""

    def __init__(self, config):
        self.config = config
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            if report.passed:
                sys.stdout.write(".")
                self.passed += 1
            elif report.failed:
                sys.stdout.write("F")
                self.failed += 1
        elif report.when == "setup" and report.skipped:
            sys.stdout.write("S")
            self.skipped += 1
        sys.stdout.flush()

    def pytest_sessionfinish(self, session):
        total = self.passed + self.failed + self.skipped
        print(f"\n\n{self.passed} passed, {self.failed} failed, {self.skipped} skipped ({total} total)")


class CertificationReporter:
    """Certification reporter: collects evidence to /results directory."""

    def __init__(self, config):
        self.config = config
        self.results = []
        self.results_dir = Path(config.getoption("--results-dir", default="results"))
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.date_dir = self.results_dir / datetime.now().strftime("%Y-%m-%d")
        self.date_dir.mkdir(parents=True, exist_ok=True)
        self.start_time = datetime.now()

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.skipped):
            result = {
                "nodeid": report.nodeid,
                "outcome": report.outcome,
                "duration": report.duration,
                "when": report.when,
            }
            if report.failed:
                result["longrepr"] = str(report.longrepr)[:2000]  # Truncate long errors
            self.results.append(result)

    def pytest_sessionfinish(self, session):
        # Write JSON results
        json_path = self.date_dir / f"test-run-{self.timestamp}.json"
        passed = sum(1 for r in self.results if r["outcome"] == "passed")
        failed = sum(1 for r in self.results if r["outcome"] == "failed")
        skipped = sum(1 for r in self.results if r["outcome"] == "skipped")

        summary = {
            "timestamp": self.timestamp,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "tests": self.results
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"\n[CERT] Results saved to: {json_path}")
        print(f"[CERT] {passed} passed, {failed} failed, {skipped} skipped")


# =============================================================================
# Pytest Hooks
# =============================================================================

def pytest_addoption(parser):
    """GAP-TEST-002: Add test reporting mode options."""
    group = parser.getgroup("reporting", "Test Reporting Modes (GAP-TEST-002)")
    group.addoption(
        "--report-minimal",
        action="store_true",
        default=False,
        help="Minimal output: dots only (. F S) - smallest context footprint"
    )
    group.addoption(
        "--report-trace",
        action="store_true",
        default=False,
        help="Trace mode: full logs for DEV debugging (-vv equivalent)"
    )
    group.addoption(
        "--report-cert",
        action="store_true",
        default=False,
        help="Certification mode: collect evidence in /results directory"
    )
    group.addoption(
        "--results-dir",
        action="store",
        default="results",
        help="Directory for test results (default: results)"
    )


def pytest_configure(config):
    """Register custom markers and configure reporting mode."""
    # Register markers
    config.addinivalue_line("markers", "integration: Integration tests requiring running services")
    config.addinivalue_line("markers", "unit: Unit tests that don't require services")
    config.addinivalue_line("markers", "slow: Slow tests (model inference)")
    config.addinivalue_line("markers", "heuristic(name): Exploratory test heuristic (SFDIPOT.*, CRUCSS.*)")

    # Determine report mode
    try:
        is_minimal = config.getoption("--report-minimal", default=False)
        is_trace = config.getoption("--report-trace", default=False)
        is_cert = config.getoption("--report-cert", default=False)
    except (ValueError, AttributeError):
        is_minimal = is_trace = is_cert = False

    # Configure based on mode
    if is_minimal:
        # Minimal mode: suppress default output
        config.option.verbose = -1
        config.pluginmanager.register(MinimalReporter(config), "minimal_reporter")
    elif is_trace:
        # Trace mode: maximum verbosity
        config.option.verbose = 2
    elif is_cert:
        # Certification mode: register evidence collector
        config.pluginmanager.register(CertificationReporter(config), "cert_reporter")


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def http_client() -> Generator[httpx.Client, None, None]:
    """Shared HTTP client for all tests."""
    client = httpx.Client(timeout=30.0)
    yield client
    client.close()


@pytest.fixture
def litellm_client(http_client: httpx.Client):
    """LiteLLM API client."""
    return {"client": http_client, "base_url": LITELLM_URL, "api_key": LITELLM_API_KEY}


@pytest.fixture
def chromadb_client(http_client: httpx.Client):
    """ChromaDB API client."""
    return {"client": http_client, "base_url": CHROMADB_URL}


@pytest.fixture
def agents_client(http_client: httpx.Client):
    """Agents API client."""
    return {"client": http_client, "base_url": AGENTS_URL}


@pytest.fixture
def opik_client(http_client: httpx.Client):
    """Opik API client."""
    return {"client": http_client, "base_url": OPIK_URL}


@pytest.fixture
def typedb_config():
    """TypeDB connection config."""
    return {"host": TYPEDB_HOST, "port": TYPEDB_PORT}
