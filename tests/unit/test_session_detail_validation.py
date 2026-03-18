"""
Tests for session detail validation card and loader.

Per RELIABILITY-PLAN-01-v1 P1: Surface full session data in detail view.
"""
import inspect

import pytest
from unittest.mock import patch, MagicMock


class TestValidationCardComponent:
    """Tests for the validation card view component."""

    def test_build_validation_card_callable(self):
        from agent.governance_ui.views.sessions.validation_card import build_validation_card
        assert callable(build_validation_card)

    def test_validation_card_has_testid(self):
        from agent.governance_ui.views.sessions import validation_card
        source = inspect.getsource(validation_card)
        assert "session-validation-card" in source

    def test_validation_card_shows_tool_pairing(self):
        """Card displays tool call pairing metrics."""
        from agent.governance_ui.views.sessions import validation_card
        source = inspect.getsource(validation_card)
        assert "tool_calls_total" in source
        assert "orphaned_tool_calls" in source

    def test_validation_card_shows_mcp_distribution(self):
        """Card displays MCP server distribution chips."""
        from agent.governance_ui.views.sessions import validation_card
        source = inspect.getsource(validation_card)
        assert "mcp_server_distribution" in source
        assert "mcp-server-chip" in source

    def test_validation_card_shows_thinking_metrics(self):
        """Card displays thinking block count and chars."""
        from agent.governance_ui.views.sessions import validation_card
        source = inspect.getsource(validation_card)
        assert "thinking_blocks_total" in source
        assert "thinking_chars_total" in source

    def test_validation_card_shows_message_counts(self):
        """Card displays user and assistant message counts."""
        from agent.governance_ui.views.sessions import validation_card
        source = inspect.getsource(validation_card)
        assert "user_messages" in source
        assert "assistant_messages" in source

    def test_validation_card_shows_parse_errors(self):
        """Card displays parse error count."""
        from agent.governance_ui.views.sessions import validation_card
        source = inspect.getsource(validation_card)
        assert "parse_errors" in source


class TestValidationCardInDetail:
    """Tests for validation card integration in session detail."""

    def test_detail_imports_validation_card(self):
        from agent.governance_ui.views.sessions import detail
        source = inspect.getsource(detail)
        assert "validation_card" in source

    def test_detail_calls_build_validation_card(self):
        from agent.governance_ui.views.sessions import detail
        source = inspect.getsource(detail)
        assert "build_validation_card()" in source

    def test_validation_card_before_tool_calls(self):
        """Validation summary appears before tool calls drill-down."""
        from agent.governance_ui.views.sessions import detail
        source = inspect.getsource(detail.build_session_detail_view)
        val_pos = source.index("build_validation_card")
        tool_pos = source.index("build_tool_calls_card")
        assert val_pos < tool_pos


class TestValidationStateVariables:
    """Tests for validation-related state variables."""

    def test_initial_state_has_validation_data(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "session_validation_data" in state
        assert state["session_validation_data"] is None

    def test_initial_state_has_validation_loading(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "session_validation_loading" in state
        assert state["session_validation_loading"] is False


class TestValidationLoader:
    """Tests for the validation data loader function."""

    def test_loader_dict_has_load_validation(self):
        """Detail loaders return load_validation function."""
        state = MagicMock()
        loaders = _get_loaders(state)
        assert "load_validation" in loaders
        assert callable(loaders["load_validation"])

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx")
    def test_loader_sets_loading_state(self, mock_httpx):
        """Loader sets loading=True then False."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"valid": True, "entry_count": 10}
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        loaders = _get_loaders(state)
        loaders["load_validation"]("SESSION-2026-02-20-TEST")

        # Should have been set to True at start, False at end
        assert state.session_validation_loading is False

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx")
    def test_loader_stores_response_data(self, mock_httpx):
        """Loader stores API response in state."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        expected = {"valid": True, "entry_count": 504, "tool_calls_total": 177}
        mock_response.json.return_value = expected
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        loaders = _get_loaders(state)
        loaders["load_validation"]("SESSION-2026-02-20-TEST")
        assert state.session_validation_data == expected

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx")
    def test_loader_rejects_invalid_session_id(self, mock_httpx):
        """Loader skips invalid session IDs — no API call made."""
        state = MagicMock()
        loaders = _get_loaders(state)
        loaders["load_validation"]("../../etc/passwd")
        # Should NOT have called httpx.Client (rejected before HTTP)
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx")
    def test_loader_handles_api_failure(self, mock_httpx):
        """Loader gracefully handles API errors."""
        mock_httpx.Client.side_effect = Exception("connection refused")
        state = MagicMock()
        loaders = _get_loaders(state)
        loaders["load_validation"]("SESSION-2026-02-20-TEST")
        assert state.session_validation_data is None
        assert state.session_validation_loading is False


class TestSelectSessionCallsValidation:
    """Tests that select_session triggers validation loading."""

    def test_select_session_clears_validation_data(self):
        """select_session resets validation_data to None."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "session_validation_data = None" in source

    def test_select_session_calls_load_validation(self):
        """select_session calls loaders['load_validation']."""
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert 'loaders["load_validation"]' in source


def _get_loaders(state):
    """Helper to get loader functions from register_session_detail_loaders."""
    from agent.governance_ui.controllers.sessions_detail_loaders import (
        register_session_detail_loaders,
    )
    return register_session_detail_loaders(state, "http://test:8082")
