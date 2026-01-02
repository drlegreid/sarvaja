"""
Session Evidence Components.

Per RULE-012: Single Responsibility - evidence file management.
Per RULE-032: File size limit (<300 lines).
Per GAP-DATA-003: Evidence file navigation.
Per P11.5: Session Evidence Attachments.
"""

from trame.widgets import vuetify3 as v3, html


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
