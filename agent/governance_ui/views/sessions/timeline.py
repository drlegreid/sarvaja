"""
Enhanced Session Timeline with Plotly.

Per F.3 upgrade: D3-level interactive session timeline visualization.
Falls back to VSparkline if trame-plotly is not available.

Uses trame-plotly for:
- Interactive bar chart with hover tooltips
- Color-coded status (green=COMPLETED, blue=ACTIVE)
- Stacked bars showing status breakdown per day

Created: 2026-02-11
"""

import logging

logger = logging.getLogger(__name__)

# Check if both plotly and trame-plotly are available
_HAS_PLOTLY = False
_plotly_widget = None
try:
    from trame.widgets import plotly as tw_plotly
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    logger.debug("trame-plotly or plotly not installed, using VSparkline fallback")


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
    earliest_date = None
    for s in sessions:
        start = s.get("start_time", "")
        status = s.get("status", "UNKNOWN")
        if start:
            try:
                date_str = start[:10]
                status_per_day[date_str][status] += 1
                if earliest_date is None or date_str < earliest_date:
                    earliest_date = date_str
            except Exception:
                pass

    # Adaptive date range: from earliest session to today, capped at 60 days
    today = datetime.now()
    if earliest_date:
        try:
            first = datetime.strptime(earliest_date, "%Y-%m-%d")
            span_days = (today - first).days
        except ValueError:
            span_days = 14
    else:
        span_days = 14
    span_days = max(7, min(span_days, 60))  # clamp 7..60

    dates = []
    for i in range(span_days, -1, -1):
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
        "height": 160,
        "margin": {"l": 40, "r": 10, "t": 30, "b": 35},
        "title": {"text": "Sessions per Day", "font": {"size": 12},
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


def _create_plotly_figure(figure_data: dict = None):
    """Create a plotly.graph_objects.Figure from timeline data dict."""
    if not _HAS_PLOTLY:
        return None
    if figure_data:
        return go.Figure(data=figure_data.get("data", []),
                         layout=figure_data.get("layout", {}))
    return go.Figure()


def build_plotly_timeline():
    """Build the Plotly-based interactive timeline widget.

    Creates an empty Plotly Figure widget at build time.
    Use update_plotly_timeline() to push data into it after loading.
    """
    global _plotly_widget
    if not _HAS_PLOTLY:
        return False

    try:
        from trame.widgets import html
        with html.Div(classes="mb-3", style="height: 200px; overflow: hidden"):
            _plotly_widget = tw_plotly.Figure(
                figure=go.Figure(),
                display_mode_bar=False,
                style="height: 190px; width: 100%",
            )
        return True
    except Exception as e:
        logger.warning("Plotly timeline build failed: %s, using VSparkline fallback", e)
        _plotly_widget = None
        return False


def update_plotly_timeline(figure_data: dict):
    """Update the Plotly timeline widget with new session data.

    Called by the sessions controller after loading session data.
    """
    global _plotly_widget
    if _plotly_widget is None or not _HAS_PLOTLY:
        return
    try:
        fig = _create_plotly_figure(figure_data)
        if fig:
            _plotly_widget.update(fig)
    except Exception as e:
        logger.debug("Plotly timeline update failed: %s", e)


def has_plotly() -> bool:
    """Check if Plotly timeline is available."""
    return _HAS_PLOTLY
