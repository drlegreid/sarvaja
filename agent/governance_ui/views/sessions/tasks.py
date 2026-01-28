"""
Session Tasks Component.

Per RULE-012: Single Responsibility - completed tasks display.
Per RULE-032: File size limit (<300 lines).
Per GAP-DATA-INTEGRITY-001 Phase 3: UI navigation for relationships.
Per UI-NAV-01-v1: Entity Navigation - pass source for back button.
"""

from trame.widgets import vuetify3 as v3, html


def build_completed_tasks_card() -> None:
    """Build completed tasks section for session detail view.

    Per GAP-DATA-INTEGRITY-001 Phase 3: Click session -> show completed tasks.
    Displays tasks linked via completed-in relation.
    """
    with v3.VCard(
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-completed-tasks"}
    ):
        with v3.VCardTitle(classes="d-flex justify-space-between align-center"):
            html.Span("Completed Tasks")
            v3.VChip(
                v_text="session_tasks.length || 0",
                size="small",
                color="primary",
                __properties=["data-testid"],
                **{"data-testid": "session-tasks-count"}
            )
        with v3.VCardText():
            # Loading state
            with v3.VProgressLinear(
                v_if="session_tasks_loading",
                indeterminate=True,
                color="primary"
            ):
                pass

            # List of completed tasks
            with v3.VList(
                v_if="session_tasks && session_tasks.length > 0 && !session_tasks_loading",
                density="compact"
            ):
                with v3.VListItem(
                    v_for="(task, idx) in session_tasks",
                    key=("idx",),
                    prepend_icon="mdi-check-circle",
                    click=(
                        "trigger('navigate_to_task', ["
                        "task.task_id, "
                        "'sessions', "
                        "selected_session.session_id || selected_session.id, "
                        "'Session: ' + (selected_session.session_id || selected_session.id)"
                        "])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "session-task-item"}
                ):
                    # Task ID and name as title (inline)
                    v3.VListItemTitle("{{ task.task_id }}: {{ task.name }}")
                    # Status chip
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="task.status",
                            size="x-small",
                            color="success"
                        )

            # No tasks message
            with html.Div(
                v_if=(
                    "(!session_tasks || session_tasks.length === 0) && "
                    "!session_tasks_loading"
                ),
                classes="text-grey text-center py-4"
            ):
                html.Span("No tasks linked to this session")
