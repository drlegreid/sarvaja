"""
Unit tests for Governance Sync Agent.

Per DOC-SIZE-01-v1: Tests for agent/sync_agent/governance_sync.py module.
Tests: SyncResult, GovernanceSync — _call_mcp, get_sync_status,
       capture_tasks, link_rules_to_documents, get_pending_handoffs,
       complete_handoff, sync_all.
"""

from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import pytest

from agent.sync_agent.governance_sync import (
    GovernanceSync,
    SyncResult,
    SyncStatus,
)


# ── SyncResult ────────────────────────────────────────────────


class TestSyncResult:
    def test_defaults(self):
        r = SyncResult(success=True)
        assert r.tasks_synced == 0
        assert r.rules_linked == 0
        assert r.errors == []

    def test_errors_default_list(self):
        r = SyncResult(success=False)
        assert isinstance(r.errors, list)

    def test_errors_preserved(self):
        r = SyncResult(success=False, errors=["e1"])
        assert r.errors == ["e1"]


# ── _call_mcp ─────────────────────────────────────────────────


class TestCallMcp:
    @pytest.mark.asyncio
    async def test_get_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.sync_agent.governance_sync.httpx.AsyncClient", return_value=mock_client):
            sync = GovernanceSync()
            result = await sync._call_mcp("/api/test")
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_post_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"created": True}
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.sync_agent.governance_sync.httpx.AsyncClient", return_value=mock_client):
            sync = GovernanceSync()
            result = await sync._call_mcp("/api/test", method="POST", data={"a": 1})
        assert result == {"created": True}

    @pytest.mark.asyncio
    async def test_put_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"updated": True}
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.sync_agent.governance_sync.httpx.AsyncClient", return_value=mock_client):
            sync = GovernanceSync()
            result = await sync._call_mcp("/api/test", method="PUT", data={"b": 2})
        assert result == {"updated": True}

    @pytest.mark.asyncio
    async def test_non_200_returns_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.sync_agent.governance_sync.httpx.AsyncClient", return_value=mock_client):
            sync = GovernanceSync()
            result = await sync._call_mcp("/api/test")
        assert "error" in result
        assert result["status_code"] == 500

    @pytest.mark.asyncio
    async def test_exception_returns_error(self):
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.sync_agent.governance_sync.httpx.AsyncClient", return_value=mock_client):
            sync = GovernanceSync()
            result = await sync._call_mcp("/api/test")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unsupported_method(self):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agent.sync_agent.governance_sync.httpx.AsyncClient", return_value=mock_client):
            sync = GovernanceSync()
            result = await sync._call_mcp("/api/test", method="DELETE")
        assert "error" in result


# ── get_sync_status ───────────────────────────────────────────


class TestGetSyncStatus:
    @pytest.mark.asyncio
    async def test_all_synced(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={
            "rules": {"synced": True},
            "tasks": {"synced": True},
            "sessions": {"synced": True},
            "sync_needed": False,
            "timestamp": "2026-02-11T10:00:00",
        })
        status = await sync.get_sync_status()
        assert status.rules_synced is True
        assert status.sync_needed is False

    @pytest.mark.asyncio
    async def test_divergence(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={
            "rules": {"synced": False},
            "tasks": {"synced": True},
            "sessions": {"synced": True},
            "sync_needed": True,
            "timestamp": "2026-02-11T10:00:00",
        })
        status = await sync.get_sync_status()
        assert status.rules_synced is False
        assert status.sync_needed is True

    @pytest.mark.asyncio
    async def test_error_response(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"error": "connection refused"})
        status = await sync.get_sync_status()
        assert status.sync_needed is True
        assert "error" in status.details


# ── capture_tasks ─────────────────────────────────────────────


class TestCaptureTasks:
    @pytest.mark.asyncio
    async def test_success(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"inserted": 3, "updated": 2})
        result = await sync.capture_tasks()
        assert result.success is True
        assert result.tasks_synced == 5

    @pytest.mark.asyncio
    async def test_error(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"error": "failed"})
        result = await sync.capture_tasks()
        assert result.success is False
        assert "failed" in result.errors


# ── link_rules_to_documents ───────────────────────────────────


class TestLinkRulesToDocuments:
    @pytest.mark.asyncio
    async def test_success(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"relations_created": 5})
        result = await sync.link_rules_to_documents()
        assert result.success is True
        assert result.rules_linked == 5

    @pytest.mark.asyncio
    async def test_error(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"error": "no rules"})
        result = await sync.link_rules_to_documents()
        assert result.success is False


# ── get_pending_handoffs ──────────────────────────────────────


class TestGetPendingHandoffs:
    @pytest.mark.asyncio
    async def test_returns_handoffs(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"handoffs": [{"id": "H-1"}]})
        result = await sync.get_pending_handoffs()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_with_agent_filter(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"handoffs": []})
        await sync.get_pending_handoffs(for_agent="code-agent")
        sync._call_mcp.assert_called_with("/api/handoffs/pending?for_agent=code-agent")

    @pytest.mark.asyncio
    async def test_error_returns_empty(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"error": "fail"})
        result = await sync.get_pending_handoffs()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_response(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value=[{"id": "H-1"}])
        result = await sync.get_pending_handoffs()
        assert len(result) == 1


# ── complete_handoff ──────────────────────────────────────────


class TestCompleteHandoff:
    @pytest.mark.asyncio
    async def test_success(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"success": True})
        result = await sync.complete_handoff("T-1", "agent-a", "agent-b", "done")
        assert result is True

    @pytest.mark.asyncio
    async def test_failure(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value={"success": False})
        result = await sync.complete_handoff("T-1", "agent-a", "agent-b")
        assert result is False

    @pytest.mark.asyncio
    async def test_non_dict_response(self):
        sync = GovernanceSync()
        sync._call_mcp = AsyncMock(return_value="error string")
        result = await sync.complete_handoff("T-1", "a", "b")
        assert result is False


# ── sync_all ──────────────────────────────────────────────────


class TestSyncAll:
    @pytest.mark.asyncio
    async def test_all_succeed(self):
        sync = GovernanceSync()
        sync.capture_tasks = AsyncMock(return_value=SyncResult(success=True, tasks_synced=3))
        sync.link_rules_to_documents = AsyncMock(return_value=SyncResult(success=True, rules_linked=2))
        sync.get_pending_handoffs = AsyncMock(return_value=[{"id": "H-1"}])
        result = await sync.sync_all()
        assert result.success is True
        assert result.tasks_synced == 3
        assert result.rules_linked == 2
        assert result.handoffs_processed == 1

    @pytest.mark.asyncio
    async def test_with_errors(self):
        sync = GovernanceSync()
        sync.capture_tasks = AsyncMock(return_value=SyncResult(success=False, errors=["e1"]))
        sync.link_rules_to_documents = AsyncMock(return_value=SyncResult(success=True))
        sync.get_pending_handoffs = AsyncMock(return_value=[])
        result = await sync.sync_all()
        assert result.success is False
        assert "e1" in result.errors
