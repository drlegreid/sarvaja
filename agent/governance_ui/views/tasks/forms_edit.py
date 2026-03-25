"""
Task Edit Form Component.

Per DOC-SIZE-01-v1: Extracted from forms.py.
"""

from trame.widgets import vuetify3 as v3, html


def build_task_edit_form() -> None:
    """Build the task edit form (shown when edit_task_mode is true)."""
    with html.Div(v_if="edit_task_mode"):
        # P15: Summary field (short title)
        v3.VTextField(
            v_model="edit_task_summary",
            label="Summary",
            variant="outlined",
            density="compact",
            classes="mb-3",
            __properties=["data-testid"],
            **{"data-testid": "task-edit-summary"}
        )
        v3.VTextField(
            v_model="edit_task_description",
            label="Description",
            variant="outlined",
            density="compact",
            classes="mb-3",
            __properties=["data-testid"],
            **{"data-testid": "task-edit-description"}
        )
        # P15: Body textarea (extended content)
        v3.VTextarea(
            v_model="edit_task_body",
            label="Body / Extended Content",
            variant="outlined",
            density="compact",
            rows=4,
            auto_grow=True,
            classes="mb-3",
            __properties=["data-testid"],
            **{"data-testid": "task-edit-body"}
        )
        # Per UI-RESP-01-v1: Responsive form layout
        with v3.VRow():
            with v3.VCol(cols=12, sm=6, md=3):
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
            with v3.VCol(cols=12, sm=6, md=3):
                # P14: Status dropdown from canonical TaskStatus enum
                v3.VSelect(
                    v_model="edit_task_status",
                    label="Status",
                    items=("task_status_options",),
                    variant="outlined",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-status"}
                )
            with v3.VCol(cols=12, sm=6, md=3):
                # P15: Priority select
                v3.VSelect(
                    v_model="edit_task_priority",
                    label="Priority",
                    items=("task_priority_options",),
                    variant="outlined",
                    density="compact",
                    clearable=True,
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-priority"}
                )
            with v3.VCol(cols=12, sm=6, md=3):
                # P15: Task type select
                v3.VSelect(
                    v_model="edit_task_type",
                    label="Task Type",
                    items=("task_type_options",),
                    variant="outlined",
                    density="compact",
                    clearable=True,
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-type"}
                )
        with v3.VRow():
            with v3.VCol(cols=12, sm=6):
                v3.VTextField(
                    v_model="edit_task_agent",
                    label="Agent ID",
                    variant="outlined",
                    density="compact",
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-agent"}
                )
        # EPIC-TASK-TAXONOMY-V2: Orthogonal tag dimensions
        with v3.VRow():
            with v3.VCol(cols=12, sm=4):
                v3.VCombobox(
                    v_model="edit_task_layer",
                    label="Layer (where)",
                    items=("task_layer_options",),
                    variant="outlined",
                    density="compact",
                    clearable=True,
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-layer"}
                )
            with v3.VCol(cols=12, sm=4):
                v3.VCombobox(
                    v_model="edit_task_concern",
                    label="Concern (what aspect)",
                    items=("task_concern_options",),
                    variant="outlined",
                    density="compact",
                    clearable=True,
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-concern"}
                )
            with v3.VCol(cols=12, sm=4):
                v3.VCombobox(
                    v_model="edit_task_method",
                    label="Method (how)",
                    items=("task_method_options",),
                    variant="outlined",
                    density="compact",
                    clearable=True,
                    __properties=["data-testid"],
                    **{"data-testid": "task-edit-method"}
                )
        # P17: Resolution notes textarea (shown for terminal tasks)
        v3.VTextarea(
            v_if=(
                "selected_task.status === 'DONE' || "
                "selected_task.status === 'CANCELED'"
            ),
            v_model="edit_task_resolution_notes",
            label="Resolution Notes",
            variant="outlined",
            density="compact",
            rows=4,
            auto_grow=True,
            classes="mb-3",
            hint="Markdown-formatted resolution narrative",
            persistent_hint=True,
            __properties=["data-testid"],
            **{"data-testid": "task-edit-resolution-notes"}
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
