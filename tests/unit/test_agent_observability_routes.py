"""
Unit tests for Agent Observability Routes.

Batch 128: Tests for governance/routes/agents/observability.py
- get_agents_status_summary: agent status + conflict detection
- get_stuck_agents / get_stale_locks: availability check
- agent_heartbeat: heartbeat registration
- acquire_lock / release_lock: file lock management
- get_merge_conflicts: conflict summary
- get_monitor_events: audit event retrieval
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from governance.routes.agents.observability import router


_MOD = "governance.routes.agents.observability"

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


# ── status summary ───────────────────────────────────────


class TestGetAgentsStatusSummary:

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", False)
    def test_unavailable(self):
        resp = client.get("/api/agents/status/summary")
        data = resp.json()
        assert data["status"] == "UNAVAILABLE"

    @patch(f"{_MOD}.CONFLICT_CHECKER_AVAILABLE", False)
    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.get_agent_status_summary")
    def test_without_conflicts(self, mock_summary):
        mock_summary.return_value = {
            "status": "OK", "alerts": [], "alert_count": 0
        }
        resp = client.get("/api/agents/status/summary")
        data = resp.json()
        assert data["status"] == "OK"
        assert "conflicts" not in data

    @patch(f"{_MOD}.CONFLICT_CHECKER_AVAILABLE", True)
    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.get_conflict_summary")
    @patch(f"{_MOD}.get_agent_status_summary")
    def test_with_conflicts(self, mock_summary, mock_conflicts):
        mock_summary.return_value = {
            "status": "OK", "alerts": [], "alert_count": 0
        }
        mock_conflicts.return_value = {
            "conflicts": ["file.py"],
            "conflict_count": 1,
            "has_conflicts": True,
            "alerts": [{"type": "conflict", "message": "file.py"}],
        }
        resp = client.get("/api/agents/status/summary")
        data = resp.json()
        assert data["status"] == "CRITICAL"
        assert data["conflict_count"] == 1
        assert len(data["alerts"]) == 1

    @patch(f"{_MOD}.CONFLICT_CHECKER_AVAILABLE", True)
    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.get_conflict_summary")
    @patch(f"{_MOD}.get_agent_status_summary")
    def test_no_conflicts_keeps_status(self, mock_summary, mock_conflicts):
        mock_summary.return_value = {
            "status": "OK", "alerts": [], "alert_count": 0
        }
        mock_conflicts.return_value = {
            "conflicts": [], "conflict_count": 0,
            "has_conflicts": False, "alerts": [],
        }
        resp = client.get("/api/agents/status/summary")
        data = resp.json()
        assert data["status"] == "OK"


# ── stuck agents / stale locks ───────────────────────────


class TestStuckAgentsAndLocks:

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", False)
    def test_stuck_unavailable(self):
        data = client.get("/api/agents/status/stuck").json()
        assert data["stuck_agents"] == []
        assert "error" in data

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.check_stuck_agents", return_value=["agent-1"])
    def test_stuck_returns_agents(self, mock_check):
        data = client.get("/api/agents/status/stuck").json()
        assert data["stuck_agents"] == ["agent-1"]

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", False)
    def test_locks_unavailable(self):
        data = client.get("/api/agents/status/locks").json()
        assert data["stale_locks"] == []

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.check_file_locks", return_value=[{"file": "test.py"}])
    def test_locks_returns_data(self, mock_check):
        data = client.get("/api/agents/status/locks").json()
        assert len(data["stale_locks"]) == 1


# ── heartbeat ────────────────────────────────────────────


class TestHeartbeat:

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", False)
    def test_unavailable_returns_503(self):
        resp = client.post("/api/agents/code-agent/heartbeat")
        assert resp.status_code == 503

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.update_agent_heartbeat", return_value={"ts": "2026-02-11"})
    def test_successful_heartbeat(self, mock_hb):
        # BUG-294-OBS-003: agent_type must be in whitelist {claude-code, docker-agent, ci, unknown}
        resp = client.post("/api/agents/code-agent/heartbeat?agent_type=claude-code&status=active")
        data = resp.json()
        assert data["agent_id"] == "code-agent"
        mock_hb.assert_called_once_with("code-agent", "claude-code", None, "active")


# ── lock acquire/release ─────────────────────────────────


class TestLockManagement:

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", False)
    def test_acquire_unavailable(self):
        resp = client.post("/api/agents/locks/acquire?resource=f.py&agent_id=a1")
        assert resp.status_code == 503

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.acquire_file_lock", return_value="/tmp/lock")
    def test_acquire_success(self, mock_lock):
        resp = client.post("/api/agents/locks/acquire?resource=f.py&agent_id=a1")
        data = resp.json()
        assert data["acquired"] is True

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.acquire_file_lock", return_value=None)
    def test_acquire_conflict(self, mock_lock):
        resp = client.post("/api/agents/locks/acquire?resource=f.py&agent_id=a1")
        assert resp.status_code == 409

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", False)
    def test_release_unavailable(self):
        resp = client.post("/api/agents/locks/release?resource=f.py&agent_id=a1")
        assert resp.status_code == 503

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.release_file_lock", return_value=True)
    def test_release_success(self, mock_rel):
        resp = client.post("/api/agents/locks/release?resource=f.py&agent_id=a1")
        data = resp.json()
        assert data["released"] is True

    @patch(f"{_MOD}.AGENT_STATUS_AVAILABLE", True)
    @patch(f"{_MOD}.release_file_lock", return_value=False)
    def test_release_not_found(self, mock_rel):
        resp = client.post("/api/agents/locks/release?resource=f.py&agent_id=a1")
        assert resp.status_code == 404


# ── merge conflicts ──────────────────────────────────────


class TestMergeConflicts:

    @patch(f"{_MOD}.CONFLICT_CHECKER_AVAILABLE", False)
    def test_unavailable(self):
        data = client.get("/api/agents/status/conflicts").json()
        assert data["status"] == "UNAVAILABLE"
        assert data["has_conflicts"] is False

    @patch(f"{_MOD}.CONFLICT_CHECKER_AVAILABLE", True)
    @patch(f"{_MOD}.get_conflict_summary", return_value={"has_conflicts": True, "conflicts": ["x.py"]})
    def test_returns_conflicts(self, mock_conf):
        data = client.get("/api/agents/status/conflicts").json()
        assert data["has_conflicts"] is True


# ── monitor events ───────────────────────────────────────


class TestMonitorEvents:

    @patch("agent.governance_ui.data_access.monitoring.read_audit_events", return_value=[{"type": "rule_change"}])
    def test_returns_events(self, mock_read):
        resp = client.get("/api/monitor/events")
        data = resp.json()
        assert data["count"] == 1
        assert data["events"][0]["type"] == "rule_change"

    @patch("agent.governance_ui.data_access.monitoring.read_audit_events", return_value=[])
    def test_clamps_params(self, mock_read):
        client.get("/api/monitor/events?days=99&limit=9999")
        call_kwargs = mock_read.call_args[1]
        assert call_kwargs["days"] == 7
        assert call_kwargs["limit"] == 1000

    @patch("agent.governance_ui.data_access.monitoring.read_audit_events", return_value=[])
    def test_filters_passed(self, mock_read):
        client.get("/api/monitor/events?event_type=violation&severity=CRITICAL")
        call_kwargs = mock_read.call_args[1]
        assert call_kwargs["event_type"] == "violation"
        assert call_kwargs["severity"] == "CRITICAL"
