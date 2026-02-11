"""
Unit tests for API Startup Handlers.

Per DOC-SIZE-01-v1: Tests for extracted api_startup.py module.
Tests: cleanup_orphaned_chat_sessions, _module_exists,
       _check_service_integration, seed_data.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from governance.api_startup import (
    cleanup_orphaned_chat_sessions,
    seed_data,
    _module_exists,
    _check_service_integration,
)


class TestModuleExists:
    """Tests for _module_exists()."""

    def test_existing_module(self):
        assert _module_exists("json") is True

    def test_nonexistent_module(self):
        assert _module_exists("nonexistent_module_xyz_123") is False

    def test_governance_module(self):
        assert _module_exists("governance.services.tasks") is True


class TestCheckServiceIntegration:
    """Tests for _check_service_integration()."""

    def test_existing_returns_service_layer(self):
        result = _check_service_integration("governance.services.tasks")
        assert result == "SERVICE_LAYER"

    def test_missing_returns_direct_typedb(self):
        result = _check_service_integration("nonexistent_module_xyz")
        assert result == "DIRECT_TYPEDB"


class TestCleanupOrphanedChatSessions:
    """Tests for cleanup_orphaned_chat_sessions()."""

    @pytest.mark.asyncio
    async def test_cleans_in_memory_store(self):
        store = {
            "SESSION-2026-02-11-CHAT-TEST": {
                "status": "ACTIVE",
                "session_id": "SESSION-2026-02-11-CHAT-TEST",
            },
            "SESSION-2026-02-11-NON-CHAT": {
                "status": "ACTIVE",
                "session_id": "SESSION-2026-02-11-NON-CHAT",
            },
        }
        # The import is inside function body; patch at source module
        with patch(
            "governance.services.sessions.list_sessions",
            side_effect=Exception("skip TypeDB"),
        ):
            await cleanup_orphaned_chat_sessions(store)
        # CHAT session should be completed
        assert store["SESSION-2026-02-11-CHAT-TEST"]["status"] == "COMPLETED"
        # Non-CHAT should be untouched
        assert store["SESSION-2026-02-11-NON-CHAT"]["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_skips_completed(self):
        store = {
            "SESSION-2026-02-11-CHAT-DONE": {
                "status": "COMPLETED",
                "session_id": "SESSION-2026-02-11-CHAT-DONE",
            },
        }
        with patch(
            "governance.services.sessions.list_sessions",
            side_effect=Exception("skip"),
        ):
            await cleanup_orphaned_chat_sessions(store)
        assert store["SESSION-2026-02-11-CHAT-DONE"]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_empty_store(self):
        store = {}
        with patch(
            "governance.services.sessions.list_sessions",
            side_effect=Exception("skip"),
        ):
            await cleanup_orphaned_chat_sessions(store)
        assert len(store) == 0


class TestSeedData:
    """Tests for seed_data()."""

    @pytest.mark.asyncio
    @patch("governance.seed_data.seed_tasks_and_sessions")
    async def test_calls_seed(self, mock_seed):
        tasks = {}
        sessions = {}
        agents = {}
        await seed_data(tasks, sessions, agents)
        mock_seed.assert_called_once_with(tasks, sessions, agents)
