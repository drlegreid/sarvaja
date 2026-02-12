"""
Unit tests for Sync Agent Orchestrator.

Per DOC-SIZE-01-v1: Tests for agent/sync_agent/sync.py.
Tests: SyncAgent — init, _default_config, _init_transports, track_change,
       get_pending_changes, clear_pending, sync_once, stop.
"""

from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from agent.sync_agent.sync import SyncAgent
from agent.sync_agent.models import Change


# ── Init / Config ────────────────────────────────────────


class TestInit:
    def test_default_config(self):
        agent = SyncAgent()
        assert agent.config["sync"]["enabled"] is True
        assert "collections" in agent.config["sync"]
        assert agent.running is False
        assert agent.last_sync is None

    def test_custom_config(self):
        cfg = {"sync": {"enabled": False, "interval_seconds": 60, "transports": {}}}
        agent = SyncAgent(config=cfg)
        assert agent.config["sync"]["enabled"] is False

    def test_init_local_transport(self):
        cfg = {"sync": {"transports": {"local": {"base_path": "/tmp/sync"}}}}
        agent = SyncAgent(config=cfg)
        assert len(agent.transports) == 1

    def test_init_no_transports(self):
        cfg = {"sync": {"transports": {}}}
        agent = SyncAgent(config=cfg)
        assert agent.transports == []


# ── track_change / pending ───────────────────────────────


class TestTrackChange:
    def test_tracks_change(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.track_change("rules", "R-1", {"name": "test"})
        pending = agent.get_pending_changes()
        assert len(pending) == 1
        assert isinstance(pending[0], Change)
        assert pending[0].collection == "rules"
        assert pending[0].doc_id == "R-1"

    def test_overwrites_same_key(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.track_change("rules", "R-1", {"v": 1})
        agent.track_change("rules", "R-1", {"v": 2})
        assert len(agent.get_pending_changes()) == 1
        assert agent.get_pending_changes()[0].data == {"v": 2}

    def test_default_action_is_upsert(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.track_change("rules", "R-1", {})
        assert agent.get_pending_changes()[0].action == "upsert"

    def test_delete_action(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.track_change("rules", "R-1", {}, action="delete")
        assert agent.get_pending_changes()[0].action == "delete"


class TestClearPending:
    def test_clears(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.track_change("rules", "R-1", {})
        agent.clear_pending()
        assert agent.get_pending_changes() == []


# ── sync_once ────────────────────────────────────────────


class TestSyncOnce:
    @pytest.mark.asyncio
    async def test_no_transports(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        result = await agent.sync_once()
        assert result.changes_pushed == 0
        assert result.changes_pulled == 0
        assert result.errors == []
        assert agent.last_sync is not None

    @pytest.mark.asyncio
    async def test_with_transport_error(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        mock_transport = MagicMock()
        mock_transport.name = "test"
        mock_transport.pull = AsyncMock(side_effect=Exception("pull failed"))
        agent.transports = [mock_transport]

        result = await agent.sync_once()
        assert len(result.errors) == 1
        assert "pull failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_pulls_and_pushes(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.track_change("rules", "R-1", {"name": "test"})

        mock_transport = MagicMock()
        mock_transport.name = "test"
        mock_transport.pull = AsyncMock(return_value=[])
        mock_transport.push = AsyncMock(return_value=1)
        agent.transports = [mock_transport]

        result = await agent.sync_once()
        assert result.changes_pushed == 1
        # Pending cleared on success
        assert agent.get_pending_changes() == []

    @pytest.mark.asyncio
    async def test_conflict_resolution(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        local_change = Change("rules", "R-1", "upsert", {"v": 1})
        agent._local_state["rules:R-1"] = local_change

        remote_change = Change("rules", "R-1", "upsert", {"v": 2})
        mock_transport = MagicMock()
        mock_transport.name = "test"
        mock_transport.pull = AsyncMock(return_value=[remote_change])
        mock_transport.push = AsyncMock(return_value=0)
        agent.transports = [mock_transport]

        result = await agent.sync_once()
        assert result.conflicts_resolved == 1


# ── stop ─────────────────────────────────────────────────


class TestStop:
    def test_stop(self):
        agent = SyncAgent(config={"sync": {"transports": {}}})
        agent.running = True
        agent.stop()
        assert agent.running is False
