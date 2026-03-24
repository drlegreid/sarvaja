"""
Task Create Dialog Component.

Per DOC-SIZE-01-v1: Extracted from forms.py.
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
                with v3.VRow():
                    with v3.VCol(cols=12, sm=6):
                        v3.VSelect(
                            v_model="form_task_type",
                            label="Task Type",
                            items=("task_type_options",),
                            variant="outlined",
                            density="compact",
                            clearable=True,
                            __properties=["data-testid"],
                            **{"data-testid": "task-create-type"}
                        )
                    with v3.VCol(cols=12, sm=6):
                        v3.VSelect(
                            v_model="form_task_priority",
                            label="Priority",
                            items=("task_priority_options",),
                            variant="outlined",
                            density="compact",
                            clearable=True,
                            __properties=["data-testid"],
                            **{"data-testid": "task-create-priority"}
                        )
                v3.VTextField(
                    v_model="form_task_id",
                    label="Task ID (auto-generated if empty)",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    hint="Leave blank to auto-generate from Task Type",
                    persistent_hint=True,
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
                v3.VTextarea(
                    v_model="form_task_body",
                    label="Body / Extended Content (optional)",
                    variant="outlined",
                    density="compact",
                    rows=4,
                    auto_grow=True,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "task-create-body"}
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
                    click="trigger('create_task')",
                    __properties=["data-testid"],
                    **{"data-testid": "task-create-submit-btn"}
                )
