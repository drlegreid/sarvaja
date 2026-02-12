"""
Unit tests for Agent Observability Routes.

Per DOC-SIZE-01-v1: Tests for routes/agents/observability.py module.
Tests: status summary, stuck agents, file locks, heartbeat,
       lock acquire/release, merge conflicts, monitor events.
"""

import pytest
from unittest.mock import patch, MagicMock

_P = "governance.routes.agents.observability"


@pytest.fixture(autouse=True)
def _patch_flags():
    with patch(f"{_P}.AGENT_STATUS_AVAILABLE", True), \
         patch(f"{_P}.CONFLICT_CHECKER_AVAILABLE", True):
        yield


# ── status summary ──────────────────────────────────────────────


class TestGetAgentsStatusSummary:
    @pytest.mark.asyncio
    async def test_success_without_conflicts(self):
        from governance.routes.agents.observability import get_agents_status_summary
        summary = {"status": "OK", "alerts": [], "alert_count": 0}
        with patch(f"{_P}.get_agent_status_summary", create=True, return_value=summary), \
             patch(f"{_P}.CONFLICT_CHECKER_AVAILABLE", False):
            result = await get_agents_status_summary()
        assert result["status"] == "OK"

    @pytest.mark.asyncio
    async def test_success_with_conflicts(self):
        from governance.routes.agents.observability import get_agents_status_summary
        summary = {"status": "OK", "alerts": [], "alert_count": 0}
        conflict = {
            "conflicts": ["file.py"], "conflict_count": 1,
            "has_conflicts": True, "alerts": [{"msg": "conflict"}],
        }
        with patch(f"{_P}.get_agent_status_summary", create=True, return_value=summary), \
             patch(f"{_P}.get_conflict_summary", create=True, return_value=conflict):
            result = await get_agents_status_summary()
        assert result["status"] == "CRITICAL"
        assert result["conflict_count"] == 1

    @pytest.mark.asyncio
    async def test_no_conflicts_present(self):
        from governance.routes.agents.observability import get_agents_status_summary
        summary = {"status": "OK", "alerts": [], "alert_count": 0}
        conflict = {
            "conflicts": [], "conflict_count": 0,
            "has_conflicts": False, "alerts": [],
        }
        with patch(f"{_P}.get_agent_status_summary", create=True, return_value=summary), \
             patch(f"{_P}.get_conflict_summary", create=True, return_value=conflict):
            result = await get_agents_status_summary()
        assert result["status"] == "OK"
        assert result["conflict_count"] == 0

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from governance.routes.agents.observability import get_agents_status_summary
        with patch(f"{_P}.AGENT_STATUS_AVAILABLE", False):
            result = await get_agents_status_summary()
        assert result["status"] == "UNAVAILABLE"


# ── stuck agents ────────────────────────────────────────────────


class TestGetStuckAgents:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import get_stuck_agents
        with patch(f"{_P}.check_stuck_agents", create=True, return_value=["agent-1"]):
            result = await get_stuck_agents()
        assert result["stuck_agents"] == ["agent-1"]

    @pytest.mark.asyncio
    async def test_empty(self):
        from governance.routes.agents.observability import get_stuck_agents
        with patch(f"{_P}.check_stuck_agents", create=True, return_value=[]):
            result = await get_stuck_agents()
        assert result["stuck_agents"] == []

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from governance.routes.agents.observability import get_stuck_agents
        with patch(f"{_P}.AGENT_STATUS_AVAILABLE", False):
            result = await get_stuck_agents()
        assert "error" in result


# ── file locks ──────────────────────────────────────────────────


class TestGetStaleLocks:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import get_stale_locks
        with patch(f"{_P}.check_file_locks", create=True, return_value=[{"file": "a.py"}]):
            result = await get_stale_locks()
        assert len(result["stale_locks"]) == 1

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from governance.routes.agents.observability import get_stale_locks
        with patch(f"{_P}.AGENT_STATUS_AVAILABLE", False):
            result = await get_stale_locks()
        assert "error" in result


# ── heartbeat ───────────────────────────────────────────────────


