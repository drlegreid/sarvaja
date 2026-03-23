"""Task Test Factory with Auto-Cleanup.

SRVJ-FEAT-005: Shared factory fixture for integration + E2E tests.
Creates tasks via live API, tracks IDs, auto-cleans on teardown.

Usage (pytest fixture):
    def test_something(task_factory):
        t = task_factory.create(summary="E2E > Test > Factory > Demo")
        assert t.task_id.startswith("E2E-")
        # Auto-cleanup on teardown (pass or fail)

Usage (purge CLI):
    python3 -m tests.shared.task_test_factory --purge
"""

import uuid
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Prefix for factory-created tasks
FACTORY_PREFIX = "E2E"

# All test data prefixes — used by purge and global cleanup
ALL_TEST_PREFIXES = [
    "E2E-", "E2E-QUAL-", "RF-QUAL-", "INTTEST-", "CRUD-",
    "TEST-", "AGENT-TEST-", "UI-TEST-", "VERIFY-TEST-",
    "LINK-TEST-", "TASK-TEST-", "SESSION-TEST-", "E2E-TEST-",
]

API_BASE = "http://localhost:8082/api"
TIMEOUT = 10.0


@dataclass
class CreatedTask:
    """Tracks a task created by the factory."""

    task_id: str
    response: dict


class TaskTestFactory:
    """Creates tasks via API and tracks them for cleanup.

    Accepts an optional httpx.Client for testability.
    """

    def __init__(
        self,
        client: Optional[httpx.Client] = None,
        base_url: str = API_BASE,
        timeout: float = TIMEOUT,
    ):
        self._base_url = base_url
        self._timeout = timeout
        self._created: list[str] = []
        self._client = client
        self._owns_client = client is None

    @property
    def client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(base_url=self._base_url, timeout=self._timeout)
            self._owns_client = True
        return self._client

    def create(
        self,
        summary: str = "E2E > Factory > Default > Task",
        task_type: str = "test",
        priority: str = "LOW",
        workspace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> CreatedTask:
        """Create a task via API and track it for cleanup."""
        if task_id is None:
            task_id = f"{FACTORY_PREFIX}-{uuid.uuid4().hex[:8].upper()}"

        payload = {
            "task_id": task_id,
            "description": summary,
            "summary": summary,
            "task_type": task_type,
            "priority": priority,
            "phase": "P10",
            **kwargs,
        }
        if workspace_id:
            payload["workspace_id"] = workspace_id

        r = self.client.post("/tasks", json=payload)
        if r.status_code == 201:
            self._created.append(task_id)
            return CreatedTask(task_id=task_id, response=r.json())
        raise RuntimeError(f"Factory create failed ({r.status_code}): {r.text}")

    def cleanup(self) -> dict:
        """Delete all tracked tasks. Returns stats."""
        stats = {"deleted": 0, "failed": 0, "errors": []}
        for task_id in self._created:
            try:
                r = self.client.delete(f"/tasks/{task_id}")
                if r.status_code in (200, 204, 404):
                    stats["deleted"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append(f"{task_id}: {r.status_code}")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{task_id}: {e}")
        self._created.clear()
        if stats["errors"]:
            logger.warning("Factory cleanup errors: %s", stats["errors"])
        return stats

    def close(self):
        """Close the HTTP client if we own it."""
        if self._owns_client and self._client and not self._client.is_closed:
            self._client.close()

    @property
    def created_ids(self) -> list[str]:
        """IDs of all tasks created by this factory instance."""
        return list(self._created)


def purge_test_artifacts(
    base_url: str = API_BASE,
    prefixes: Optional[list[str]] = None,
) -> dict:
    """One-time purge of all test artifacts from TypeDB.

    SRVJ-CHORE-002: Deletes tasks matching test prefixes.
    """
    if prefixes is None:
        prefixes = ALL_TEST_PREFIXES

    stats = {"checked": 0, "deleted": 0, "failed": 0, "errors": []}
    with httpx.Client(base_url=base_url, timeout=TIMEOUT) as client:
        for _ in range(20):
            r = client.get("/tasks", params={"limit": 200})
            if r.status_code != 200:
                stats["errors"].append(f"Fetch failed: {r.status_code}")
                break
            items = r.json().get("items", [])
            deleted_round = 0
            for item in items:
                tid = item.get("task_id", "")
                if any(tid.startswith(p) for p in prefixes):
                    stats["checked"] += 1
                    try:
                        dr = client.delete(f"/tasks/{tid}")
                        if dr.status_code in (200, 204, 404):
                            stats["deleted"] += 1
                            deleted_round += 1
                        else:
                            stats["failed"] += 1
                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append(f"{tid}: {e}")
            if deleted_round == 0:
                break
    return stats


# =============================================================================
# Pytest fixtures — import in conftest.py
# =============================================================================

try:
    import pytest

    @pytest.fixture
    def task_factory():
        """Per-test task factory with auto-cleanup."""
        factory = TaskTestFactory()
        yield factory
        factory.cleanup()
        factory.close()

    @pytest.fixture(scope="module")
    def module_task_factory():
        """Module-scoped factory — shared across tests in a module."""
        factory = TaskTestFactory()
        yield factory
        factory.cleanup()
        factory.close()

except ImportError:
    pass  # pytest not available (e.g., CLI usage)


# =============================================================================
# CLI entry point for purge
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if "--purge" in sys.argv:
        print("Purging test artifacts from TypeDB...")
        result = purge_test_artifacts()
        print(f"Checked: {result['checked']}")
        print(f"Deleted: {result['deleted']}")
        print(f"Failed:  {result['failed']}")
        if result["errors"]:
            print("Errors:")
            for err in result["errors"][:10]:
                print(f"  - {err}")
        sys.exit(0 if result["failed"] == 0 else 1)
    else:
        print("Usage: python3 -m tests.shared.task_test_factory --purge")
        sys.exit(1)
