"""
Attach Document Dialog for Tasks.

Simple dialog to attach a document to the selected task.
Per task document management feature.
"""

from trame.widgets import vuetify3 as v3, html


def build_attach_document_dialog() -> None:
    """Build the attach document dialog."""
    with v3.VDialog(
        v_model="show_attach_document_dialog",
        max_width="500px",
        __properties=["data-testid"],
        **{"data-testid": "attach-document-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Attach Document")
            with v3.VCardText():
                html.P(
                    "Enter the path to a document to attach to this task.",
                    classes="text-body-2 mb-3"
                )
                v3.VTextField(
                    v_model="attach_document_path",
                    label="Document Path (e.g., docs/rules/leaf/RULE-ID.md)",
                    variant="outlined",
                    density="compact",
                    prepend_inner_icon="mdi-file-document-outline",
                    hint="Relative path from project root",
                    persistent_hint=True,
                    __properties=["data-testid"],
                    **{"data-testid": "attach-document-path"}
                )
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click="show_attach_document_dialog = false; attach_document_path = ''",
                    __properties=["data-testid"],
                    **{"data-testid": "attach-document-cancel-btn"}
                )
                v3.VBtn(
                    "Attach",
                    color="primary",
                    disabled=("!attach_document_path",),
                    click="trigger('attach_document')",
                    __properties=["data-testid"],
                    **{"data-testid": "attach-document-submit-btn"}
                )
