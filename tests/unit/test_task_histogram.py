"""
Tests for Task Histogram Plotly data computation.

Per EPIC-GOV-TASKS-V2 Phase 9e: Interactive stacked bar chart
by task_type (x-axis) and status (stacked colors).

TDD-first: these tests written BEFORE implementation.
Created: 2026-03-21
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TASK_TYPES = [
    "bug", "feature", "chore", "specification",
    "research", "gap", "epic", "test",
]
STATUSES = ["OPEN", "IN_PROGRESS", "DONE", "CLOSED"]
STATUS_COLORS = {
    "OPEN": "#FF9800",
    "IN_PROGRESS": "#2196F3",
    "DONE": "#4CAF50",
    "CLOSED": "#9E9E9E",
}


def _make_task(task_type=None, status="OPEN", task_id="T-1"):
    return {
        "task_id": task_id,
        "task_type": task_type,
        "status": status,
        "summary": f"Test task {task_id}",
    }


# ---------------------------------------------------------------------------
# TestHistogramData — pure function tests
# ---------------------------------------------------------------------------

class TestHistogramData:
    """compute_histogram_data() output shape and correctness."""

    def test_returns_data_and_layout(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([_make_task("bug")])
        assert "data" in result
        assert "layout" in result

    def test_one_trace_per_status(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([_make_task("bug")])
        assert len(result["data"]) == len(STATUSES)
        trace_names = {t["name"] for t in result["data"]}
        assert trace_names == set(STATUSES)

    def test_x_axis_contains_all_types_plus_unknown(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([_make_task("bug")])
        x_values = result["data"][0]["x"]
        for tt in TASK_TYPES:
            assert tt in x_values
        assert "unknown" in x_values

    def test_correct_count_single_type_single_status(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        tasks = [_make_task("bug", "OPEN", f"B-{i}") for i in range(3)]
        result = compute_histogram_data(tasks)
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        idx = open_trace["x"].index("bug")
        assert open_trace["y"][idx] == 3

    def test_correct_count_mixed_types_and_statuses(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        tasks = [
            _make_task("bug", "OPEN", "B-1"),
            _make_task("bug", "DONE", "B-2"),
            _make_task("feature", "OPEN", "F-1"),
            _make_task("feature", "OPEN", "F-2"),
            _make_task("feature", "CLOSED", "F-3"),
        ]
        result = compute_histogram_data(tasks)
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        done_trace = [t for t in result["data"] if t["name"] == "DONE"][0]
        closed_trace = [t for t in result["data"] if t["name"] == "CLOSED"][0]
        assert open_trace["y"][open_trace["x"].index("bug")] == 1
        assert open_trace["y"][open_trace["x"].index("feature")] == 2
        assert done_trace["y"][done_trace["x"].index("bug")] == 1
        assert closed_trace["y"][closed_trace["x"].index("feature")] == 1

    def test_empty_tasks_returns_zero_counts(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([])
        for trace in result["data"]:
            assert all(v == 0 for v in trace["y"])

    def test_null_task_type_counted_as_unknown(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        tasks = [_make_task(None, "OPEN", "N-1"), _make_task(None, "OPEN", "N-2")]
        result = compute_histogram_data(tasks)
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        idx = open_trace["x"].index("unknown")
        assert open_trace["y"][idx] == 2

    def test_layout_stacked_barmode(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([])
        assert result["layout"]["barmode"] == "stack"

    def test_layout_height(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([])
        assert result["layout"]["height"] == 180

    def test_traces_have_correct_colors(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([_make_task("bug")])
        for trace in result["data"]:
            expected = STATUS_COLORS[trace["name"]]
            assert trace["marker"]["color"] == expected

    def test_traces_have_bar_type(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([])
        for trace in result["data"]:
            assert trace["type"] == "bar"

    def test_customdata_contains_type_status_tuples(self):
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        tasks = [_make_task("bug", "OPEN")]
        result = compute_histogram_data(tasks)
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        assert "customdata" in open_trace
        idx = open_trace["x"].index("bug")
        cd = open_trace["customdata"][idx]
        assert cd["task_type"] == "bug"
        assert cd["status"] == "OPEN"


# ---------------------------------------------------------------------------
# TestHistogramFilter — click event parsing
# ---------------------------------------------------------------------------

class TestHistogramFilter:
    """extract_filter_from_click() for interactive bar filtering."""

    def test_valid_click_returns_filter(self):
        from agent.governance_ui.views.tasks.histogram import extract_filter_from_click
        click = {"points": [{"customdata": {"task_type": "bug", "status": "OPEN"}}]}
        result = extract_filter_from_click(click)
        assert result == {"task_type": "bug", "status": "OPEN"}

    def test_none_click_returns_none(self):
        from agent.governance_ui.views.tasks.histogram import extract_filter_from_click
        assert extract_filter_from_click(None) is None

    def test_empty_click_returns_none(self):
        from agent.governance_ui.views.tasks.histogram import extract_filter_from_click
        assert extract_filter_from_click({}) is None

    def test_no_points_returns_none(self):
        from agent.governance_ui.views.tasks.histogram import extract_filter_from_click
        assert extract_filter_from_click({"points": []}) is None

    def test_missing_customdata_returns_none(self):
        from agent.governance_ui.views.tasks.histogram import extract_filter_from_click
        assert extract_filter_from_click({"points": [{}]}) is None


# ---------------------------------------------------------------------------
# TestHistogramAvailability
# ---------------------------------------------------------------------------

class TestHistogramAvailability:
    """Plotly availability guard."""

    def test_has_plotly_returns_bool(self):
        from agent.governance_ui.views.tasks.histogram import has_plotly
        assert isinstance(has_plotly(), bool)

    def test_compute_works_without_plotly(self):
        """compute_histogram_data is pure — no Plotly dependency."""
        from agent.governance_ui.views.tasks.histogram import compute_histogram_data
        result = compute_histogram_data([_make_task("bug")])
        assert isinstance(result, dict)

    def test_extract_filter_works_without_plotly(self):
        """extract_filter_from_click is pure — no Plotly dependency."""
        from agent.governance_ui.views.tasks.histogram import extract_filter_from_click
        result = extract_filter_from_click(None)
        assert result is None
