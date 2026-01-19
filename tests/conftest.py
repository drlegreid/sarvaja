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

# EPIC-DR-009: API endpoint and test data prefixes
DASHBOARD_API_URL = os.getenv("DASHBOARD_API_URL", "http://localhost:8082")
API_MAX_LIMIT = 200  # API enforces max 200 items per request
TEST_DATA_PREFIXES = [
    "TEST-", "AGENT-TEST-", "UI-TEST-", "VERIFY-TEST-",
    "LINK-TEST-", "TASK-TEST-", "SESSION-TEST-", "E2E-TEST-",
]


def _is_test_entity(entity_id: str) -> bool:
    """Check if entity ID matches test data pattern."""
    return any(entity_id.startswith(prefix) for prefix in TEST_DATA_PREFIXES)


def _cleanup_test_tasks(client: httpx.Client) -> dict:
    """Remove all test-prefixed tasks. Returns cleanup statistics."""
    stats = {"checked": 0, "deleted": 0, "failed": 0, "errors": []}
    try:
        response = client.get(f"{DASHBOARD_API_URL}/api/tasks", params={"limit": API_MAX_LIMIT})
        if response.status_code != 200:
            stats["errors"].append(f"Failed to fetch tasks: {response.status_code}")
            return stats
        data = response.json()
        tasks = data.get("items", data) if isinstance(data, dict) else data
        for task in tasks:
            task_id = task.get("task_id") or task.get("id", "")
            if _is_test_entity(task_id):
                stats["checked"] += 1
                try:
                    del_response = client.delete(f"{DASHBOARD_API_URL}/api/tasks/{task_id}")
                    if del_response.status_code in (200, 204):
                        stats["deleted"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Delete {task_id}: {str(e)}")
    except Exception as e:
        stats["errors"].append(f"Cleanup failed: {str(e)}")
    return stats


def _cleanup_test_sessions(client: httpx.Client) -> dict:
    """Remove all test-prefixed sessions. Returns cleanup statistics."""
    stats = {"checked": 0, "deleted": 0, "failed": 0, "errors": []}
    try:
        response = client.get(f"{DASHBOARD_API_URL}/api/sessions", params={"limit": API_MAX_LIMIT})
        if response.status_code != 200:
            stats["errors"].append(f"Failed to fetch sessions: {response.status_code}")
            return stats
        sessions = response.json()
        if isinstance(sessions, dict):
            sessions = sessions.get("items", [])
        for session in sessions:
            session_id = session.get("session_id") or session.get("id", "")
            if _is_test_entity(session_id):
                stats["checked"] += 1
                try:
                    del_response = client.delete(f"{DASHBOARD_API_URL}/api/sessions/{session_id}")
                    if del_response.status_code in (200, 204):
                        stats["deleted"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Delete {session_id}: {str(e)}")
    except Exception as e:
        stats["errors"].append(f"Cleanup failed: {str(e)}")
    return stats


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

    # EPIC-DR-009: Test data cleanup option
    parser.addoption(
        "--cleanup-test-data",
        action="store_true",
        default=False,
        help="Clean up test data (TEST-*, AGENT-TEST-*, etc.) before running tests"
    )
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
    # Register markers (matching pytest.ini)
    config.addinivalue_line("markers", "unit: Unit tests (no external deps, container-safe)")
    config.addinivalue_line("markers", "integration: Integration tests (needs TypeDB/ChromaDB)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (needs services + may need browser)")
    config.addinivalue_line("markers", "browser: Browser tests (needs pytest-playwright, run locally)")
    config.addinivalue_line("markers", "slow: Slow tests (model inference)")
    config.addinivalue_line("markers", "api: API tests (needs REST server on :8082)")
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

    # EPIC-DR-009: Run cleanup if requested
    try:
        do_cleanup = config.getoption("--cleanup-test-data", default=False)
        if do_cleanup:
            print("[CLEANUP] Running pre-test data cleanup...")
            with httpx.Client(timeout=30.0) as client:
                task_stats = _cleanup_test_tasks(client)
                session_stats = _cleanup_test_sessions(client)
                print(f"[CLEANUP] Removed {task_stats['deleted']} tasks, {session_stats['deleted']} sessions")
    except (ValueError, AttributeError):
        pass


# =============================================================================
# Auto-mark tests based on path (GAP-TEST-PROFILES)
# =============================================================================

def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their file path.

    Path patterns:
    - tests/e2e/* -> e2e marker
    - tests/integration/* -> integration marker
    - tests/unit/* -> unit marker
    - *_e2e.py -> e2e marker
    - Files importing pytest_playwright -> browser marker
    """
    for item in items:
        # Get relative path
        rel_path = str(item.fspath)

        # Auto-mark based on directory
        if "/e2e/" in rel_path or "_e2e.py" in rel_path:
            item.add_marker(pytest.mark.e2e)
            # Check if it's a browser test (has playwright imports)
            if hasattr(item, 'module'):
                module_source = getattr(item.module, '__file__', '')
                if 'playwright' in str(module_source).lower():
                    item.add_marker(pytest.mark.browser)
        elif "/integration/" in rel_path:
            item.add_marker(pytest.mark.integration)
        elif "/unit/" in rel_path:
            item.add_marker(pytest.mark.unit)


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


# =============================================================================
# EPIC-DR-009: Test Data Cleanup Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def cleanup_test_data():
    """
    Session-scoped fixture that cleans up test data after all tests.

    Per EPIC-DR-009: Removes TEST-*, AGENT-TEST-*, etc. prefixed entities.

    Usage:
        def test_something(cleanup_test_data):
            # Test runs, cleanup happens automatically at session end
            pass
    """
    # Yield to run tests first
    yield

    # Cleanup after all tests complete
    with httpx.Client(timeout=30.0) as client:
        print("\n[CLEANUP] Starting test data cleanup...")

        task_stats = _cleanup_test_tasks(client)
        print(f"[CLEANUP] Tasks: {task_stats['deleted']} deleted, {task_stats['failed']} failed")

        session_stats = _cleanup_test_sessions(client)
        print(f"[CLEANUP] Sessions: {session_stats['deleted']} deleted, {session_stats['failed']} failed")

        if task_stats["errors"] or session_stats["errors"]:
            print("[CLEANUP] Errors:")
            for err in task_stats["errors"][:5]:
                print(f"  - {err}")
            for err in session_stats["errors"][:5]:
                print(f"  - {err}")


@pytest.fixture
def test_task_factory(http_client: httpx.Client):
    """
    Factory fixture for creating test tasks with automatic cleanup.

    Per EPIC-DR-009: Creates tasks with TEST- prefix for easy identification.

    Usage:
        def test_something(test_task_factory):
            task = test_task_factory(description="My test task")
            # task has task_id like "TEST-abc123"
            # Cleanup happens automatically
    """
    created_task_ids = []

    def create_task(
        description: str = "Test task",
        phase: str = "TEST",
        status: str = "TODO",
        **kwargs
    ) -> dict:
        """Create a test task with TEST- prefix."""
        import uuid
        task_id = f"TEST-{uuid.uuid4().hex[:8].upper()}"

        task_data = {
            "task_id": task_id,
            "description": description,
            "phase": phase,
            "status": status,
            **kwargs
        }

        response = http_client.post(f"{DASHBOARD_API_URL}/api/tasks", json=task_data)
        if response.status_code == 201:
            created_task_ids.append(task_id)
            return response.json()
        else:
            raise RuntimeError(f"Failed to create task: {response.status_code} - {response.text}")

    yield create_task

    # Cleanup created tasks
    for task_id in created_task_ids:
        try:
            http_client.delete(f"{DASHBOARD_API_URL}/api/tasks/{task_id}")
        except Exception:
            pass  # Best effort cleanup


@pytest.fixture
def test_session_factory(http_client: httpx.Client):
    """
    Factory fixture for creating test sessions with automatic cleanup.

    Per EPIC-DR-009: Creates sessions with SESSION-TEST- prefix.

    Usage:
        def test_something(test_session_factory):
            session = test_session_factory(description="My test session")
            # Cleanup happens automatically
    """
    created_session_ids = []

    def create_session(
        description: str = "Test session",
        status: str = "ACTIVE",
        **kwargs
    ) -> dict:
        """Create a test session with SESSION-TEST- prefix."""
        import uuid
        session_id = f"SESSION-TEST-{uuid.uuid4().hex[:8].upper()}"

        session_data = {
            "session_id": session_id,
            "description": description,
            "status": status,
            **kwargs
        }

        response = http_client.post(f"{DASHBOARD_API_URL}/api/sessions", json=session_data)
        if response.status_code == 201:
            created_session_ids.append(session_id)
            return response.json()
        else:
            raise RuntimeError(f"Failed to create session: {response.status_code} - {response.text}")

    yield create_session

    # Cleanup created sessions
    for session_id in created_session_ids:
        try:
            http_client.delete(f"{DASHBOARD_API_URL}/api/sessions/{session_id}")
        except Exception:
            pass  # Best effort cleanup
