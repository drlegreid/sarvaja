"""Integration test fixtures for MCP tool integration tests.

Shared fixtures for testing MCP tools against real TypeDB and ChromaDB instances.
Per TEST-E2E-01-v1: Tier 2 integration tests require live services.

Run: .venv/bin/python3 -m pytest tests/integration/ -v -m integration
Requires: TypeDB on localhost:1729, ChromaDB on localhost:8001, API on localhost:8082
"""

import json
import os
import uuid

import pytest

# ---------------------------------------------------------------------------
# Environment: force JSON output for MCP tools during tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def mcp_json_format():
    """Force JSON output so test assertions can json.loads() results."""
    old = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old


# ---------------------------------------------------------------------------
# Service availability guards
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def typedb_available():
    """Skip entire module if TypeDB is not reachable."""
    try:
        from governance.mcp_tools.common import get_typedb_client
        client = get_typedb_client()
        try:
            if not client.connect():
                pytest.skip("TypeDB not available")
        finally:
            client.close()
    except Exception:
        pytest.skip("TypeDB not available")
    return True


@pytest.fixture(scope="module")
def chromadb_available():
    """Skip entire module if ChromaDB is not reachable."""
    try:
        import httpx
        # Try v2 first, then v1 (depends on ChromaDB version)
        for path in ["/api/v2/heartbeat", "/api/v1/heartbeat"]:
            try:
                r = httpx.get(f"http://localhost:8001{path}", timeout=5.0)
                if r.status_code == 200:
                    return True
            except Exception:
                continue
        pytest.skip("ChromaDB not available")
    except Exception:
        pytest.skip("ChromaDB not available")


# ---------------------------------------------------------------------------
# MCP tool extraction helper
# ---------------------------------------------------------------------------

class MockMCP:
    """Lightweight mock that captures @mcp.tool() registrations."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


@pytest.fixture(scope="module")
def mock_mcp():
    """Create a MockMCP instance for tool registration."""
    return MockMCP()


# ---------------------------------------------------------------------------
# Test ID generator
# ---------------------------------------------------------------------------

def make_test_id(prefix: str = "INTTEST") -> str:
    """Generate a unique test ID that cleanup fixtures can find."""
    short = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{short}"


# ---------------------------------------------------------------------------
# JSON result parser
# ---------------------------------------------------------------------------

def parse_mcp_result(result: str) -> dict:
    """Parse MCP tool JSON result, handling both str and dict."""
    if isinstance(result, dict):
        return result
    return json.loads(result)


# ---------------------------------------------------------------------------
# SRVJ-FEAT-005: Shared task factory fixtures
# ---------------------------------------------------------------------------

from tests.shared.task_test_factory import (  # noqa: E402
    task_factory,
    module_task_factory,
    purge_test_artifacts,
)


@pytest.fixture(scope="module", autouse=True)
def sweep_orphans_after_module():
    """Safety net: purge any orphaned test artifacts after each module.

    SRVJ-FEAT-007: Ensures no test data leaks even if per-test cleanup fails.
    """
    yield
    try:
        purge_test_artifacts()
    except Exception:
        pass  # Best effort — don't fail tests on cleanup errors
