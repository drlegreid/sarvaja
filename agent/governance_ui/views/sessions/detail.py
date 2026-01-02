"""
Session Detail View Component.

Per RULE-012: Single Responsibility - only session detail UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-034: Session CRUD operations.
"""

from trame.widgets import vuetify3 as v3, html

from .content import build_session_metadata_chips, build_session_info_card
from .evidence import build_evidence_files_card


def build_session_detail_view() -> None:
    """
    Build the Session detail view.

    Shows session details with file path navigation (GAP-DATA-003).
    """
    with v3.VCard(
        v_if="active_view === 'sessions' && show_session_detail && selected_session",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "session-detail"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_session_detail = false; selected_session = null",
                __properties=["data-testid"],
                **{"data-testid": "session-detail-back-btn"}
            )
            html.Span(
                "{{ selected_session.session_id || selected_session.id }}",
                __properties=["data-testid"],
                **{"data-testid": "session-detail-id"}
            )
            v3.VSpacer()
            # Edit/Delete buttons (GAP-UI-034)
            v3.VBtn(
                "Edit",
                color="primary",
                prepend_icon="mdi-pencil",
                click="session_form_mode = 'edit'; show_session_form = true",
                __properties=["data-testid"],
                **{"data-testid": "session-detail-edit-btn"}
            )
            v3.VBtn(
                "Delete",
                color="error",
                prepend_icon="mdi-delete",
                click="delete_session",
                classes="ml-2",
                __properties=["data-testid"],
                **{"data-testid": "session-detail-delete-btn"}
            )

        with v3.VCardText():
            # Session metadata
            build_session_metadata_chips()

            # Session details
            build_session_info_card()

            # Evidence Files section (GAP-DATA-003)
            build_evidence_files_card()
