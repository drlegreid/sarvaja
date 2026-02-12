"""
Unit tests for Session Visibility Routes.

Per DOC-SIZE-01-v1: Tests for governance/routes/agents/visibility.py.
Tests: get_visibility, get_tokens, get_task_rules, start_visibility_session,
       start_task_tracking, record_task_rule, record_task_tool_call,
       complete_task_tracking — both available and unavailable paths.
"""

from unittest.mock import patch, MagicMock
from dataclasses import dataclass

import pytest


_P = "governance.routes.agents.visibility"


@pytest.fixture()
def _available():
    """Patch SESSION_VISIBILITY_AVAILABLE = True with mocked functions."""
    mocks = {
        f"{_P}.SESSION_VISIBILITY_AVAILABLE": True,
        f"{_P}.get_session_visibility": MagicMock(return_value={"active_tasks": 2}),
        f"{_P}.get_token_usage_report": MagicMock(return_value={"total_tokens": 1000}),
        f"{_P}.get_task_rules_summary": MagicMock(return_value={"rules": ["R-1"]}),
        f"{_P}.vis_start_session": MagicMock(return_value={"session_id": "S-1"}),
        f"{_P}.vis_start_task": MagicMock(),
        f"{_P}.record_rule_application": MagicMock(),
        f"{_P}.vis_record_tool_call": MagicMock(),
        f"{_P}.vis_complete_task": MagicMock(),
    }
    with patch.multiple("", **{k: v for k, v in mocks.items()}, create=True):
        yield mocks


@pytest.fixture()
def _unavailable():
    """Patch SESSION_VISIBILITY_AVAILABLE = False."""
    with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
        yield


# ── get_visibility ────────────────────────────────────────────


class TestGetVisibility:
    @pytest.mark.asyncio
    async def test_available(self):
        mock_fn = MagicMock(return_value={"active_tasks": 2})
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.get_session_visibility", mock_fn):
            from governance.routes.agents.visibility import get_visibility
            result = await get_visibility()
        assert result == {"active_tasks": 2}

    @pytest.mark.asyncio
    async def test_unavailable(self):
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import get_visibility
            result = await get_visibility()
        assert result["status"] == "UNAVAILABLE"


# ── get_tokens ────────────────────────────────────────────────


class TestGetTokens:
    @pytest.mark.asyncio
    async def test_available(self):
        mock_fn = MagicMock(return_value={"total_tokens": 500})
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.get_token_usage_report", mock_fn):
            from governance.routes.agents.visibility import get_tokens
            result = await get_tokens()
        assert result["total_tokens"] == 500

    @pytest.mark.asyncio
    async def test_unavailable(self):
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import get_tokens
            result = await get_tokens()
        assert "error" in result


# ── get_task_rules ────────────────────────────────────────────


class TestGetTaskRules:
    @pytest.mark.asyncio
    async def test_available(self):
        mock_fn = MagicMock(return_value={"rules": ["R-1"]})
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.get_task_rules_summary", mock_fn):
            from governance.routes.agents.visibility import get_task_rules
            result = await get_task_rules("T-1")
        mock_fn.assert_called_once_with("T-1")
        assert result["rules"] == ["R-1"]

    @pytest.mark.asyncio
    async def test_unavailable(self):
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import get_task_rules
            result = await get_task_rules("T-1")
        assert "error" in result


# ── start_visibility_session ──────────────────────────────────


class TestStartVisibilitySession:
    @pytest.mark.asyncio
    async def test_available(self):
        mock_fn = MagicMock(return_value={"session_id": "S-1"})
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.vis_start_session", mock_fn):
            from governance.routes.agents.visibility import start_visibility_session
            result = await start_visibility_session("S-1")
        assert result["session_id"] == "S-1"

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import start_visibility_session
            with pytest.raises(HTTPException) as exc_info:
                await start_visibility_session("S-1")
        assert exc_info.value.status_code == 503


# ── start_task_tracking ───────────────────────────────────────


class TestStartTaskTracking:
    @pytest.mark.asyncio
    async def test_available(self):
        @dataclass
        class FakeTask:
            task_id: str = "T-1"
            task_name: str = "Test"

        mock_fn = MagicMock(return_value=FakeTask())
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.vis_start_task", mock_fn):
            from governance.routes.agents.visibility import start_task_tracking
            result = await start_task_tracking("T-1", "Test Task")
        assert result["task_id"] == "T-1"

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import start_task_tracking
            with pytest.raises(HTTPException):
                await start_task_tracking("T-1", "Test")


# ── record_task_rule ──────────────────────────────────────────


class TestRecordTaskRule:
    @pytest.mark.asyncio
    async def test_available(self):
        mock_fn = MagicMock()
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.record_rule_application", mock_fn):
            from governance.routes.agents.visibility import record_task_rule
            result = await record_task_rule("T-1", "R-1", "context")
        assert result["recorded"] is True
        mock_fn.assert_called_once_with("T-1", "R-1", "context")

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import record_task_rule
            with pytest.raises(HTTPException):
                await record_task_rule("T-1", "R-1")


# ── record_task_tool_call ─────────────────────────────────────


class TestRecordTaskToolCall:
    @pytest.mark.asyncio
    async def test_available(self):
        mock_fn = MagicMock()
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.vis_record_tool_call", mock_fn):
            from governance.routes.agents.visibility import record_task_tool_call
            result = await record_task_tool_call(
                "T-1", "Read", duration_ms=100, rules_applied="R-1,R-2", tokens=50,
            )
        assert result["recorded"] is True
        mock_fn.assert_called_once_with("T-1", "Read", 100, ["R-1", "R-2"], 50)

    @pytest.mark.asyncio
    async def test_empty_rules(self):
        mock_fn = MagicMock()
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.vis_record_tool_call", mock_fn):
            from governance.routes.agents.visibility import record_task_tool_call
            await record_task_tool_call("T-1", "Bash")
        mock_fn.assert_called_once_with("T-1", "Bash", 0, [], 0)

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import record_task_tool_call
            with pytest.raises(HTTPException):
                await record_task_tool_call("T-1", "Read")


# ── complete_task_tracking ────────────────────────────────────


class TestCompleteTaskTracking:
    @pytest.mark.asyncio
    async def test_available_found(self):
        mock_fn = MagicMock(return_value={"task_id": "T-1", "status": "completed"})
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.vis_complete_task", mock_fn):
            from governance.routes.agents.visibility import complete_task_tracking
            result = await complete_task_tracking("T-1")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_available_not_found(self):
        from fastapi import HTTPException
        mock_fn = MagicMock(return_value=None)
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", True), \
             patch(f"{_P}.vis_complete_task", mock_fn):
            from governance.routes.agents.visibility import complete_task_tracking
            with pytest.raises(HTTPException) as exc_info:
                await complete_task_tracking("T-MISS")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_unavailable(self):
        from fastapi import HTTPException
        with patch(f"{_P}.SESSION_VISIBILITY_AVAILABLE", False):
            from governance.routes.agents.visibility import complete_task_tracking
            with pytest.raises(HTTPException):
                await complete_task_tracking("T-1")
