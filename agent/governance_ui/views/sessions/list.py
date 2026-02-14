"""
Sessions List View Component.

Per RULE-012: Single Responsibility - only sessions list UI.
Per RULE-032: File size limit (<300 lines).
Per EPIC-F: Rich session UI features (filters, duration, timeline, pivot).
Per F.3 upgrade: Plotly timeline with VSparkline fallback.
"""

from trame.widgets import vuetify3 as v3, html
from agent.governance_ui.views.sessions.timeline import build_plotly_timeline, has_plotly


def _build_metrics_row():
    """Session metrics summary cards."""
    with v3.VRow(dense=True, classes="mb-2"):
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div("{{ sessions_pagination.total || sessions.length || 0 }}", classes="text-h6")
                html.Div("Total Sessions", classes="text-caption")
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div("{{ sessions.filter(s => s.status === 'ACTIVE').length || 0 }}", classes="text-h6")
                html.Div("Active", classes="text-caption")
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div("{{ sessions_metrics_duration || '0h' }}", classes="text-h6")
                html.Div("Total Duration", classes="text-caption")
        with v3.VCol(cols=6, sm=3):
            with v3.VCard(variant="tonal", classes="text-center pa-2"):
                html.Div("{{ sessions_metrics_avg_tasks || 0 }}", classes="text-h6")
                html.Div("Avg Tasks/Session", classes="text-caption")


def _build_filters_row():
    """F.1: Dynamic column filters for Status and Agent."""
    with v3.VRow(dense=True, classes="align-center mb-1"):
        with v3.VCol(cols=12, sm=3):
            v3.VSelect(
                v_model="sessions_filter_status",
                items=("['ACTIVE', 'COMPLETED']",),
                label="Status",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                __properties=["data-testid"],
                **{"data-testid": "sessions-filter-status"},
            )
        with v3.VCol(cols=12, sm=3):
            v3.VSelect(
                v_model="sessions_filter_agent",
                items=("sessions_agent_options",),
                label="Agent",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                __properties=["data-testid"],
                **{"data-testid": "sessions-filter-agent"},
            )
        with v3.VCol(cols=12, sm=4):
            v3.VTextField(
                v_model="sessions_search_query",
                label="Search sessions...",
                prepend_inner_icon="mdi-magnify",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                __properties=["data-testid"],
                **{"data-testid": "sessions-search"},
            )
        with v3.VCol(cols=12, sm=2, classes="d-flex gap-1 align-center"):
            v3.VBtn(
                icon="mdi-text-search", variant="tonal", size="small",
                color="secondary",
                click="trigger('perform_search', [sessions_search_query])",
                disabled=("!sessions_search_query",),
                __properties=["data-testid"],
                **{"data-testid": "sessions-evidence-search-btn"},
            )
            with v3.VBtnToggle(
                v_model="sessions_view_mode",
                mandatory=True,
                density="compact",
                variant="outlined",
                update_modelValue="(val) => trigger('sessions_toggle_view', [val])",
            ):
                v3.VBtn(value="table", icon="mdi-table", size="small")
                v3.VBtn(value="pivot", icon="mdi-chart-bar", size="small")


