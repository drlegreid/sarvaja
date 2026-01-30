"""
Sessions List View Component.

Per RULE-012: Single Responsibility - only sessions list UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html


def build_sessions_list_view() -> None:
    """
    Build the Sessions list view.

    Displays session evidence in a timeline format.
    Clicking a session opens the detail view.
    """
    with v3.VCard(
        v_if="active_view === 'sessions' && !show_session_detail && !show_session_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "sessions-list"}
    ):
        # Header with title and add button (GAP-UI-034)
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Session Evidence")
            v3.VSpacer()
            v3.VBtn(
                "Add Session",
                color="primary",
                prepend_icon="mdi-plus",
                click="session_form_mode = 'create'; show_session_form = true",
                __properties=["data-testid"],
                **{"data-testid": "sessions-add-btn"}
            )

        # Search field
        with v3.VCardText(classes="pb-0"):
            v3.VTextField(
                v_model="sessions_search_query",
                label="Search sessions...",
                prepend_inner_icon="mdi-magnify",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                __properties=["data-testid"],
                **{"data-testid": "sessions-search"}
            )

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "sessions-loading"}
        )

        # Sessions data table (PLAN-UI-OVERHAUL-001 Task 1.2: Grid with columns)
        with v3.VCardText():
            v3.VDataTable(
                items=("sessions",),
                headers=[
                    {"title": "Session ID", "key": "session_id", "width": "200px", "sortable": True},
                    {"title": "Start Time", "key": "start_time", "width": "140px", "sortable": True},
                    {"title": "End Time", "key": "end_time", "width": "140px", "sortable": True},
                    {"title": "Status", "key": "status", "width": "100px", "sortable": True},
                    {"title": "Agent", "key": "agent_id", "width": "140px", "sortable": True},
                    {"title": "Description", "key": "description"},
                ],
                item_value="session_id",
                search=("sessions_search_query",),
                density="compact",
                items_per_page=("sessions_per_page",),
                hover=True,
                click_row=(
                    "($event, row) => { trigger('select_session', [row.item.session_id || row.item.id]) }",
                ),
                loading=("is_loading",),
                __properties=["data-testid"],
                **{"data-testid": "sessions-table"}
            )

        # Pagination controls (GAP-UI-036)
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
                    change="trigger('sessions_change_page_size')",
                    __properties=["data-testid"],
                    **{"data-testid": "sessions-per-page"}
                )
            html.Span(
                v_text=(
                    "'Page ' + sessions_page + ' of ' + "
                    "Math.max(1, Math.ceil(sessions_pagination.total / sessions_per_page)) + "
                    "' (' + sessions_pagination.total + ' total)'"
                ),
                classes="text-body-2 text-grey",
                __properties=["data-testid"],
                **{"data-testid": "sessions-page-info"}
            )
            with html.Div(classes="d-flex align-center"):
                v3.VBtn(
                    icon="mdi-chevron-left",
                    variant="text",
                    size="small",
                    disabled=("sessions_page <= 1",),
                    click="trigger('sessions_prev_page')",
                    __properties=["data-testid"],
                    **{"data-testid": "sessions-prev-btn"}
                )
                v3.VBtn(
                    icon="mdi-chevron-right",
                    variant="text",
                    size="small",
                    disabled=("!sessions_pagination.has_more",),
                    click="trigger('sessions_next_page')",
                    __properties=["data-testid"],
                    **{"data-testid": "sessions-next-btn"}
                )
