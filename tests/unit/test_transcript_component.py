"""
Component tests for session transcript feature (GAP-SESSION-TRANSCRIPT-001).

Tests the full data pipeline: state → loader → controller → UI bindings.
Verifies state transitions, loader behavior with mock API, and controller
trigger wiring across the transcript feature stack.
"""

import json
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from agent.governance_ui.state.initial import get_initial_state


# ---------- State Initialization ----------

class TestTranscriptStateInit:
    """Transcript state variables are properly initialized."""

    def test_initial_state_has_transcript_vars(self):
        state = get_initial_state()
        assert state["session_transcript"] == []
        assert state["session_transcript_loading"] is False
        assert state["session_transcript_page"] == 1
        assert state["session_transcript_total"] == 0
        assert state["session_transcript_has_more"] is False
        assert state["session_transcript_include_thinking"] is True
        assert state["session_transcript_include_user"] is True
        assert state["session_transcript_expanded_entry"] is None

    def test_transcript_state_independent_per_call(self):
        """Factory returns fresh state each call (no shared refs)."""
        s1 = get_initial_state()
        s2 = get_initial_state()
        s1["session_transcript"].append({"test": True})
        assert len(s2["session_transcript"]) == 0


# ---------- Loader Registration ----------

_LOADERS_MOD = "agent.governance_ui.controllers.sessions_detail_loaders"


class TestTranscriptLoaderRegistration:
    """Transcript loaders are properly registered and callable."""

    def test_loader_dict_includes_transcript(self):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        state = MagicMock()
        loaders = register_session_detail_loaders(state, "http://localhost:8082")
        assert "load_transcript" in loaders
        assert "load_transcript_entry" in loaders
        assert callable(loaders["load_transcript"])
        assert callable(loaders["load_transcript_entry"])


# ---------- Transcript Loader Behavior ----------

class TestTranscriptLoaderBehavior:
    """Transcript loader properly calls API and populates state."""

    @pytest.fixture
    def state(self):
        s = MagicMock()
        s.session_transcript = []
        s.session_transcript_loading = False
        s.session_transcript_page = 1
        s.session_transcript_total = 0
        s.session_transcript_has_more = False
        s.session_transcript_include_thinking = True
        s.session_transcript_include_user = True
        s.session_transcript_expanded_entry = None
        return s

    @pytest.fixture
    def loaders(self, state):
        from agent.governance_ui.controllers.sessions_detail_loaders import (
            register_session_detail_loaders,
        )
        return register_session_detail_loaders(state, "http://localhost:8082")

    @patch(f"{_LOADERS_MOD}.httpx.Client")
    def test_load_transcript_populates_state_on_200(self, mock_client_cls, state, loaders):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entries": [
                {"index": 0, "entry_type": "user_prompt", "content": "hello"},
                {"index": 1, "entry_type": "assistant_text", "content": "hi"},
            ],
            "total": 2,
            "page": 1,
            "has_more": False,
        }
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders["load_transcript"]("SESSION-1")

        assert state.session_transcript == [
            {"index": 0, "entry_type": "user_prompt", "content": "hello"},
            {"index": 1, "entry_type": "assistant_text", "content": "hi"},
        ]
        assert state.session_transcript_total == 2
        assert state.session_transcript_has_more is False
        assert state.session_transcript_loading is False

    @patch(f"{_LOADERS_MOD}.httpx.Client")
    def test_load_transcript_handles_404_gracefully(self, mock_client_cls, state, loaders):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders["load_transcript"]("SESSION-1")

        assert state.session_transcript == []
        assert state.session_transcript_total == 0
        assert state.session_transcript_loading is False

    @patch(f"{_LOADERS_MOD}.httpx.Client")
    def test_load_transcript_handles_connection_error(self, mock_client_cls, state, loaders):
        mock_client_cls.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(side_effect=ConnectionError("down")))
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders["load_transcript"]("SESSION-1")

        assert state.session_transcript == []
        assert state.session_transcript_loading is False  # finally block

    def test_load_transcript_skips_when_no_session_id(self, state, loaders):
        loaders["load_transcript"](None)
        # Should return immediately without touching loading state
        assert state.session_transcript_loading is False

    @patch(f"{_LOADERS_MOD}.httpx.Client")
    def test_load_transcript_passes_filter_params(self, mock_client_cls, state, loaders):
        state.session_transcript_include_thinking = False
        state.session_transcript_include_user = False

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entries": [], "total": 0, "page": 1, "has_more": False,
        }
        mock_get = MagicMock(return_value=mock_resp)
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(get=mock_get))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders["load_transcript"]("SESSION-1", page=2)

        # Verify params were passed
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        assert params["page"] == 2
        assert params["include_thinking"] is False
        assert params["include_user"] is False

    @patch(f"{_LOADERS_MOD}.httpx.Client")
    def test_expand_entry_replaces_in_list(self, mock_client_cls, state, loaders):
        """Expanding an entry replaces it in the current transcript list."""
        state.session_transcript = [
            {"index": 0, "content": "truncated...", "is_truncated": True},
            {"index": 1, "content": "other"},
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "entry": {"index": 0, "content": "full expanded content", "is_truncated": False},
        }
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        loaders["load_transcript_entry"]("SESSION-1", 0)

        assert state.session_transcript[0]["content"] == "full expanded content"
        assert state.session_transcript[1]["content"] == "other"  # Unchanged
        assert state.session_transcript_expanded_entry == 0


