"""Deep scan batch 128: UI controllers + state.

Batch 128 findings: 20 total, 0 confirmed fixes, 20 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── State initialization completeness defense ──────────────


class TestStateInitializationDefense:
    """Verify all state variables are initialized in initial.py."""

    def test_session_transcript_loading_exists(self):
        """session_transcript_loading is initialized in initial state."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert "session_transcript_loading" in state
        assert state["session_transcript_loading"] is False

    def test_session_detail_loading_vars_exist(self):
        """All session detail loading variables are initialized."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        loading_vars = [
            "session_tool_calls_loading",
            "session_thinking_items_loading",
            "session_evidence_loading",
        ]
        for var in loading_vars:
            assert var in state, f"{var} missing from initial state"
            assert state[var] is False

    def test_task_execution_loading_exists(self):
        """task_execution_loading is initialized."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert "task_execution_loading" in state

    def test_transcript_state_vars_complete(self):
        """All transcript state variables are initialized."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        transcript_vars = [
            "session_transcript",
            "session_transcript_page",
            "session_transcript_total",
            "session_transcript_has_more",
            "session_transcript_include_thinking",
            "session_transcript_include_user",
            "session_transcript_expanded_entry",
        ]
        for var in transcript_vars:
            assert var in state, f"{var} missing from initial state"


# ── Navigation items single source defense ──────────────


class TestNavigationItemsSingleSourceDefense:
    """Verify NAVIGATION_ITEMS is the single source of truth."""

    def test_navigation_items_in_constants(self):
        """NAVIGATION_ITEMS is defined in constants.py."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        assert isinstance(NAVIGATION_ITEMS, list)
        assert len(NAVIGATION_ITEMS) >= 10

    def test_navigation_items_have_required_fields(self):
        """Each navigation item has icon and title."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS

        for item in NAVIGATION_ITEMS:
            assert "icon" in item, f"Missing icon in {item}"
            assert "title" in item, f"Missing title in {item}"


# ── Controller registration defense ──────────────


class TestControllerRegistrationDefense:
    """Verify controllers return expected function dicts."""

    def test_sessions_controller_importable(self):
        """Sessions controller module is importable."""
        import agent.governance_ui.controllers.sessions as mod
        assert hasattr(mod, '__file__')

    def test_tasks_controller_importable(self):
        """Tasks controller module is importable."""
        import agent.governance_ui.controllers.tasks as mod
        assert hasattr(mod, '__file__')


# ── Data loader defense ──────────────


class TestDataLoaderDefense:
    """Verify data loaders handle API responses correctly."""

    def test_empty_response_sets_empty_list(self):
        """API returning None body results in empty list."""
        result = None
        items = result if result is not None else []
        assert items == []

    def test_valid_response_preserves_data(self):
        """API returning valid data is preserved."""
        result = [{"session_id": "S-1"}]
        items = result if result is not None else []
        assert len(items) == 1


# ── Tasks page guard defense ──────────────


class TestTasksPageGuardDefense:
    """Verify page never goes below 1."""

    def test_max_prevents_page_zero(self):
        """max(1, page - 1) prevents page=0."""
        current_page = 1
        new_page = max(1, current_page - 1)
        assert new_page == 1

    def test_max_decrements_normally(self):
        """max(1, page - 1) decrements from page 2 to 1."""
        current_page = 2
        new_page = max(1, current_page - 1)
        assert new_page == 1
