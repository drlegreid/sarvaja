"""
Sessions View for Governance Dashboard.

Per RULE-012: Single Responsibility - only session evidence UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 2234-2362.
"""

from trame.widgets import vuetify3 as v3, html


def build_sessions_list_view() -> None:
    """
    Build the Sessions list view.

    Displays session evidence in a timeline format.
    Clicking a session opens the detail view.
    """
    with v3.VCard(
        v_if="active_view === 'sessions' && !show_session_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "sessions-list"}
    ):
        v3.VCardTitle("Session Evidence")
        with v3.VCardText():
            html.Div(
                "{{ sessions.length }} sessions loaded",
                classes="mb-2 text-grey"
            )
            with v3.VTimeline(density="compact"):
                with v3.VTimelineItem(
                    v_for="session in sessions",
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
                        v3.VCardSubtitle("{{ session.date || 'No date' }}")


def build_session_metadata_chips() -> None:
    """Build session metadata chips."""
    with v3.VChipGroup(classes="mb-4"):
        v3.VChip(
            v_text="selected_session.date || 'No date'",
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
                    subtitle=("selected_session.date || 'N/A'",),
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


def build_evidence_files_card() -> None:
    """Build evidence files section (GAP-DATA-003) with attachment UI (P11.5)."""
    with v3.VCard(
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-evidence-files"}
    ):
        with v3.VCardTitle(classes="d-flex justify-space-between align-center"):
            html.Span("Evidence Files")
            v3.VBtn(
                "Attach Evidence",
                variant="outlined",
                size="small",
                prepend_icon="mdi-attachment",
                click="show_evidence_attach = true",
                __properties=["data-testid"],
                **{"data-testid": "attach-evidence-btn"}
            )
        with v3.VCardText():
            # List existing evidence files
            with v3.VList(
                v_if=(
                    "selected_session.evidence_files && "
                    "selected_session.evidence_files.length > 0"
                ),
                density="compact"
            ):
                v3.VListItem(
                    v_for="(filePath, idx) in selected_session.evidence_files",
                    key=("idx",),
                    v_text="filePath",
                    prepend_icon="mdi-file-document-outline",
                    click="trigger('load_file_content', [filePath])",
                    __properties=["data-testid"],
                    **{"data-testid": "evidence-file-item"}
                )
            # No evidence message
            html.Div(
                v_if=(
                    "!selected_session.evidence_files || "
                    "selected_session.evidence_files.length === 0"
                ),
                classes="text-grey text-center py-4"
            ).add_child(html.Span("No evidence files attached"))


def build_evidence_attach_dialog() -> None:
    """Build evidence attachment dialog (P11.5)."""
    with v3.VDialog(
        v_model=("show_evidence_attach",),
        max_width="500px",
        __properties=["data-testid"],
        **{"data-testid": "evidence-attach-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Attach Evidence to Session")
            with v3.VCardText():
                v3.VTextField(
                    v_model=("evidence_attach_path",),
                    label="Evidence File Path",
                    placeholder="e.g., evidence/DECISION-001.md",
                    hint="Enter the relative path to the evidence file",
                    persistent_hint=True,
                    prepend_icon="mdi-file-document",
                    __properties=["data-testid"],
                    **{"data-testid": "evidence-path-input"}
                )
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click="show_evidence_attach = false; evidence_attach_path = ''",
                )
                v3.VBtn(
                    "Attach",
                    color="primary",
                    loading=("evidence_attach_loading",),
                    disabled=("!evidence_attach_path",),
                    click=(
                        "trigger('attach_evidence', "
                        "[selected_session.session_id || selected_session.id, "
                        "evidence_attach_path])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "attach-evidence-confirm-btn"}
                )


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

        with v3.VCardText():
            # Session metadata
            build_session_metadata_chips()

            # Session details
            build_session_info_card()

            # Evidence Files section (GAP-DATA-003)
            build_evidence_files_card()


def build_sessions_view() -> None:
    """
    Build the complete Sessions view including list and detail.

    This is the main entry point for the sessions view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    Per P11.5: Session Evidence Attachments.
    """
    build_sessions_list_view()
    build_session_detail_view()
    build_evidence_attach_dialog()