# ---------- Controller Wiring ----------

class TestTranscriptControllerWiring:
    """Transcript triggers are wired in sessions controller."""

    def test_close_session_detail_resets_transcript_state(self):
        """close_session_detail clears all transcript state."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers

        source = inspect.getsource(register_sessions_controllers)
        assert "session_transcript = []" in source
        assert "session_transcript_page = 1" in source
        assert "session_transcript_total = 0" in source
        assert "session_transcript_expanded_entry = None" in source

    def test_select_session_loads_transcript(self):
        """select_session calls the transcript loader."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers

        source = inspect.getsource(register_sessions_controllers)
        assert 'loaders["load_transcript"](session_id)' in source

    def test_controller_has_transcript_triggers(self):
        """Controller registers pagination and toggle triggers."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers

        source = inspect.getsource(register_sessions_controllers)
        assert "load_transcript_page" in source
        assert "expand_transcript_entry" in source
        assert "toggle_transcript_thinking" in source
        assert "toggle_transcript_user" in source


# ---------- UI Component Structure ----------

class TestTranscriptUIComponent:
    """Transcript UI component renders expected structure."""

    def test_transcript_card_exports(self):
        """session_transcript.py exports build_session_transcript_card."""
        from agent.governance_ui.views.sessions.session_transcript import (
            build_session_transcript_card,
        )
        assert callable(build_session_transcript_card)

    def test_transcript_card_in_detail_view_imports(self):
        """detail.py imports and uses transcript card."""
        import inspect
        from agent.governance_ui.views.sessions.detail import build_session_detail_view

        source = inspect.getsource(build_session_detail_view)
        assert "build_session_transcript_card" in source

    def test_transcript_card_in_package_exports(self):
        """Package __init__.py exports the transcript card."""
        from agent.governance_ui.views.sessions import build_session_transcript_card
        assert callable(build_session_transcript_card)

    def test_entry_styles_cover_all_types(self):
        """All 6 entry types have styling definitions."""
        from agent.governance_ui.views.sessions.session_transcript import _ENTRY_STYLES

        expected_types = {
            "user_prompt", "assistant_text", "tool_use",
            "tool_result", "thinking", "compaction",
        }
        assert set(_ENTRY_STYLES.keys()) == expected_types

    def test_entry_styles_have_icon_and_color(self):
        """Each entry style has icon, color, indent, label."""
        from agent.governance_ui.views.sessions.session_transcript import _ENTRY_STYLES

        for entry_type, style in _ENTRY_STYLES.items():
            assert len(style) == 4, f"{entry_type} style tuple should have 4 elements"
            icon, color, indent, label = style
            assert icon.startswith("mdi-"), f"{entry_type} icon should start with mdi-"
            assert label, f"{entry_type} should have a label"


# ---------- Duration Fix Component Test ----------

class TestDurationFixComponent:
    """Session duration no longer shows 'invalid' for reversed timestamps."""

    def test_reversed_timestamps_show_duration(self):
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-14T00:07:18", "2026-02-13T22:09:29"
        )
        assert result != "invalid"
        assert result != ""
        assert "m" in result  # e.g., "1h 57m"

    def test_normal_timestamps_still_work(self):
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-14T10:00:00", "2026-02-14T11:30:00"
        )
        assert result == "1h 30m"

    def test_ongoing_session(self):
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration("2026-02-14T10:00:00", None)
        assert result == "ongoing"
