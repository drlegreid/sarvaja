"""
Tasks Execution Log Components.

Per RULE-012: Single Responsibility - only execution log UI.
Per RULE-032: File size limit (<300 lines).
Per ORCH-007: Task execution log timeline.
"""

from trame.widgets import vuetify3 as v3, html


def build_execution_timeline() -> None:
    """Build the execution events timeline."""
    with v3.VTimeline(
        # BUG-290-EXEC-001: Null guard on task_execution_log before .length access
        v_if="!task_execution_loading && (task_execution_log || []).length > 0",
        density="compact",
        side="end",
        __properties=["data-testid"],
        **{"data-testid": "task-execution-timeline"}
    ):
        with v3.VTimelineItem(
            v_for="(event, idx) in task_execution_log",
            # BUG-186-002: Use dynamic binding, not static string
            **{":key": "idx"},
            dot_color=(
                "event.event_type === 'completed' ? 'success' : "
                "event.event_type === 'failed' ? 'error' : "
                "event.event_type === 'claimed' ? 'info' : "
                "event.event_type === 'progress' ? 'warning' : 'grey'",
            ),
            size="small",
            __properties=["data-testid"],
            **{"data-testid": "task-execution-event"}
        ):
            with html.Template(v_slot_opposite=True):
                html.Span(
                    "{{ event.timestamp ? "
                    "event.timestamp.substring(0, 19).replace('T', ' ') : '' }}",
                    classes="text-caption text-grey"
                )
            with html.Div():
                with html.Div(classes="d-flex align-center"):
                    v3.VIcon(
                        icon=(
                            "event.event_type === 'completed' ? 'mdi-check-circle' : "
                            "event.event_type === 'failed' ? 'mdi-alert-circle' : "
                            "event.event_type === 'claimed' ? 'mdi-hand-back-right' : "
                            "event.event_type === 'started' ? 'mdi-play' : "
                            "event.event_type === 'progress' ? 'mdi-progress-clock' : "
                            "event.event_type === 'delegated' ? 'mdi-account-switch' : "
                            "event.event_type === 'evidence' ? 'mdi-file-document' : "
                            "'mdi-circle'",
                        ),
                        size="small",
                        classes="mr-2"
                    )
                    html.Strong(
                        # BUG-256-UI-003: Guard against null event_type before charAt
                        "{{ event.event_type ? (event.event_type.charAt(0).toUpperCase() + "
                        "event.event_type.slice(1)) : 'Unknown' }}",
                        classes="text-body-2"
                    )
                    v3.VChip(
                        v_if="event.agent_id",
                        v_text="event.agent_id",
                        size="x-small",
                        color="secondary",
                        variant="tonal",
                        classes="ml-2"
                    )
                html.Div(
                    "{{ event.message }}",
                    v_if="event.message",
                    classes="text-body-2 text-grey mt-1"
                )


def build_task_execution_log() -> None:
    """Build the task execution log section (ORCH-007)."""
    v3.VDivider(v_if="!edit_task_mode", classes="my-4")
    with v3.VCard(
        v_if="!edit_task_mode",
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "task-execution-log"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon(icon="mdi-timeline-clock", classes="mr-2")
            html.Span("Execution Log")
            v3.VSpacer()
            v3.VBtn(
                "Refresh",
                variant="text",
                size="small",
                prepend_icon="mdi-refresh",
                click=(
                    # BUG-290-EXEC-002: Guard against null selected_task before accessing task_id
                    "selected_task && trigger('load_task_execution', "
                    "[selected_task.task_id || selected_task.id])"
                ),
                loading=("task_execution_loading",),
                __properties=["data-testid"],
                **{"data-testid": "task-execution-refresh"}
            )
            with v3.VBtn(
                icon=True,
                variant="text",
                size="small",
                click="show_task_execution_inline = !show_task_execution_inline",
            ):
                v3.VIcon(
                    v_bind_icon=(
                        "show_task_execution_inline ? 'mdi-chevron-up' : 'mdi-chevron-down'",
                    )
                )

        with v3.VExpandTransition():
            with html.Div(v_if="show_task_execution_inline"):
                with v3.VCardText():
                    # Loading state
                    with v3.VProgressLinear(
                        v_if="task_execution_loading",
                        indeterminate=True,
                        color="primary"
                    ):
                        pass

                    # Empty state
                    html.Div(
                        "No execution events recorded",
                        # BUG-290-EXEC-001: Null guard on task_execution_log before .length access
                        v_if="!task_execution_loading && (task_execution_log || []).length === 0",
                        classes="text-grey text-center py-4"
                    )

                    # Timeline of events
                    build_execution_timeline()
