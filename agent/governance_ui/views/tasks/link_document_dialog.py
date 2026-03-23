"""
Link Document Dialog for Tasks (SRVJ-FEAT-012).

File browser dialog to link documents to a task.
Per BDD spec: multi-select from workspace documents, batch link.
"""

from trame.widgets import vuetify3 as v3, html


def build_link_document_dialog() -> None:
    """Build the link document tree browser dialog."""
    with v3.VDialog(
        v_model="show_link_document_dialog",
        max_width="700px",
        __properties=["data-testid"],
        **{"data-testid": "link-document-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Link Documents")
            with v3.VCardText():
                html.P(
                    "Select documents to link to this task.",
                    classes="text-body-2 mb-3"
                )
                v3.VTextField(
                    v_model="link_document_search",
                    label="Filter documents...",
                    variant="outlined",
                    density="compact",
                    prepend_inner_icon="mdi-magnify",
                    clearable=True,
                    hide_details=True,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "link-document-search"}
                )
                v3.VProgressLinear(
                    indeterminate=True,
                    v_if="link_document_loading",
                    color="primary",
                    classes="mb-2",
                )
                with v3.VList(
                    v_if="!link_document_loading",
                    max_height="400px",
                    style="overflow-y: auto",
                    select_strategy="classic",
                ):
                    v3.VListItem(
                        v_for=(
                            "doc in link_document_items.filter("
                            "d => !link_document_search || "
                            "d.path.toLowerCase().includes("
                            "link_document_search.toLowerCase()))"
                        ),
                        v_bind_title="doc.path.split('/').pop()",
                        v_bind_subtitle="doc.path",
                        v_bind_value="doc.path",
                        v_bind_prepend_icon=(
                            "doc.path.includes('evidence') ? 'mdi-beaker-outline' : "
                            "doc.path.includes('plans/') ? 'mdi-map-outline' : "
                            "doc.path.includes('.gherkin') ? 'mdi-format-list-checks' : "
                            "'mdi-file-document-outline'"
                        ),
                        click=(
                            "link_document_selected.includes(doc.path) "
                            "? link_document_selected = link_document_selected.filter("
                            "p => p !== doc.path) "
                            ": link_document_selected = [...link_document_selected, doc.path]"
                        ),
                        v_bind_active="link_document_selected.includes(doc.path)",
                        v_bind_append_icon=(
                            "link_document_selected.includes(doc.path) "
                            "? 'mdi-check-circle' : ''"
                        ),
                        v_bind_disabled=(
                            "(selected_task?.linked_documents || []).includes("
                            "doc.path)"
                        ),
                        __properties=["data-testid"],
                        **{"data-testid": "link-document-item"},
                    )
                html.P(
                    "No documents found",
                    v_if="!link_document_loading && link_document_items.length === 0",
                    classes="text-medium-emphasis text-center py-4",
                )
                html.Div(
                    v_if="link_document_selected.length > 0",
                    classes="text-caption text-medium-emphasis mt-2",
                    v_text=(
                        "link_document_selected.length + ' document(s) selected'"
                    ),
                )
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click=(
                        "show_link_document_dialog = false; "
                        "link_document_search = ''; "
                        "link_document_selected = []"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "link-document-cancel-btn"}
                )
                v3.VBtn(
                    "Link Selected",
                    color="primary",
                    disabled=("link_document_selected.length === 0",),
                    click="trigger('link_documents_to_task')",
                    __properties=["data-testid"],
                    **{"data-testid": "link-document-submit-btn"}
                )
