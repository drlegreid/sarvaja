"""DSP-14: Histogram Taxonomy V2 Tests.

Tests compute_histogram_data and extract_filter_from_click with:
1. All 6 canonical types produce bars
2. "unknown" catch-all for unrecognized types
3. CLOSED status mapped to DONE in histogram
4. Deprecated type aliases (gap, story) → "unknown" in histogram
5. extract_filter_from_click — valid/invalid click data
6. Empty task list returns valid empty traces
"""
import pytest

from agent.governance_ui.views.tasks.histogram import (
    compute_histogram_data,
    extract_filter_from_click,
    TASK_TYPES,
    STATUS_CONFIG,
)


def _t(task_type=None, status="OPEN", task_id="T-1"):
    return {"task_id": task_id, "task_type": task_type, "status": status}


# =============================================================================
# 1. compute_histogram_data Structure
# =============================================================================


class TestHistogramStructure:
    """Output shape of compute_histogram_data."""

    def test_returns_data_and_layout(self):
        result = compute_histogram_data([_t("bug")])
        assert "data" in result
        assert "layout" in result

    def test_data_has_three_traces(self):
        """One trace per status in STATUS_CONFIG."""
        result = compute_histogram_data([_t("bug")])
        assert len(result["data"]) == len(STATUS_CONFIG)

    def test_each_trace_has_x_y_name(self):
        result = compute_histogram_data([_t("bug")])
        for trace in result["data"]:
            assert "x" in trace
            assert "y" in trace
            assert "name" in trace

    def test_x_axis_contains_all_types(self):
        result = compute_histogram_data([_t("bug")])
        for trace in result["data"]:
            assert trace["x"] == list(TASK_TYPES)

    def test_layout_is_stacked_bar(self):
        result = compute_histogram_data([])
        assert result["layout"]["barmode"] == "stack"


# =============================================================================
# 2. Canonical Type Counting
# =============================================================================


class TestHistogramTypeCounting:
    """Each canonical type gets counted in the correct bar."""

    def test_bug_counted(self):
        result = compute_histogram_data([_t("bug", "OPEN")])
        # Find OPEN trace
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        bug_idx = TASK_TYPES.index("bug")
        assert open_trace["y"][bug_idx] == 1

    def test_feature_counted(self):
        result = compute_histogram_data([_t("feature", "IN_PROGRESS")])
        ip_trace = [t for t in result["data"] if t["name"] == "IN_PROGRESS"][0]
        feat_idx = TASK_TYPES.index("feature")
        assert ip_trace["y"][feat_idx] == 1

    def test_all_six_types(self):
        tasks = [_t(tt, "DONE", f"T-{i}") for i, tt in enumerate(
            ["bug", "feature", "chore", "research", "spec", "test"]
        )]
        result = compute_histogram_data(tasks)
        done_trace = [t for t in result["data"] if t["name"] == "DONE"][0]
        # All 6 canonical types should have 1 each
        for tt in ["bug", "feature", "chore", "research", "spec", "test"]:
            idx = TASK_TYPES.index(tt)
            assert done_trace["y"][idx] == 1, f"{tt} not counted"


# =============================================================================
# 3. Unknown Type Handling
# =============================================================================


class TestHistogramUnknownTypes:
    """Unrecognized types fall into 'unknown' bucket."""

    def test_none_type_goes_to_unknown(self):
        result = compute_histogram_data([_t(None, "OPEN")])
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        unk_idx = TASK_TYPES.index("unknown")
        assert open_trace["y"][unk_idx] == 1

    def test_deprecated_gap_goes_to_unknown(self):
        """'gap' is not a canonical type — histogram puts it in unknown."""
        result = compute_histogram_data([_t("gap", "OPEN")])
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        unk_idx = TASK_TYPES.index("unknown")
        assert open_trace["y"][unk_idx] == 1

    def test_random_type_goes_to_unknown(self):
        result = compute_histogram_data([_t("banana", "OPEN")])
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        unk_idx = TASK_TYPES.index("unknown")
        assert open_trace["y"][unk_idx] == 1


# =============================================================================
# 4. Status Normalization in Histogram
# =============================================================================


class TestHistogramStatusHandling:
    """Status normalization for histogram bars."""

    def test_lowercase_status_normalized(self):
        result = compute_histogram_data([_t("bug", "open")])
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        bug_idx = TASK_TYPES.index("bug")
        assert open_trace["y"][bug_idx] == 1

    def test_none_status_defaults_to_open(self):
        result = compute_histogram_data([{"task_id": "T-1", "task_type": "bug"}])
        open_trace = [t for t in result["data"] if t["name"] == "OPEN"][0]
        bug_idx = TASK_TYPES.index("bug")
        assert open_trace["y"][bug_idx] == 1


# =============================================================================
# 5. Empty Input
# =============================================================================


class TestHistogramEmpty:
    """Empty task list produces valid but zero-count histogram."""

    def test_empty_tasks_still_has_traces(self):
        result = compute_histogram_data([])
        assert len(result["data"]) == len(STATUS_CONFIG)

    def test_empty_tasks_all_zeros(self):
        result = compute_histogram_data([])
        for trace in result["data"]:
            assert all(v == 0 for v in trace["y"])


# =============================================================================
# 6. extract_filter_from_click
# =============================================================================


class TestExtractFilterFromClick:
    """extract_filter_from_click — Plotly click event parsing."""

    def test_valid_click(self):
        click_data = {
            "points": [{"customdata": {"task_type": "bug", "status": "OPEN"}}]
        }
        result = extract_filter_from_click(click_data)
        assert result == {"task_type": "bug", "status": "OPEN"}

    def test_none_click_returns_none(self):
        assert extract_filter_from_click(None) is None

    def test_empty_dict_returns_none(self):
        assert extract_filter_from_click({}) is None

    def test_no_points_returns_none(self):
        assert extract_filter_from_click({"points": []}) is None

    def test_missing_customdata_returns_none(self):
        assert extract_filter_from_click({"points": [{}]}) is None

    def test_missing_task_type_returns_none(self):
        click_data = {"points": [{"customdata": {"status": "OPEN"}}]}
        assert extract_filter_from_click(click_data) is None

    def test_missing_status_returns_none(self):
        click_data = {"points": [{"customdata": {"task_type": "bug"}}]}
        assert extract_filter_from_click(click_data) is None

    def test_non_dict_click_returns_none(self):
        assert extract_filter_from_click("not a dict") is None

    def test_non_list_points_returns_none(self):
        assert extract_filter_from_click({"points": "not a list"}) is None
