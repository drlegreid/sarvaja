"""
Chat Task Execution Components.

Per RULE-012: Single Responsibility - execution display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-CHAT-002: Task execution viewing.
Per ORCH-007: Task execution timeline.
"""

from trame.widgets import vuetify3 as v3, html


def build_task_execution_button() -> None:
    """Build button to view current task execution (GAP-UI-CHAT-002)."""
    with html.Div(
        v_if="chat_task_id",
        classes="px-4 pb-2"
    ):
        v3.VBtn(
            "View Task Execution",
            prepend_icon="mdi-timeline-clock",
            variant="outlined",
            size="small",
            color="primary",
            click="trigger('load_task_execution', [chat_task_id])",
            __properties=["data-testid"],
            **{"data-testid": "view-execution-btn"}
        )


def build_task_execution_viewer() -> None:
    """Build Task Execution Viewer dialog (GAP-UI-CHAT-002, ORCH-007)."""
    with v3.VDialog(
        v_model="show_task_execution",
        max_width="700px",
        __properties=["data-testid"],
        **{"data-testid": "task-execution-dialog"}
    ):
        with v3.VCard():
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon("mdi-timeline-clock", classes="mr-2")
                html.Span("Task Execution Timeline")
                v3.VSpacer()
                v3.VBtn(
                    icon="mdi-close",
                    variant="text",
                    click="show_task_execution = false",
                    __properties=["data-testid"],
                    **{"data-testid": "execution-close-btn"}
                )

            with v3.VCardText():
                # Loading state
                with html.Div(
                    v_if="task_execution_loading",
                    classes="d-flex justify-center pa-4"
                ):
                    v3.VProgressCircular(indeterminate=True, size=32)
                    html.Span("Loading execution history...", classes="ml-2")

                # Empty state
                with v3.VAlert(
                    v_if=(
                        "!task_execution_loading && "
                        "task_execution_log.length === 0"
                    ),
                    type_="info",
                    variant="tonal"
                ):
                    html.Span("No execution events recorded yet.")

                # Timeline
                with v3.VTimeline(
                    v_if=(
                        "!task_execution_loading && "
                        "task_execution_log.length > 0"
                    ),
                    density="compact",
                    align="start",
                    __properties=["data-testid"],
                    **{"data-testid": "execution-timeline"}
                ):
                    with v3.VTimelineItem(
                        v_for="(event, idx) in task_execution_log",
                        key="idx",
                        dot_color=(
                            "event.event_type === 'completed' ? 'success' : "
                            "event.event_type === 'failed' ? 'error' : "
                            "event.event_type === 'progress' ? 'info' : 'primary'",
                        ),
                        size="small",
                        __properties=["data-testid"],
                        **{"data-testid": "execution-event"}
                    ):
                        with v3.VCard(density="compact", variant="outlined"):
                            with v3.VCardTitle(
                                classes="text-subtitle-2 py-1"
                            ):
                                # Event type icon (BUG-UI-TASKS-004: use icon= not v_text=)
                                v3.VIcon(
                                    icon=(
                                        "event.event_type === 'completed' "
                                        "? 'mdi-check-circle' : "
                                        "event.event_type === 'failed' "
                                        "? 'mdi-alert-circle' : "
                                        "event.event_type === 'claimed' "
                                        "? 'mdi-hand-pointing-right' : "
                                        "event.event_type === 'started' "
                                        "? 'mdi-play-circle' : "
                                        "event.event_type === 'progress' "
                                        "? 'mdi-progress-clock' : "
                                        "event.event_type === 'evidence' "
                                        "? 'mdi-file-document' : "
                                        "'mdi-circle'"
                                    ),
                                    size="small",
                                    classes="mr-1"
                                )
                                html.Span(
                                    "{{ event.event_type.toUpperCase() }}"
                                )
                            with v3.VCardText(classes="py-1"):
                                # Message
                                html.Div(
                                    v_if="event.message",
                                    v_text="event.message",
                                    classes="text-body-2"
                                )
                                # Timestamp and agent
                                with html.Div(
                                    classes="d-flex text-caption text-grey mt-1"
                                ):
                                    html.Span("{{ event.timestamp }}")
                                    html.Span(
                                        v_if="event.agent_id",
                                        v_text="' • ' + event.agent_id",
                                        classes="ml-1"
                                    )
