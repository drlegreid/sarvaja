"""
Session Metrics Dashboard View.

Per SESSION-METRICS-01-v1: Session analytics UI.
Per GAP-SESSION-METRICS-UI Phase 4: View component.
Per RULE-012: Single Responsibility - only session metrics UI.
Per DOC-SIZE-01-v1: Search & timeline tabs in metrics_view_tabs.py.

Shows:
- Summary with stat cards and per-day table
- Session content search
- Activity timeline
- Tool breakdown
"""

from trame.widgets import vuetify3 as v3, html

from .metrics_view_tabs import build_search_tab, build_timeline_tab  # noqa: F401


def build_metrics_header() -> None:
    """Build metrics dashboard header with filters."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-chart-line", classes="mr-2")
        html.Span("Session Metrics")
        v3.VSpacer()
        v3.VSelect(
            v_model="metrics_days_filter",
            items=("metrics_days_options",),
            label="Days",
            variant="outlined",
            density="compact",
            hide_details=True,
            style="max-width: 120px",
            update_modelValue="trigger('load_metrics_data')",
            __properties=["data-testid"],
            **{"data-testid": "metrics-days-filter"}
        )
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            classes="ml-2",
            click="trigger('load_metrics_data')",
            loading=("metrics_loading",),
            __properties=["data-testid"],
            **{"data-testid": "metrics-refresh-btn"}
        )


def build_metrics_tabs() -> None:
    """Build tab navigation for metrics sub-views."""
    v3.VTabs(
        v_model="metrics_active_tab",
        color="primary",
        __properties=["data-testid"],
        **{"data-testid": "metrics-tabs"}
    )
    with v3.VTabs(
        v_model="metrics_active_tab",
        color="primary",
    ):
        v3.VTab(value="summary", text="Summary", prepend_icon="mdi-chart-box")
        v3.VTab(value="search", text="Search", prepend_icon="mdi-magnify")
        v3.VTab(value="timeline", text="Timeline", prepend_icon="mdi-timeline-text")


def build_stat_cards() -> None:
    """Build summary stat cards."""
    with v3.VRow(
        v_if="metrics_data && metrics_data.totals",
        __properties=["data-testid"],
        **{"data-testid": "metrics-stat-cards"}
    ):
        # Active time
        with v3.VCol(cols=12, sm=6, md=4, lg=2):
            with v3.VCard(variant="tonal", color="primary"):
                with v3.VCardText(classes="text-center"):
                    html.Div("Active Time", classes="text-caption text-grey")
                    html.Div(
                        "{{ metrics_data.totals.active_minutes || 0 }} min",
                        classes="text-h5 font-weight-bold"
                    )
        # Sessions
        with v3.VCol(cols=12, sm=6, md=4, lg=2):
            with v3.VCard(variant="tonal", color="success"):
                with v3.VCardText(classes="text-center"):
                    html.Div("Sessions", classes="text-caption text-grey")
                    html.Div(
                        "{{ metrics_data.totals.session_count || 0 }}",
                        classes="text-h5 font-weight-bold"
                    )
        # Messages
        with v3.VCol(cols=12, sm=6, md=4, lg=2):
            with v3.VCard(variant="tonal", color="info"):
                with v3.VCardText(classes="text-center"):
                    html.Div("Messages", classes="text-caption text-grey")
                    html.Div(
                        "{{ metrics_data.totals.message_count || 0 }}",
                        classes="text-h5 font-weight-bold"
                    )
        # Tool calls
        with v3.VCol(cols=12, sm=6, md=4, lg=2):
            with v3.VCard(variant="tonal", color="warning"):
                with v3.VCardText(classes="text-center"):
                    html.Div("Tool Calls", classes="text-caption text-grey")
                    html.Div(
                        "{{ metrics_data.totals.tool_calls || 0 }}",
                        classes="text-h5 font-weight-bold"
                    )
        # MCP calls
        with v3.VCol(cols=12, sm=6, md=4, lg=2):
            with v3.VCard(variant="tonal", color="secondary"):
                with v3.VCardText(classes="text-center"):
                    html.Div("MCP Calls", classes="text-caption text-grey")
                    html.Div(
                        "{{ metrics_data.totals.mcp_calls || 0 }}",
                        classes="text-h5 font-weight-bold"
                    )
        # Error rate
        with v3.VCol(cols=12, sm=6, md=4, lg=2):
            with v3.VCard(
                variant="tonal",
                color=(
                    "metrics_data.totals.error_rate > 0.05 ? 'error' : "
                    "metrics_data.totals.error_rate > 0.01 ? 'warning' : 'success'"
                ),
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div("Error Rate", classes="text-caption text-grey")
                    html.Div(
                        "{{ ((metrics_data.totals.error_rate || 0) * 100).toFixed(1) }}%",
                        classes="text-h5 font-weight-bold"
                    )


def build_per_day_table() -> None:
    """Build per-day metrics breakdown table."""
    with v3.VCard(
        v_if="metrics_data && metrics_data.days && metrics_data.days.length > 0",
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "metrics-per-day-table"}
    ):
        v3.VCardTitle("Per-Day Breakdown")
        with v3.VCardText():
            with v3.VTable(density="compact"):
                with html.Thead():
                    with html.Tr():
                        html.Th("Date")
                        html.Th("Active Min")
                        html.Th("Sessions")
                        html.Th("Messages")
                        html.Th("Tools")
                        html.Th("MCP")
                        html.Th("Errors")
                with html.Tbody():
                    with html.Tr(
                        v_for="day in metrics_data.days",
                        key="day.date"
                    ):
                        html.Td("{{ day.date }}")
                        html.Td("{{ day.active_minutes }}")
                        html.Td("{{ day.session_count }}")
                        html.Td("{{ day.message_count }}")
                        html.Td("{{ day.tool_calls }}")
                        html.Td("{{ day.mcp_calls }}")
                        html.Td("{{ day.api_errors }}")


def build_tool_breakdown() -> None:
    """Build tool usage breakdown."""
    with v3.VCard(
        v_if="metrics_data && metrics_data.tool_breakdown",
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "metrics-tool-breakdown"}
    ):
        v3.VCardTitle("Tool Usage Breakdown")
        with v3.VCardText():
            with v3.VTable(density="compact"):
                with html.Thead():
                    with html.Tr():
                        html.Th("Tool")
                        html.Th("Count")
                with html.Tbody():
                    with html.Tr(
                        v_for="(count, name) in metrics_data.tool_breakdown",
                        key="name"
                    ):
                        html.Td("{{ name }}")
                        html.Td("{{ count }}")


def build_summary_tab() -> None:
    """Build the summary tab content."""
    with html.Div(v_if="metrics_active_tab === 'summary'"):
        build_stat_cards()
        build_per_day_table()
        build_tool_breakdown()

        # Error state
        v3.VAlert(
            v_if="metrics_data && metrics_data.error",
            type="warning",
            density="compact",
            classes="mt-4",
            v_text="metrics_data.error",
            __properties=["data-testid"],
            **{"data-testid": "metrics-error"}
        )

        # Empty state
        v3.VAlert(
            v_if="!metrics_loading && !metrics_data",
            type="info",
            density="compact",
            classes="mt-4",
            text="No metrics data. Click Refresh to load session analytics.",
            __properties=["data-testid"],
            **{"data-testid": "metrics-empty"}
        )


def build_metrics_view() -> None:
    """Build the Session Metrics Dashboard view.

    Main entry point for the metrics view module.
    Per GAP-SESSION-METRICS-UI: Session analytics dashboard.
    """
    with v3.VCard(
        v_if="active_view === 'metrics'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "metrics-dashboard"}
    ):
        build_metrics_header()

        with v3.VCardText():
            # Loading indicator
            v3.VProgressLinear(
                v_if="metrics_loading",
                indeterminate=True,
                color="primary",
            )

            # Tab navigation
            build_metrics_tabs()

            # Tab content
            build_summary_tab()
            build_search_tab()
            build_timeline_tab()
