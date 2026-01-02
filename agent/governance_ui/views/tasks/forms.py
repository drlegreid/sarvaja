"""
Tasks Form Components.

Per RULE-012: Single Responsibility - only task forms and content previews.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-037: Task body/content preview and linked items.
"""

from trame.widgets import vuetify3 as v3, html


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
        with v3.VRow():
            with v3.VCol(cols=4):
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
            with v3.VCol(cols=4):
                v3.VSelect(
                    v_model="edit_task_status",
                    label="Status",
                    items=["TODO", "IN_PROGRESS", "DONE", "BLOCKED"],
                    variant="outlined",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-status"}
                )
            with v3.VCol(cols=4):
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
                      "font-size: 0.875rem; background: #f5f5f5; "
                      "padding: 12px; border-radius: 4px; max-height: 300px; "
                      "overflow-y: auto;",
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
