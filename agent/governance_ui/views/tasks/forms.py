"""
Tasks Form Components.

Per RULE-012: Single Responsibility - only task forms and content previews.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-037: Task body/content preview and linked items.
"""

from trame.widgets import vuetify3 as v3, html


def build_task_create_dialog() -> None:
    """Build the task creation dialog (shown when show_task_form is true).

    Per B.1: Fix task create dialog - dialog bound to show_task_form state.
    """
    with v3.VDialog(
        v_model="show_task_form",
        max_width="600px",
        __properties=["data-testid"],
        **{"data-testid": "task-create-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Create New Task")
            with v3.VCardText():
                v3.VTextField(
                    v_model="form_task_id",
                    label="Task ID (e.g., GAP-XXX-001)",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "task-create-id"}
                )
                v3.VTextField(
                    v_model="form_task_description",
                    label="Description",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "task-create-description"}
                )
                with v3.VRow():
                    with v3.VCol(cols=12, sm=6):
                        v3.VSelect(
                            v_model="form_task_phase",
                            label="Phase",
                            items=[
                                "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10",
                                "RD", "TOOL", "DOC", "FH", "TEST"
                            ],
                            variant="outlined",
                            density="compact",
                            __properties=["data-testid"],
                            **{"data-testid": "task-create-phase"}
                        )
                    with v3.VCol(cols=12, sm=6):
                        v3.VTextField(
                            v_model="form_task_agent",
                            label="Agent ID (optional)",
                            variant="outlined",
                            density="compact",
                            __properties=["data-testid"],
                            **{"data-testid": "task-create-agent"}
                        )
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click="show_task_form = false",
                    __properties=["data-testid"],
                    **{"data-testid": "task-create-cancel-btn"}
                )
                v3.VBtn(
                    "Create",
                    color="primary",
                    click="create_task(); show_task_form = false",
                    __properties=["data-testid"],
                    **{"data-testid": "task-create-submit-btn"}
                )


def build_task_edit_form() -> None:
    """Build the task edit form (shown when edit_task_mode is true)."""
    with html.Div(v_if="edit_task_mode"):
        v3.VTextField(
            v_model="edit_task_description",
            label="Description",
            variant="outlined",
            density="compact",
            classes="mb-3",
            __properties=["data-testid"],
            **{"data-testid": "task-edit-description"}
        )
        # Per UI-RESP-01-v1: Responsive form layout
        with v3.VRow():
            with v3.VCol(cols=12, sm=4):
                v3.VSelect(
                    v_model="edit_task_phase",
                    label="Phase",
                    items=[
                        "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10",
                        "RD", "TOOL", "DOC", "FH", "TEST"
                    ],
                    variant="outlined",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-phase"}
                )
            with v3.VCol(cols=12, sm=4):
                v3.VSelect(
                    v_model="edit_task_status",
                    label="Status",
                    items=["TODO", "IN_PROGRESS", "DONE", "BLOCKED"],
                    variant="outlined",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-status"}
                )
            with v3.VCol(cols=12, sm=4):
                v3.VTextField(
                    v_model="edit_task_agent",
                    label="Agent ID",
                    variant="outlined",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-agent"}
                )
        with html.Div(classes="d-flex justify-end mt-3"):
            v3.VBtn(
                "Cancel",
                variant="text",
                click="edit_task_mode = false",
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "task-edit-cancel-btn"}
            )
            v3.VBtn(
                "Save",
                color="primary",
                click="trigger('submit_task_edit')",
                __properties=["data-testid"],
                **{"data-testid": "task-edit-save-btn"}
            )


def build_task_content_preview() -> None:
    """Build task body/content preview (GAP-UI-037)."""
    with v3.VCard(
        v_if="!edit_task_mode && (selected_task.body || selected_task.content)",
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "task-content-preview"}
    ):
        v3.VCardTitle("Content", density="compact")
        with v3.VCardText():
            html.Pre(
                "{{ selected_task.body || selected_task.content }}",
                style="white-space: pre-wrap; font-family: monospace; "
                      "font-size: 0.875rem; "
                      "padding: 12px; border-radius: 4px; max-height: 300px; "
                      "overflow-y: auto;",
                classes="bg-surface-variant",
                __properties=["data-testid"],
                **{"data-testid": "task-content-text"}
            )


