"""TDD Tests: Loading state guarantees via finally blocks.

Validates that all session detail loaders use finally blocks
to guarantee loading flags are reset even on exceptions.
"""
import inspect

from unittest.mock import MagicMock, patch


class TestLoadingFinallyBlocks:
    """All loaders use finally to guarantee loading=False."""

    def test_tool_calls_has_finally(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        source = inspect.getsource(register_session_detail_loaders)
        idx = source.index("def load_session_tool_calls")
        next_def = source.index("def load_session_thinking_items")
        fn_source = source[idx:next_def]
        assert "finally:" in fn_source
        assert "session_tool_calls_loading = False" in fn_source

    def test_thinking_items_has_finally(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        source = inspect.getsource(register_session_detail_loaders)
        idx = source.index("def load_session_thinking_items")
        next_def = source.index("def build_session_timeline")
        fn_source = source[idx:next_def]
        assert "finally:" in fn_source
        assert "session_thinking_items_loading = False" in fn_source

    def test_evidence_rendered_has_finally(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        source = inspect.getsource(register_session_detail_loaders)
        idx = source.index("def load_session_evidence_rendered")
        # Find next def after this one (skip the "rendered" substring match)
        after_rendered = idx + len("def load_session_evidence_rendered")
        next_def = source.index("\n    def ", after_rendered)
        fn_source = source[idx:next_def]
        assert "finally:" in fn_source
        assert "session_evidence_loading = False" in fn_source

    def test_tasks_has_finally(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        source = inspect.getsource(register_session_detail_loaders)
        idx = source.index("def load_session_tasks")
        fn_source = source[idx:]
        assert "finally:" in fn_source
        assert "session_tasks_loading = False" in fn_source


class TestLoadingFlagsBehavioral:
    """Behavioral tests: loading flags reset on exception."""

    def _make_state(self):
        state = MagicMock()
        state.session_tool_calls = []
        state.session_tool_calls_loading = False
        state.session_thinking_items = []
        state.session_thinking_items_loading = False
        state.session_evidence_html = ''
        state.session_evidence_loading = False
        state.session_tasks = []
        state.session_tasks_loading = False
        state.selected_session = None
        return state

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx.Client")
    def test_tool_calls_loading_reset_on_error(self, mock_client_cls):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        state = self._make_state()
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders = register_session_detail_loaders(state, "http://test:8082")
        loaders["load_tool_calls"]("S-1")
        assert state.session_tool_calls_loading is False

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx.Client")
    def test_thinking_items_loading_reset_on_error(self, mock_client_cls):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        state = self._make_state()
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders = register_session_detail_loaders(state, "http://test:8082")
        loaders["load_thinking_items"]("S-1")
        assert state.session_thinking_items_loading is False

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx.Client")
    def test_evidence_rendered_loading_reset_on_error(self, mock_client_cls):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        state = self._make_state()
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders = register_session_detail_loaders(state, "http://test:8082")
        loaders["load_evidence_rendered"]("S-1")
        assert state.session_evidence_loading is False

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx.Client")
    def test_tasks_loading_reset_on_error(self, mock_client_cls):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        state = self._make_state()
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders = register_session_detail_loaders(state, "http://test:8082")
        loaders["load_tasks"]("S-1")
        assert state.session_tasks_loading is False

    @patch("agent.governance_ui.controllers.sessions_detail_loaders.httpx.Client")
    def test_tool_calls_loading_set_true_before_request(self, mock_client_cls):
        """Loading flag must be True before the network call starts."""
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        state = self._make_state()
        loading_captured = []

        original_enter = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"tool_calls": []}
        original_enter.get.return_value = resp

        def capture_enter(s):
            loading_captured.append(state.session_tool_calls_loading)
            return original_enter

        mock_client_cls.return_value.__enter__ = capture_enter
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders = register_session_detail_loaders(state, "http://test:8082")
        loaders["load_tool_calls"]("S-1")
        assert loading_captured[0] is True
        assert state.session_tool_calls_loading is False
