"""Deep scan batch 173: Navigation + views layer.

Batch 173 findings: 7 total, 0 confirmed fixes (all UI template issues
deferred — require visual verification via Playwright).
"""
import pytest
from pathlib import Path


# ── Navigation constants defense ──────────────


class TestNavigationConstantsDefense:
    """Verify navigation items are complete."""

    def test_navigation_items_count(self):
        """NAVIGATION_ITEMS has at least 16 items."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        assert len(NAVIGATION_ITEMS) >= 16

    def test_navigation_items_have_required_fields(self):
        """Each nav item has title, icon, value."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        for item in NAVIGATION_ITEMS:
            assert "title" in item, f"Missing title: {item}"
            assert "icon" in item, f"Missing icon: {item}"
            assert "value" in item, f"Missing value: {item}"

    def test_sessions_nav_exists(self):
        """Sessions navigation item exists."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        values = [item["value"] for item in NAVIGATION_ITEMS]
        assert "sessions" in values


# ── Task model defense ──────────────


class TestTaskModelDefense:
    """Verify TaskResponse has expected fields."""

    def test_task_response_has_description(self):
        """TaskResponse has description field (not 'name')."""
        from governance.models import TaskResponse
        fields = TaskResponse.model_fields
        assert "description" in fields

    def test_task_response_has_task_id(self):
        """TaskResponse has task_id field."""
        from governance.models import TaskResponse
        assert "task_id" in TaskResponse.model_fields

    def test_task_response_has_status(self):
        """TaskResponse has status field."""
        from governance.models import TaskResponse
        assert "status" in TaskResponse.model_fields


# ── Decision model defense ──────────────


class TestDecisionModelDefense:
    """Verify DecisionResponse and DecisionOption have expected fields."""

    def test_decision_response_has_rationale(self):
        """DecisionResponse has rationale field."""
        from governance.models import DecisionResponse
        assert "rationale" in DecisionResponse.model_fields

    def test_decision_response_has_selected_option(self):
        """DecisionResponse has selected_option field."""
        from governance.models import DecisionResponse
        assert "selected_option" in DecisionResponse.model_fields

    def test_decision_option_has_label(self):
        """DecisionOption has label field."""
        from governance.models import DecisionOption
        assert "label" in DecisionOption.model_fields


# ── UI utils defense ──────────────


class TestUIUtilsDefense:
    """Verify UI utility functions."""

    def test_compute_session_metrics_exists(self):
        """compute_session_metrics function exists."""
        from agent.governance_ui.utils import compute_session_metrics
        assert callable(compute_session_metrics)

    def test_compute_session_metrics_empty(self):
        """compute_session_metrics handles empty list."""
        from agent.governance_ui.utils import compute_session_metrics
        result = compute_session_metrics([])
        assert "duration" in result
        assert "avg_tasks" in result

    def test_compute_session_metrics_with_data(self):
        """compute_session_metrics computes from sessions."""
        from agent.governance_ui.utils import compute_session_metrics
        sessions = [
            {"start_time": "2026-02-15T10:00:00", "end_time": "2026-02-15T12:00:00",
             "tasks_completed": 5},
            {"start_time": "2026-02-15T13:00:00", "end_time": "2026-02-15T14:00:00",
             "tasks_completed": 10},
        ]
        result = compute_session_metrics(sessions)
        assert "duration" in result
        assert "avg_tasks" in result
