"""
Enhanced Session Timeline with Plotly.

Per F.3 upgrade: D3-level interactive session timeline visualization.
Falls back to VSparkline if trame-plotly is not available.

Uses trame-plotly for:
- Interactive bar chart with hover tooltips
- Color-coded status (green=COMPLETED, blue=ACTIVE)
- Click to filter table by date
- Stacked bars showing status breakdown per day

Created: 2026-02-11
"""

import logging

logger = logging.getLogger(__name__)

# Check if trame-plotly is available
_HAS_PLOTLY = False
try:
    from trame.widgets import plotly as tw_plotly
    _HAS_PLOTLY = True
except ImportError:
    logger.debug("trame-plotly not installed, using VSparkline fallback")


def compute_timeline_plotly_data(sessions: list) -> dict:
    """Compute Plotly-compatible timeline data from sessions.

    Returns a dict with Plotly figure data (traces + layout) for
    a stacked bar chart of session activity by day.

    Args:
        sessions: List of session dicts with start_time and status fields.

    Returns:
        Dict with 'data' (list of traces) and 'layout' (dict) for Plotly.
    """
    from collections import Counter, defaultdict
    from datetime import datetime, timedelta

    # Count sessions per day per status
    status_per_day = defaultdict(Counter)
    for s in sessions:
        start = s.get("start_time", "")
        status = s.get("status", "UNKNOWN")
        if start:
            try:
                date_str = start[:10]
                status_per_day[date_str][status] += 1
            except Exception:
                pass

    # Build last 14 days
    today = datetime.now()
    dates = []
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)

    # Build traces per status
    completed_counts = [status_per_day[d].get("COMPLETED", 0) for d in dates]
    active_counts = [status_per_day[d].get("ACTIVE", 0) for d in dates]
    date_labels = [d[5:] for d in dates]  # MM-DD format

    traces = [
        {
            "x": date_labels,
            "y": completed_counts,
            "name": "Completed",
            "type": "bar",
            "marker": {"color": "#4CAF50"},
        },
        {
            "x": date_labels,
            "y": active_counts,
            "name": "Active",
            "type": "bar",
            "marker": {"color": "#2196F3"},
        },
    ]

    layout = {
        "barmode": "stack",
        "height": 120,
        "margin": {"l": 30, "r": 10, "t": 10, "b": 30},
        "showlegend": True,
        "legend": {"orientation": "h", "y": 1.15, "x": 0},
        "xaxis": {"tickfont": {"size": 10}},
        "yaxis": {"tickfont": {"size": 10}, "dtick": 1},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    return {"data": traces, "layout": layout}


def build_plotly_timeline():
    """Build the Plotly-based interactive timeline.

    Only renders if trame-plotly is installed. Otherwise, does nothing
    (caller should use VSparkline fallback).
    """
    if not _HAS_PLOTLY:
        return False

    from trame.widgets import html

    with html.Div(
        v_if="sessions_plotly_timeline && sessions_plotly_timeline.data",
        classes="mb-2",
    ):
        html.Div("Session Activity (14 days)", classes="text-caption text-grey mb-1")
        tw_plotly.Figure(
            display_mode_bar=False,
            data=("sessions_plotly_timeline.data",),
            layout=("sessions_plotly_timeline.layout",),
        )
    return True


def has_plotly() -> bool:
    """Check if Plotly timeline is available."""
    return _HAS_PLOTLY
