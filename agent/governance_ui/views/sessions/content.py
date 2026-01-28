"""
Session Content Components.

Per RULE-012: Single Responsibility - session content display.
Per RULE-032: File size limit (<300 lines).
Per GAP-DATA-003: File path navigation.
"""

from trame.widgets import vuetify3 as v3


def build_session_metadata_chips() -> None:
    """Build session metadata chips."""
    with v3.VChipGroup(classes="mb-4"):
        v3.VChip(
            v_text="selected_session.start_time || selected_session.date || 'No date'",
            prepend_icon="mdi-calendar",
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "session-detail-date"}
        )
        v3.VChip(
            v_text="selected_session.status || 'N/A'",
            prepend_icon="mdi-information",
            __properties=["data-testid"],
            **{"data-testid": "session-detail-status"}
        )


def build_session_info_card() -> None:
    """Build session information card."""
    with v3.VCard(
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "session-detail-content"}
    ):
        v3.VCardTitle("Session Information", density="compact")
        with v3.VCardText():
            with v3.VList(density="compact"):
                v3.VListItem(
                    title="Session ID",
                    subtitle=("selected_session.session_id || selected_session.id",),
                    prepend_icon="mdi-identifier",
                )
                v3.VListItem(
                    title="Date",
                    subtitle=("selected_session.start_time || selected_session.date || 'N/A'",),
                    prepend_icon="mdi-calendar",
                )
                # File Path - Clickable to view content (GAP-DATA-003)
                v3.VListItem(
                    v_if="selected_session.file_path || selected_session.path",
                    title="File Path",
                    subtitle=(
                        "selected_session.file_path || selected_session.path",
                    ),
                    prepend_icon="mdi-file-document",
                    click=(
                        "trigger('load_file_content', "
                        "[selected_session.file_path || selected_session.path])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "session-file-path"}
                )
                v3.VListItem(
                    v_if="!selected_session.file_path && !selected_session.path",
                    title="File Path",
                    subtitle="N/A",
                    prepend_icon="mdi-file-document",
                )
                v3.VListItem(
                    title="Description",
                    subtitle=("selected_session.description || 'No description'",),
                    prepend_icon="mdi-text",
                )
