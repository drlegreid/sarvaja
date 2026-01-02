"""
Tasks List View Component.

Per RULE-012: Single Responsibility - only tasks list UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html


def build_tasks_list_view() -> None:
    """
    Build the Tasks list view.

    Shows all platform tasks with status, phase, and assignment info.
    Clicking a task opens the detail view.
    """
    with v3.VCard(
        v_if="active_view === 'tasks' && !show_task_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "tasks-list"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Platform Tasks")
            v3.VSpacer()
            v3.VBtn(
                "Add Task",
                prepend_icon="mdi-plus",
                color="primary",
                size="small",
                click="show_task_form = true",
                __properties=["data-testid"],
                **{"data-testid": "tasks-add-btn"}
            )

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "tasks-loading"}
        )

        # Tasks list content (GAP-UI-036: scrollable)
        with v3.VCardText(style="max-height: 500px; overflow-y: auto;"):
            html.Div("{{ tasks.length }} tasks loaded", classes="mb-2 text-grey")
            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "tasks-table"}
            ):
                with v3.VListItem(
                    v_for="task in tasks",
                    **{":key": "task.task_id || task.id"},
                    click="selected_task = task; show_task_detail = true",
                    __properties=["data-testid"],
                    **{"data-testid": "task-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon(
                            icon=(
                                "task.status === 'DONE' ? 'mdi-checkbox-marked' : "
                                "task.status === 'IN_PROGRESS' ? 'mdi-progress-clock' : "
                                "'mdi-checkbox-blank-outline'",
                            ),
                            color=(
                                "task.status === 'DONE' ? 'success' : "
                                "task.status === 'IN_PROGRESS' ? 'info' : 'grey'",
                            ),
                        )
                    with v3.VListItemTitle():
                        html.Span(
                            "{{ task.task_id || task.id }}: "
                            "{{ task.description || task.title || task.name }}"
                        )
                    with v3.VListItemSubtitle():
                        # Metadata chips (GAP-UI-049 enhancement)
                        with html.Div(classes="d-flex align-center flex-wrap mb-1"):
                            v3.VChip(
                                v_text="task.phase",
                                size="x-small",
                                color="primary",
                                variant="tonal",
                                classes="mr-1"
                            )
                            v3.VChip(
                                v_text="task.status",
                                size="x-small",
                                v_bind_color=(
                                    "task.status === 'DONE' ? 'success' : "
                                    "task.status === 'IN_PROGRESS' ? 'info' : "
                                    "task.status === 'BLOCKED' ? 'error' : 'grey'"
                                ),
                                variant="tonal",
                                classes="mr-1"
                            )
                            v3.VChip(
                                v_if="task.agent_id",
                                v_text="task.agent_id",
                                size="x-small",
                                color="secondary",
                                variant="tonal",
                                prepend_icon="mdi-robot",
                                classes="mr-1"
                            )
                            # Linked items indicators (GAP-UI-049)
                            v3.VChip(
                                v_if="task.gap_id",
                                v_text="task.gap_id",
                                size="x-small",
                                color="warning",
                                variant="tonal",
                                prepend_icon="mdi-alert-circle-outline"
                            )
                        # Linked rules and sessions count (GAP-UI-049)
                        with html.Div(
                            v_if=(
                                "task.linked_rules?.length > 0 || "
                                "task.linked_sessions?.length > 0"
                            ),
                            classes="d-flex align-center text-caption text-grey"
                        ):
                            html.Span(
                                v_if="task.linked_rules?.length > 0",
                                v_text=(
                                    "'Rules: ' + task.linked_rules.join(', ')"
                                ),
                                classes="mr-2"
                            )
                            html.Span(
                                v_if="task.linked_sessions?.length > 0",
                                v_text=(
                                    "'Sessions: ' + task.linked_sessions.length"
                                )
                            )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="task.status",
                            color=(
                                "task.status === 'DONE' ? 'success' : "
                                "task.status === 'IN_PROGRESS' ? 'info' : "
                                "task.status === 'BLOCKED' ? 'error' : 'grey'",
                            ),
                            size="small",
                        )
