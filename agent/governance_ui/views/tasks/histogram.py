"""
Task Histogram with Plotly.

Per EPIC-GOV-TASKS-V2 Phase 9e: Interactive stacked bar chart showing
task distribution by type (x-axis) and status (stacked colors).

Follows the pattern of sessions/timeline.py exactly:
- Pure compute function (testable without Trame)
- Build-time widget registration
- Runtime update function
- Plotly import guard with graceful fallback

Created: 2026-03-21
"""

import logging

logger = logging.getLogger(__name__)

# Check if both plotly and trame-plotly are available
_HAS_PLOTLY = False
_histogram_widget = None
try:
    from trame.widgets import plotly as tw_plotly
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    logger.debug("trame-plotly or plotly not installed, histogram unavailable")


# Canonical type order (META-TAXON-02-v1 — EPIC-TASK-TAXONOMY-V2 Session 4)
TASK_TYPES = [
    "bug", "feature", "chore", "research", "spec", "test", "unknown",
]

# Status trace order and colors (CLOSED removed — normalized to DONE)
STATUS_CONFIG = [
    ("OPEN", "#FF9800"),
    ("IN_PROGRESS", "#2196F3"),
    ("DONE", "#4CAF50"),
]


def compute_histogram_data(tasks: list) -> dict:
    """Compute Plotly-compatible histogram data from tasks.

    Returns a dict with Plotly figure data (traces + layout) for
    a stacked bar chart of task counts by type and status.

    Args:
        tasks: List of task dicts with task_type and status fields.

    Returns:
        Dict with 'data' (list of traces) and 'layout' (dict).
    """
    from collections import Counter

    # Count tasks per (type, status)
    counts = Counter()
    for t in tasks:
        tt = t.get("task_type") or "unknown"
        if tt not in TASK_TYPES:
            tt = "unknown"
        status = (t.get("status") or "OPEN").upper()
        counts[(tt, status)] += 1

    # Build one trace per status
    traces = []
    for status, color in STATUS_CONFIG:
        y_values = [counts.get((tt, status), 0) for tt in TASK_TYPES]
        customdata = [{"task_type": tt, "status": status} for tt in TASK_TYPES]
        traces.append({
            "x": list(TASK_TYPES),
            "y": y_values,
            "name": status,
            "type": "bar",
            "marker": {"color": color},
            "customdata": customdata,
        })

    layout = {
        "barmode": "stack",
        "height": 180,
        "margin": {"l": 40, "r": 10, "t": 30, "b": 35},
        "title": {"text": "Tasks by Type", "font": {"size": 12},
                  "x": 0.01, "xanchor": "left"},
        "showlegend": True,
        "legend": {"orientation": "h", "y": 1.15, "x": 0, "yanchor": "bottom"},
        "xaxis": {"type": "category", "tickfont": {"size": 10}},
        "yaxis": {"tickfont": {"size": 10}, "dtick": 1,
                  "title": {"text": "Count", "font": {"size": 10}}},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    return {"data": traces, "layout": layout}


def extract_filter_from_click(click_data) -> dict | None:
    """Parse a Plotly bar click event into a filter payload.

    Args:
        click_data: Plotly click event dict with 'points' array.

    Returns:
        Dict with task_type and status, or None if invalid.
    """
    if not click_data or not isinstance(click_data, dict):
        return None
    points = click_data.get("points")
    if not points or not isinstance(points, list) or len(points) == 0:
        return None
    point = points[0]
    cd = point.get("customdata")
    if not cd or not isinstance(cd, dict):
        return None
    if "task_type" not in cd or "status" not in cd:
        return None
    return {"task_type": cd["task_type"], "status": cd["status"]}


def _create_plotly_figure(figure_data: dict = None):
    """Create a plotly.graph_objects.Figure from histogram data dict."""
    if not _HAS_PLOTLY:
        return None
    if figure_data:
        return go.Figure(data=figure_data.get("data", []),
                         layout=figure_data.get("layout", {}))
    return go.Figure()


def build_plotly_histogram():
    """Build the Plotly histogram widget with toggle button.

    Creates an empty Plotly Figure widget at build time.
    Use update_plotly_histogram() to push data after loading.

    The toggle button is embedded here to keep list.py under 300 lines.
    """
    global _histogram_widget
    if not _HAS_PLOTLY:
        return False

    try:
        from trame.widgets import html, vuetify3 as v3
        with html.Div(v_if="!is_loading"):
            # Toggle button
            v3.VBtn(
                icon=True,
                click="tasks_show_histogram = !tasks_show_histogram",
                density="compact",
                variant="text",
                classes="mb-1",
                children=[
                    v3.VIcon(
                        v_text=("tasks_show_histogram"
                                " ? 'mdi-chart-bar' : 'mdi-chart-bar-stacked'"),
                    ),
                ],
            )
            # Chart container
            with html.Div(
                v_if="tasks_show_histogram",
                classes="mb-2",
                style="height: 200px; overflow: hidden",
            ):
                _histogram_widget = tw_plotly.Figure(
                    figure=go.Figure(),
                    display_mode_bar=False,
                    style="height: 190px; width: 100%",
                )
        return True
    except Exception as e:
        logger.warning("Plotly histogram build failed: %s", e)
        _histogram_widget = None
        return False


def update_plotly_histogram(figure_data: dict):
    """Update the Plotly histogram widget with new task data.

    Called by the tasks controller after loading task data.
    """
    global _histogram_widget
    if _histogram_widget is None or not _HAS_PLOTLY:
        return
    try:
        fig = _create_plotly_figure(figure_data)
        if fig:
            _histogram_widget.update(fig)
    except Exception as e:
        logger.debug("Plotly histogram update failed: %s", e)


def has_plotly() -> bool:
    """Check if Plotly histogram is available."""
    return _HAS_PLOTLY
