"""
Tasks View for Governance Dashboard.

Per RULE-012: Single Responsibility - only tasks list/detail UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 2554-2870.
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
        with v3.VCardText():
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
                        html.Span(
                            "Phase: {{ task.phase }} | Status: {{ task.status }} | "
                            "Agent: {{ task.agent_id || 'Unassigned' }}"
                        )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="task.status",
                            color=(
                                "task.status === 'DONE' ? 'success' : "
                                "task.status === 'IN_PROGRESS' ? 'info' : 'grey'",
                            ),
                            size="small",
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


def build_task_info_cards() -> None:
    """Build task information cards (shown when not in edit mode)."""
    # Content preview first (GAP-UI-037)
    build_task_content_preview()
    build_task_linked_items()

    with v3.VRow(v_if="!edit_task_mode"):
        # Left column: Task information
        with v3.VCol(cols=6):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-info"}
            ):
                v3.VCardTitle("Task Information", density="compact")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            title="Task ID",
                            subtitle=("selected_task.task_id || selected_task.id",),
                            prepend_icon="mdi-identifier",
                        )
                        v3.VListItem(
                            title="Phase",
                            subtitle=("selected_task.phase || 'N/A'",),
                            prepend_icon="mdi-calendar-range",
                        )
                        v3.VListItem(
                            title="Status",
                            subtitle=("selected_task.status || 'TODO'",),
                            prepend_icon="mdi-list-status",
                        )
        # Right column: Assignment info
        with v3.VCol(cols=6):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-assignment"}
            ):
                v3.VCardTitle("Assignment", density="compact")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            title="Assigned Agent",
                            subtitle=("selected_task.agent_id || 'Unassigned'",),
                            prepend_icon="mdi-robot",
                        )
                        v3.VListItem(
                            title="Priority",
                            subtitle=("selected_task.priority || 'Normal'",),
                            prepend_icon="mdi-flag",
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
                    "trigger('load_task_execution', "
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
                click="show_task_execution = !show_task_execution",
            ):
                v3.VIcon(
                    v_bind_icon=(
                        "show_task_execution ? 'mdi-chevron-up' : 'mdi-chevron-down'",
                    )
                )

        with v3.VExpandTransition():
            with html.Div(v_if="show_task_execution"):
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
                        v_if="!task_execution_loading && task_execution_log.length === 0",
                        classes="text-grey text-center py-4"
                    )

                    # Timeline of events
                    _build_execution_timeline()


def _build_execution_timeline() -> None:
    """Build the execution events timeline."""
    with v3.VTimeline(
        v_if="!task_execution_loading && task_execution_log.length > 0",
        density="compact",
        side="end",
        __properties=["data-testid"],
        **{"data-testid": "task-execution-timeline"}
    ):
        with v3.VTimelineItem(
            v_for="(event, idx) in task_execution_log",
            key="idx",
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
                        "{{ event.event_type.charAt(0).toUpperCase() + "
                        "event.event_type.slice(1) }}",
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


def build_task_detail_view() -> None:
    """
    Build the Task detail view.

    Shows task details with edit/delete capabilities.
    Includes execution log timeline (ORCH-007).
    """
    with v3.VCard(
        v_if="active_view === 'tasks' && show_task_detail && selected_task",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "task-detail"}
    ):
        # Header with back button and actions
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_task_detail = false; selected_task = null",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-back-btn"}
            )
            html.Span(
                "{{ selected_task.task_id || selected_task.id }}",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-id"}
            )
            v3.VSpacer()
            v3.VBtn(
                "Edit",
                v_if="!edit_task_mode",
                color="primary",
                prepend_icon="mdi-pencil",
                variant="outlined",
                click=(
                    "edit_task_mode = true; "
                    "edit_task_description = selected_task.description || "
                    "selected_task.title || ''; "
                    "edit_task_phase = selected_task.phase || 'P10'; "
                    "edit_task_status = selected_task.status || 'TODO'; "
                    "edit_task_agent = selected_task.agent_id || ''"
                ),
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-edit-btn"}
            )
            v3.VBtn(
                "Delete",
                v_if="!edit_task_mode",
                color="error",
                prepend_icon="mdi-delete",
                variant="outlined",
                click="trigger('delete_task')",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-delete-btn"}
            )

        with v3.VCardText():
            # Edit Form
            build_task_edit_form()

            # Task description (shown when not in edit mode)
            html.H2(
                "{{ selected_task.description || selected_task.title || "
                "selected_task.name }}",
                v_if="!edit_task_mode",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-description"}
            )

            # Metadata chips (shown when not in edit mode)
            with v3.VChipGroup(v_if="!edit_task_mode", classes="mt-3"):
                v3.VChip(
                    v_text="selected_task.status",
                    color=(
                        "selected_task.status === 'DONE' ? 'success' : "
                        "selected_task.status === 'IN_PROGRESS' ? 'info' : 'grey'",
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "task-detail-status"}
                )
                v3.VChip(
                    v_text="'Phase: ' + selected_task.phase",
                    color="primary",
                    __properties=["data-testid"],
                    **{"data-testid": "task-detail-phase"}
                )
                v3.VChip(
                    v_text="'Agent: ' + (selected_task.agent_id || 'Unassigned')",
                    color="secondary",
                    __properties=["data-testid"],
                    **{"data-testid": "task-detail-agent"}
                )

            # Task details section
            v3.VDivider(v_if="!edit_task_mode", classes="my-4")
            build_task_info_cards()

            # Execution Log Section (ORCH-007)
            build_task_execution_log()


def build_tasks_view() -> None:
    """
    Build the complete Tasks view including list and detail.

    This is the main entry point for the tasks view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    """
    build_tasks_list_view()
    build_task_detail_view()