class TestAgentHeartbeat:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import agent_heartbeat
        with patch(f"{_P}.update_agent_heartbeat", create=True, return_value={"ok": True}):
            result = await agent_heartbeat(agent_id="agent-1", agent_type="code")
        assert result["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_with_task(self):
        from governance.routes.agents.observability import agent_heartbeat
        with patch(f"{_P}.update_agent_heartbeat", create=True, return_value={"ok": True}):
            result = await agent_heartbeat(
                agent_id="agent-1", current_task="TASK-1",
            )
        assert result["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        from governance.routes.agents.observability import agent_heartbeat
        with patch(f"{_P}.AGENT_STATUS_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await agent_heartbeat(agent_id="agent-1")
            assert exc.value.status_code == 503


# ── lock acquire ────────────────────────────────────────────────


class TestAcquireLock:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import acquire_lock
        with patch(f"{_P}.acquire_file_lock", create=True, return_value="/tmp/lock"):
            result = await acquire_lock(resource="file.py", agent_id="a-1")
        assert result["acquired"] is True

    @pytest.mark.asyncio
    async def test_conflict(self):
        from fastapi import HTTPException
        from governance.routes.agents.observability import acquire_lock
        with patch(f"{_P}.acquire_file_lock", create=True, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await acquire_lock(resource="file.py", agent_id="a-1")
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        from governance.routes.agents.observability import acquire_lock
        with patch(f"{_P}.AGENT_STATUS_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await acquire_lock(resource="file.py", agent_id="a-1")
            assert exc.value.status_code == 503


# ── lock release ────────────────────────────────────────────────


class TestReleaseLock:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import release_lock
        with patch(f"{_P}.release_file_lock", create=True, return_value=True):
            result = await release_lock(resource="file.py", agent_id="a-1")
        assert result["released"] is True

    @pytest.mark.asyncio
    async def test_not_found(self):
        from fastapi import HTTPException
        from governance.routes.agents.observability import release_lock
        with patch(f"{_P}.release_file_lock", create=True, return_value=False):
            with pytest.raises(HTTPException) as exc:
                await release_lock(resource="file.py", agent_id="a-1")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        from governance.routes.agents.observability import release_lock
        with patch(f"{_P}.AGENT_STATUS_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await release_lock(resource="file.py", agent_id="a-1")
            assert exc.value.status_code == 503


# ── merge conflicts ─────────────────────────────────────────────


class TestGetMergeConflicts:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import get_merge_conflicts
        data = {"has_conflicts": True, "conflicts": ["a.py"]}
        with patch(f"{_P}.get_conflict_summary", create=True, return_value=data):
            result = await get_merge_conflicts()
        assert result["has_conflicts"] is True

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from governance.routes.agents.observability import get_merge_conflicts
        with patch(f"{_P}.CONFLICT_CHECKER_AVAILABLE", False):
            result = await get_merge_conflicts()
        assert result["status"] == "UNAVAILABLE"


# ── monitor events ──────────────────────────────────────────────


_MONITOR_P = "agent.governance_ui.data_access.monitoring"


class TestGetMonitorEvents:
    @pytest.mark.asyncio
    async def test_success(self):
        from governance.routes.agents.observability import get_monitor_events
        events = [{"type": "alert", "severity": "INFO"}]
        with patch(f"{_MONITOR_P}.read_audit_events", return_value=events):
            result = await get_monitor_events()
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_with_filters(self):
        from governance.routes.agents.observability import get_monitor_events
        with patch(f"{_MONITOR_P}.read_audit_events", return_value=[]) as mock:
            result = await get_monitor_events(
                days=3, limit=50, event_type="alert", severity="CRITICAL",
            )
        assert result["filters"]["days"] == 3
        assert result["filters"]["severity"] == "CRITICAL"
        mock.assert_called_once_with(days=3, limit=50, event_type="alert", severity="CRITICAL")

    @pytest.mark.asyncio
    async def test_clamps_days(self):
        from governance.routes.agents.observability import get_monitor_events
        with patch(f"{_MONITOR_P}.read_audit_events", return_value=[]) as mock:
            await get_monitor_events(days=99, limit=5000)
        mock.assert_called_once_with(days=7, limit=1000, event_type=None, severity=None)
