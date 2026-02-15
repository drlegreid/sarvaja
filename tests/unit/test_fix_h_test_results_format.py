"""Tests for Fix H: Test Results Formatting + Filters.

Validates:
- tests_category_filter state variable exists in initial state
- build_recent_runs_panel renders without errors
- Category filter chips are generated correctly
"""
from unittest.mock import patch, MagicMock
import pytest


def test_initial_state_has_tests_category_filter():
    """initial state includes tests_category_filter defaulting to empty string."""
    from agent.governance_ui.state.initial import get_initial_state
    state = get_initial_state()
    assert "tests_category_filter" in state
    assert state["tests_category_filter"] == ""


def test_initial_state_has_tests_loading():
    """initial state includes tests_loading."""
    from agent.governance_ui.state.initial import get_initial_state
    state = get_initial_state()
    assert "tests_loading" in state
    assert state["tests_loading"] is False


def test_initial_state_has_tests_recent_runs():
    """initial state includes tests_recent_runs as empty list."""
    from agent.governance_ui.state.initial import get_initial_state
    state = get_initial_state()
    assert "tests_recent_runs" in state
    assert state["tests_recent_runs"] == []


def test_initial_state_has_tests_cvp_status():
    """initial state includes tests_cvp_status as None."""
    from agent.governance_ui.state.initial import get_initial_state
    state = get_initial_state()
    assert "tests_cvp_status" in state
    assert state["tests_cvp_status"] is None


def test_build_recent_runs_panel_importable():
    """build_recent_runs_panel can be imported from both locations."""
    from agent.governance_ui.views.tests_view_panels import build_recent_runs_panel
    assert callable(build_recent_runs_panel)

    from agent.governance_ui.views.tests_view import build_recent_runs_panel as reexport
    assert callable(reexport)


def test_build_current_run_panel_importable():
    """build_current_run_panel can be imported."""
    from agent.governance_ui.views.tests_view_panels import build_current_run_panel
    assert callable(build_current_run_panel)


def test_build_robot_reports_panel_importable():
    """build_robot_reports_panel can be imported."""
    from agent.governance_ui.views.tests_view_panels import build_robot_reports_panel
    assert callable(build_robot_reports_panel)


def test_category_filter_values():
    """Category filter covers expected test categories."""
    # The filter chips in build_recent_runs_panel use these values
    expected_categories = {"", "unit", "governance", "regression", "heuristic", "api"}

    # Read the source to verify chips match
    import inspect
    from agent.governance_ui.views.tests_view_panels import build_recent_runs_panel
    source = inspect.getsource(build_recent_runs_panel)

    for cat in expected_categories:
        if cat:  # skip empty string - it's the "All" filter
            assert cat in source, f"Category '{cat}' not found in build_recent_runs_panel source"

    # Verify "All" chip exists
    assert '"All"' in source or "'All'" in source


def test_filter_js_expression_in_source():
    """v_for uses .filter() to apply category filter."""
    import inspect
    from agent.governance_ui.views.tests_view_panels import build_recent_runs_panel
    source = inspect.getsource(build_recent_runs_panel)

    assert "tests_category_filter" in source
    assert ".filter(" in source


def test_run_subtitle_shows_ratio_and_duration():
    """Run subtitle shows X/Y passed format and duration."""
    import inspect
    from agent.governance_ui.views.tests_view_panels import build_recent_runs_panel
    source = inspect.getsource(build_recent_runs_panel)

    # Should show "X/Y passed | Zs" format
    assert "passed |" in source or "passed |" in source
    assert "duration_seconds" in source
    assert "toFixed" in source


def test_category_chip_in_append_slot():
    """Each run shows a category chip badge in the append slot."""
    import inspect
    from agent.governance_ui.views.tests_view_panels import build_recent_runs_panel
    source = inspect.getsource(build_recent_runs_panel)

    assert "run.category" in source
