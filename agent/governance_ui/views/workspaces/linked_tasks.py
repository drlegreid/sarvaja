"""
Workspace Linked Tasks Component.

Per RULE-012: Single Responsibility - linked tasks display.
Per RULE-032: File size limit (<300 lines).
Per GAP-WS-DETAIL-UI / EPIC-GOV-TASKS-V2 Phase 6b.
Per UI-NAV-01-v1: Entity Navigation - pass source for back button.
"""

from trame.widgets import vuetify3 as v3, html


def build_workspace_linked_tasks() -> None:
    """Build linked tasks section for workspace detail view.

    Displays tasks linked via workspace-has-task relation.
    Pattern from: sessions/tasks.py build_completed_tasks_card().
    """
    with v3.VCard(
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "workspace-linked-tasks"}
    ):
        with v3.VCardTitle(classes="d-flex justify-space-between align-center"):
            html.Span("Linked Tasks")
            v3.VChip(
                v_text="workspace_tasks.length || 0",
                size="small",
                color="primary",
                __properties=["data-testid"],
                **{"data-testid": "workspace-tasks-count"}
            )
        with v3.VCardText():
            # Loading state
            with v3.VProgressLinear(
                v_if="workspace_tasks_loading",
                indeterminate=True,
                color="primary"
            ):
                pass

            # List of linked tasks
            with v3.VList(
                v_if="workspace_tasks && workspace_tasks.length > 0 && !workspace_tasks_loading",
                density="compact"
            ):
                with v3.VListItem(
                    v_for="(task, idx) in workspace_tasks",
                    key=("idx",),
                    prepend_icon="mdi-checkbox-marked-circle-outline",
                    click=(
                        "trigger('navigate_to_task', ["
                        "task.task_id, "
                        "'workspaces', "
                        "selected_workspace.workspace_id, "
                        "'Workspace: ' + (selected_workspace.name || selected_workspace.workspace_id)"
                        "])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-task-item"}
                ):
                    v3.VListItemTitle(
                        "{{ task.task_id }}: {{ task.description || task.name }}"
                    )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="task.status",
                            size="x-small",
                            color=(
                                "task.status === 'DONE' ? 'success' : "
                                "task.status === 'IN_PROGRESS' ? 'warning' : "
                                "'default'"
                            ),
                        )

            # No tasks message
            with html.Div(
                v_if=(
                    "(!workspace_tasks || workspace_tasks.length === 0) && "
                    "!workspace_tasks_loading"
                ),
                classes="text-grey text-center py-4"
            ):
                html.Span("No tasks linked to this workspace")
