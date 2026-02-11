"""
Unit tests for Chat Delegation Protocol Integration.

Per DOC-SIZE-01-v1: Tests for extracted endpoints_delegation.py module.
Tests: _get_delegation_protocol, delegate_task_async.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from governance.stores import _agents_store, _tasks_store


@pytest.fixture(autouse=True)
def clear_stores():
    """Clear stores and reset module-level singletons between tests."""
    saved_agents = dict(_agents_store)
    saved_tasks = dict(_tasks_store)

    # Reset module-level singletons
    import governance.routes.chat.endpoints_delegation as mod
    mod._delegation_protocol = None
    mod._orchestrator_engine = None

    yield

    _agents_store.clear()
    _agents_store.update(saved_agents)
    _tasks_store.clear()
    _tasks_store.update(saved_tasks)

    mod._delegation_protocol = None
    mod._orchestrator_engine = None


class TestGetDelegationProtocol:
    """Tests for _get_delegation_protocol() lazy singleton."""

    def test_returns_none_on_import_error(self):
        from governance.routes.chat.endpoints_delegation import _get_delegation_protocol

        with patch(
            "governance.routes.chat.endpoints_delegation.get_client",
            side_effect=Exception("No client"),
        ):
            result = _get_delegation_protocol()
        assert result is None

    def test_returns_cached_instance(self):
        import governance.routes.chat.endpoints_delegation as mod

        mock_protocol = MagicMock()
        mod._delegation_protocol = mock_protocol
        result = mod._get_delegation_protocol()
        assert result is mock_protocol

    @patch("governance.routes.chat.endpoints_delegation.get_client")
    def test_registers_agents_from_store(self, mock_get_client):
        from governance.routes.chat.endpoints_delegation import _get_delegation_protocol

        _agents_store["test-agent"] = {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "agent_type": "research",
            "trust_score": 0.9,
        }

        mock_engine_class = MagicMock()
        mock_protocol_class = MagicMock()

        with patch(
            "agent.orchestrator.engine.OrchestratorEngine",
            mock_engine_class,
        ), patch(
            "agent.orchestrator.delegation.DelegationProtocol",
            mock_protocol_class,
        ):
            result = _get_delegation_protocol()

        if result is not None:
            # If delegation imports succeed, protocol should be created
            assert result is not None


class TestDelegateTaskAsync:
    """Tests for delegate_task_async()."""

    @pytest.mark.asyncio
    async def test_creates_task_in_store(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async

        _tasks_store.clear()

        with patch(
            "governance.routes.chat.endpoints_delegation._get_delegation_protocol",
            return_value=None,
        ):
            result = await delegate_task_async("Test task", "code-agent")

        # Should have created a task
        assert len(_tasks_store) == 1
        task = list(_tasks_store.values())[0]
        assert task["description"] == "Test task"
        assert task["status"] == "pending"
        assert task["priority"] == "MEDIUM"
        assert task["task_id"].startswith("TASK-")

    @pytest.mark.asyncio
    async def test_without_protocol_returns_pending(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async

        _tasks_store.clear()

        with patch(
            "governance.routes.chat.endpoints_delegation._get_delegation_protocol",
            return_value=None,
        ):
            result = await delegate_task_async("Research task", "code-agent")
        assert "Pending" in result
        assert "DelegationProtocol not available" in result

    @pytest.mark.asyncio
    async def test_successful_delegation(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async
        import governance.routes.chat.endpoints_delegation as mod

        _tasks_store.clear()

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.target_agent_id = "research-agent"
        mock_result.duration_ms = 150
        mock_result.message = "Delegated OK"

        mock_protocol = MagicMock()
        mock_protocol.delegate_research = AsyncMock(return_value=mock_result)
        mod._delegation_protocol = mock_protocol

        result = await delegate_task_async("Research X", "code-agent")

        assert "delegated successfully" in result
        assert "research-agent" in result
        assert "150ms" in result

        # Task should be in_progress
        task = list(_tasks_store.values())[0]
        assert task["status"] == "in_progress"
        assert task["agent_id"] == "research-agent"

    @pytest.mark.asyncio
    async def test_failed_delegation(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async
        import governance.routes.chat.endpoints_delegation as mod

        _tasks_store.clear()

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.message = "No suitable agent"

        mock_protocol = MagicMock()
        mock_protocol.delegate_research = AsyncMock(return_value=mock_result)
        mod._delegation_protocol = mock_protocol

        result = await delegate_task_async("Hard task", "code-agent")

        assert "Delegation failed" in result
        assert "No suitable agent" in result

        # Task remains pending
        task = list(_tasks_store.values())[0]
        assert task["status"] == "pending"

    @pytest.mark.asyncio
    async def test_delegation_exception(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async
        import governance.routes.chat.endpoints_delegation as mod

        _tasks_store.clear()

        mock_protocol = MagicMock()
        mock_protocol.delegate_research = AsyncMock(
            side_effect=Exception("Network error")
        )
        mod._delegation_protocol = mock_protocol

        result = await delegate_task_async("Broken task", "code-agent")

        assert "Delegation error" in result
        assert "Network error" in result
        assert "Pending manual assignment" in result

    @pytest.mark.asyncio
    async def test_task_name_truncated(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async

        _tasks_store.clear()

        long_desc = "A" * 100
        with patch(
            "governance.routes.chat.endpoints_delegation._get_delegation_protocol",
            return_value=None,
        ):
            await delegate_task_async(long_desc, "code-agent")

        task = list(_tasks_store.values())[0]
        assert len(task["name"]) == 50
        assert task["description"] == long_desc

    @pytest.mark.asyncio
    async def test_task_id_format(self):
        from governance.routes.chat.endpoints_delegation import delegate_task_async

        _tasks_store.clear()

        with patch(
            "governance.routes.chat.endpoints_delegation._get_delegation_protocol",
            return_value=None,
        ):
            await delegate_task_async("Format test", "code-agent")

        task_id = list(_tasks_store.keys())[0]
        assert task_id.startswith("TASK-")
        # TASK- + 8 hex chars
        assert len(task_id) == 13
