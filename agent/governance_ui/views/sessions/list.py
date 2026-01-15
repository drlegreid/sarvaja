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

        # Sessions list content (GAP-UI-036: scrollable)
        with v3.VCardText(style="max-height: 500px; overflow-y: auto;"):
            html.Div(
                "{{ sessions.filter(s => !sessions_search_query || (s.session_id || s.id || '').toLowerCase().includes(sessions_search_query.toLowerCase())).length }} sessions loaded",
                classes="mb-2 text-grey"
            )
            with v3.VTimeline(density="compact"):
                with v3.VTimelineItem(
                    v_for="session in sessions.filter(s => !sessions_search_query || (s.session_id || s.id || '').toLowerCase().includes(sessions_search_query.toLowerCase()))",
                    key=("session.session_id || session.id",),
                    dot_color="primary",
                    size="small",
                ):
                    with v3.VCard(
                        density="compact",
                        click="selected_session = session; show_session_detail = true",
                        __properties=["data-testid"],
                        **{"data-testid": "session-row"}
                    ):
                        v3.VCardTitle(
                            "{{ session.session_id || session.id }}",
                            density="compact"
                        )
                        v3.VCardSubtitle("{{ session.start_time || session.date || 'No date' }}")