def build_task_linked_items() -> None:
    """Build linked rules/sessions display (GAP-UI-037)."""
    with v3.VCard(
        v_if=(
            "!edit_task_mode && "
            "(selected_task.linked_rules?.length > 0 || "
            "selected_task.linked_sessions?.length > 0 || "
            "selected_task.gap_id)"
        ),
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "task-linked-items"}
    ):
        v3.VCardTitle("Related Items", density="compact")
        with v3.VCardText():
            # GAP ID
            with html.Div(
                v_if="selected_task.gap_id",
                classes="mb-2"
            ):
                html.Span("Gap: ", classes="font-weight-bold")
                v3.VChip(
                    v_text="selected_task.gap_id",
                    size="small",
                    color="warning",
                    prepend_icon="mdi-alert-circle-outline"
                )
            # Linked Rules
            with html.Div(
                v_if="selected_task.linked_rules?.length > 0",
                classes="mb-2"
            ):
                html.Span("Rules: ", classes="font-weight-bold")
                v3.VChip(
                    v_for="rule in selected_task.linked_rules",
                    v_text="rule",
                    size="small",
                    color="primary",
                    classes="mr-1",
                    prepend_icon="mdi-gavel"
                )
            # Linked Sessions
            with html.Div(v_if="selected_task.linked_sessions?.length > 0"):
                html.Span("Sessions: ", classes="font-weight-bold")
                v3.VChip(
                    v_for="session in selected_task.linked_sessions",
                    v_text="session",
                    size="small",
                    color="info",
                    classes="mr-1",
                    prepend_icon="mdi-calendar-clock"
                )
            # Document linkage (PLAN-UI-OVERHAUL-001 Task 2.4)
            with html.Div(
                v_if="selected_task.document_path",
                classes="mb-2"
            ):
                html.Span("Document: ", classes="font-weight-bold")
                v3.VBtn(
                    v_text="selected_task.document_path",
                    variant="tonal",
                    size="small",
                    color="secondary",
                    prepend_icon="mdi-file-document-outline",
                    click="trigger('load_file_content', [selected_task.document_path])",
                    __properties=["data-testid"],
                    **{"data-testid": "task-document-btn"}
                )
            # Agent pipeline (PLAN-UI-OVERHAUL-001 Task 3.4: Multi-Agent Mapping)
            with html.Div(
                v_if=(
                    "selected_task.involved_agents?.length > 0 || "
                    "selected_task.agent_id"
                ),
                classes="mb-2"
            ):
                html.Span("Agent Pipeline: ", classes="font-weight-bold")
                # Primary assigned agent
                v3.VChip(
                    v_if="selected_task.agent_id",
                    v_text="selected_task.agent_id",
                    size="small",
                    color="info",
                    classes="mr-1",
                    prepend_icon="mdi-robot",
                    __properties=["data-testid"],
                    **{"data-testid": "task-primary-agent"}
                )
                # Additional involved agents
                v3.VChip(
                    v_for="agent in (selected_task.involved_agents || [])",
                    v_if="agent !== selected_task.agent_id",
                    v_text="agent",
                    size="small",
                    color="secondary",
                    variant="outlined",
                    classes="mr-1",
                    prepend_icon="mdi-robot",
                    __properties=["data-testid"],
                    **{"data-testid": "task-involved-agent"}
                )

            # Evidence with verification info (GAP-UI-LINKED-SESSIONS-001)
            with html.Div(
                v_if="selected_task.evidence",
                classes="mt-3"
            ):
                html.Span("Evidence: ", classes="font-weight-bold")
                html.Pre(
                    "{{ selected_task.evidence }}",
                    style="white-space: pre-wrap; font-family: monospace; "
                          "font-size: 0.8rem; "
                          "padding: 8px; border-radius: 4px; margin-top: 4px;",
                    classes="bg-surface-variant",
                    __properties=["data-testid"],
                    **{"data-testid": "task-evidence-text"}
                )
