"""
Integration tests for EPIC-TASK-QUALITY-V3 Phase 11: MCP Data Integrity.

Per TEST-E2E-01-v1: Tier 2 — tests against live TypeDB via REST API.
Requires: API container running on :8082, TypeDB on :1729.

Run: .venv/bin/python3 -m pytest tests/integration/test_p11_live_typedb.py -v
"""

import time

import pytest
import requests

BASE = "http://localhost:8082/api"


def _api_healthy():
    """Check if API is reachable."""
    try:
        r = requests.get(f"{BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _api_healthy(),
    reason="API not reachable at localhost:8082",
)


def _create_task(task_id, **kwargs):
    """Create a test task, cleaning up any leftover first."""
    requests.delete(f"{BASE}/tasks/{task_id}")
    time.sleep(0.3)
    defaults = {
        "task_id": task_id,
        "description": f"Integration test {task_id}",
        "status": "OPEN",
        "phase": "P11",
        "task_type": "test",
    }
    defaults.update(kwargs)
    r = requests.post(f"{BASE}/tasks", json=defaults)
    assert r.status_code == 201, f"Create {task_id} failed: {r.text[:200]}"
    return r.json()


def _cleanup(task_id):
    requests.delete(f"{BASE}/tasks/{task_id}")


class TestBug018AgentIdPersistence:
    """SRVJ-BUG-018: agent_id must persist to TypeDB."""

    def test_explicit_agent_id_round_trip(self):
        """Explicit agent_id update persists and reads back from TypeDB."""
        tid = "P11-INT-018A"
        _create_task(tid)
        try:
            requests.put(f"{BASE}/tasks/{tid}", json={"agent_id": "explicit-agent"})
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            assert r.json()["agent_id"] == "explicit-agent"
        finally:
            _cleanup(tid)

    def test_h_task_002_auto_agent_id_persists(self):
        """H-TASK-002 auto-assigned agent_id persists to TypeDB."""
        tid = "P11-INT-018B"
        _create_task(tid)
        try:
            requests.put(f"{BASE}/tasks/{tid}", json={"status": "IN_PROGRESS"})
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            assert r.json()["agent_id"] == "code-agent"
        finally:
            _cleanup(tid)

    def test_agent_id_replacement(self):
        """Agent ID can be replaced with a new value."""
        tid = "P11-INT-018C"
        _create_task(tid)
        try:
            requests.put(f"{BASE}/tasks/{tid}", json={"agent_id": "agent-1"})
            time.sleep(0.3)
            requests.put(f"{BASE}/tasks/{tid}", json={"agent_id": "agent-2"})
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            assert r.json()["agent_id"] == "agent-2"
        finally:
            _cleanup(tid)


class TestBug019CreatedAtReadBack:
    """SRVJ-BUG-019: created_at must be non-null on read."""

    def test_created_at_on_single_get(self):
        """created_at is non-null when reading single task."""
        tid = "P11-INT-019A"
        _create_task(tid)
        try:
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            ct = r.json().get("created_at")
            assert ct is not None
            assert "2026" in ct
        finally:
            _cleanup(tid)

    def test_created_at_on_list(self):
        """created_at is non-null in batch list (batch fetch path)."""
        tid = "P11-INT-019B"
        _create_task(tid)
        try:
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks")
            items = r.json().get("items", [])
            ours = [t for t in items if t.get("task_id") == tid]
            assert len(ours) == 1
            assert ours[0]["created_at"] is not None
        finally:
            _cleanup(tid)


class TestBug020LinkTaskToRuleIdempotency:
    """SRVJ-BUG-020: link_task_to_rule must be idempotent."""

    def test_duplicate_link_produces_single_relation(self):
        """Linking same rule twice must result in exactly 1 relation."""
        tid = "P11-INT-020A"
        rule = "TEST-E2E-01-v1"
        _create_task(tid)
        try:
            requests.post(f"{BASE}/tasks/{tid}/rules/{rule}")
            requests.post(f"{BASE}/tasks/{tid}/rules/{rule}")
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            rules = r.json().get("linked_rules", [])
            assert rules.count(rule) == 1
        finally:
            _cleanup(tid)

    def test_different_rules_both_link(self):
        """Different rules create distinct relations."""
        tid = "P11-INT-020B"
        _create_task(tid)
        try:
            requests.post(f"{BASE}/tasks/{tid}/rules/TEST-E2E-01-v1")
            requests.post(f"{BASE}/tasks/{tid}/rules/ARCH-INFRA-01-v1")
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            rules = r.json().get("linked_rules", [])
            assert len(rules) == 2
        finally:
            _cleanup(tid)


class TestTier3FullCRUDCycle:
    """Tier 3: Full CRUD cycle — all fields must survive create→update→get."""

    def test_all_fields_non_null_after_crud_cycle(self):
        """Create + update IN_PROGRESS + GET → all key fields non-null."""
        tid = "P11-INT-TIER3"
        _create_task(tid, priority="HIGH", summary="Tier 3 probe")
        try:
            requests.put(f"{BASE}/tasks/{tid}", json={"status": "IN_PROGRESS"})
            time.sleep(0.5)
            r = requests.get(f"{BASE}/tasks/{tid}")
            d = r.json()
            for field in ["status", "agent_id", "created_at", "claimed_at",
                          "summary", "priority", "task_type"]:
                assert d.get(field) is not None, f"{field} is null after CRUD cycle"
        finally:
            _cleanup(tid)