def _build_timeline():
    """F.3: Timeline histogram of sessions by date.

    Uses Plotly interactive chart when trame-plotly is installed,
    falls back to VSparkline otherwise.
    """
    # Try Plotly first (richer, interactive, D3-like)
    if has_plotly():
        build_plotly_timeline()
        return

    # Fallback: VSparkline (basic but always available)
    with html.Div(
        v_if="sessions_timeline_data && sessions_timeline_data.length > 0",
        classes="mb-2",
    ):
        with html.Div(classes="d-flex align-center mb-1"):
            html.Span("Sessions per Day", classes="text-caption text-grey")
            html.Span(
                v_text=(
                    "' (' + (sessions_timeline_labels[0] || '')"
                    " + ' to '"
                    " + (sessions_timeline_labels[sessions_timeline_labels.length - 1] || '')"
                    " + ')'",
                ),
                classes="text-caption text-grey ml-1",
            )
            with v3.VTooltip(location="top"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VIcon(
                        "mdi-information-outline",
                        size="x-small",
                        classes="ml-1 text-grey",
                        v_bind="props",
                    )
                html.Span(
                    "Number of sessions started each day. "
                    "Bar height = session count for that date."
                )
        v3.VSparkline(
            model_value=("sessions_timeline_data",),
            labels=("sessions_timeline_labels",),
            type="bar",
            color="primary",
            height=50,
            padding=4,
            line_width=2,
            show_labels=True,
            label_size=8,
        )


def _build_data_table():
    """Main sessions data table with F.2 duration column."""
    v3.VDataTable(
        v_if="sessions_view_mode === 'table'",
        items=("sessions",),
        headers=("sessions_headers", [
            {"title": "Session ID", "key": "session_id", "width": "180px", "sortable": True},
            {"title": "Source", "key": "source_type", "width": "70px", "sortable": True},
            {"title": "Project", "key": "cc_project_slug", "width": "120px", "sortable": True},
            {"title": "Start", "key": "start_time", "width": "130px", "sortable": True},
            {"title": "End", "key": "end_time", "width": "130px", "sortable": True},
            {"title": "Duration", "key": "duration", "width": "90px", "sortable": True},
            {"title": "Status", "key": "status", "width": "100px", "sortable": True},
            {"title": "Agent", "key": "agent_id", "width": "130px", "sortable": True},
            {"title": "Description", "key": "description"},
        ]),
        item_value="session_id",
        search=("sessions_search_query",),
        density="compact",
        items_per_page=-1,
        hover=True,
        click_row="($event, row) => { trigger('select_session', [row.item.session_id || row.item.id]) }",
        __events=[("click_row", "click:row")],
        loading=("is_loading",),
        __properties=["data-testid"],
        **{"data-testid": "sessions-table"},
    )


def _build_pivot_table():
    """F.4: Pivot table view grouped by agent or status."""
    with html.Div(v_if="sessions_view_mode === 'pivot'"):
        with v3.VRow(dense=True, classes="mb-2"):
            with v3.VCol(cols=4):
                v3.VSelect(
                    v_model="sessions_pivot_group_by",
                    items=("[{title: 'Agent', value: 'agent_id'}, {title: 'Status', value: 'status'}]",),
                    label="Group by",
                    variant="outlined",
                    density="compact",
                    hide_details=True,
                    update_modelValue="trigger('sessions_compute_pivot')",
                )
        v3.VDataTable(
            items=("sessions_pivot_data",),
            headers=("sessions_pivot_headers", [
                {"title": "Group", "key": "group", "sortable": True},
                {"title": "Count", "key": "count", "width": "80px", "sortable": True},
                {"title": "Completed", "key": "completed", "width": "100px", "sortable": True},
                {"title": "Active", "key": "active", "width": "80px", "sortable": True},
                {"title": "Avg Duration", "key": "avg_duration", "width": "120px", "sortable": True},
            ]),
            density="compact",
            items_per_page=-1,
            __properties=["data-testid"],
            **{"data-testid": "sessions-pivot-table"},
        )


def _build_pagination():
    """Pagination controls (GAP-UI-036) with F.5 server-side support."""
    with v3.VCardActions(classes="d-flex justify-space-between align-center px-4"):
        with html.Div(classes="d-flex align-center"):
            html.Span("Items per page:", classes="text-body-2 mr-2")
            v3.VSelect(
                v_model="sessions_per_page",
                items=("sessions_per_page_options",),
                variant="outlined",
                density="compact",
                hide_details=True,
                style="max-width: 80px",
                update_modelValue="trigger('sessions_change_page_size')",
                __properties=["data-testid"],
                **{"data-testid": "sessions-per-page"},
            )
        html.Span(
            v_text=(
                "'Page ' + sessions_page + ' of ' + "
                "Math.max(1, Math.ceil(sessions_pagination.total / sessions_per_page)) + "
                "' (' + sessions_pagination.total + ' total)'"
            ),
            classes="text-body-2 text-grey",
        )
        with html.Div(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-chevron-left", variant="text", size="small",
                disabled=("sessions_page <= 1",),
                click="trigger('sessions_prev_page')",
            )
            v3.VBtn(
                icon="mdi-chevron-right", variant="text", size="small",
                disabled=("!sessions_pagination.has_more",),
                click="trigger('sessions_next_page')",
            )


def build_sessions_list_view() -> None:
    """Build the Sessions list view with filters, timeline, pivot, and duration."""
    with v3.VCard(
        v_if="active_view === 'sessions' && !show_session_detail && !show_session_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "sessions-list"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Session Evidence")
            v3.VSpacer()
            v3.VBtn(
                "Add Session", color="primary", prepend_icon="mdi-plus",
                click="session_form_mode = 'create'; show_session_form = true",
                __properties=["data-testid"],
                **{"data-testid": "sessions-add-btn"},
            )

        with v3.VCardText(classes="pb-0"):
            _build_metrics_row()
            _build_filters_row()
            _build_timeline()

        v3.VDivider()
        v3.VProgressLinear(
            v_if="is_loading", indeterminate=True, color="primary",
        )

        with v3.VCardText(classes="pt-1", style="overflow-y: auto"):
            _build_data_table()
            _build_pivot_table()

        _build_pagination()
