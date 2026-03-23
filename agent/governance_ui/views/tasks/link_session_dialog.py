"""
Link Session Dialog for Tasks (SRVJ-FEAT-011).

Searchable dialog to link sessions to a task.
Per BDD spec: select from all valid sessions, support multiple links.
"""

from trame.widgets import vuetify3 as v3, html


def build_link_session_dialog() -> None:
    """Build the link session picker dialog."""
    with v3.VDialog(
        v_model="show_link_session_dialog",
        max_width="700px",
        __properties=["data-testid"],
        **{"data-testid": "link-session-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Link Session")
            with v3.VCardText():
                html.P(
                    "Search and select a session to link to this task.",
                    classes="text-body-2 mb-3"
                )
                v3.VTextField(
                    v_model="link_session_search",
                    label="Search sessions...",
                    variant="outlined",
                    density="compact",
                    prepend_inner_icon="mdi-magnify",
                    clearable=True,
                    hide_details=True,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "link-session-search"}
                )
                v3.VProgressLinear(
                    indeterminate=True,
                    v_if="link_session_loading",
                    color="primary",
                    classes="mb-2",
                )
                with v3.VList(
                    v_if="!link_session_loading",
                    max_height="400px",
                    style="overflow-y: auto",
                ):
                    v3.VListItem(
                        v_for=(
                            "session in link_session_items.filter("
                            "s => !link_session_search || "
                            "s.session_id.toLowerCase().includes("
                            "link_session_search.toLowerCase()))"
                        ),
                        v_bind_title="session.session_id",
                        v_bind_subtitle=(
                            "session.topic || session.session_type || ''"
                        ),
                        prepend_icon="mdi-calendar-clock",
                        click=(
                            "trigger('link_session_to_task', "
                            "[session.session_id])"
                        ),
                        v_bind_disabled=(
                            "(selected_task?.linked_sessions || []).includes("
                            "session.session_id)"
                        ),
                        v_bind_append_icon=(
                            "(selected_task?.linked_sessions || []).includes("
                            "session.session_id) ? 'mdi-check' : ''"
                        ),
                        __properties=["data-testid"],
                        **{"data-testid": "link-session-item"},
                    )
                html.P(
                    "No sessions found",
                    v_if="!link_session_loading && link_session_items.length === 0",
                    classes="text-medium-emphasis text-center py-4",
                )
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Close",
                    variant="text",
                    click=(
                        "show_link_session_dialog = false; "
                        "link_session_search = ''"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "link-session-close-btn"}
                )
