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
            html.Span("Tasks")
            v3.VSpacer()
            # Agent ID for claim/complete (UI-AUDIT-2026-01-19: merged backlog)
            v3.VTextField(
                v_model="tasks_agent_id",
                label="Agent ID",
                variant="outlined",
                density="compact",
                hide_details=True,
                style="max-width: 180px",
                prepend_inner_icon="mdi-robot",
                __properties=["data-testid"],
                **{"data-testid": "tasks-agent-id"}
            )
            v3.VBtn(
                "Add Task",
                prepend_icon="mdi-plus",
                color="primary",
                size="small",
                classes="ml-2",
                click="show_task_form = true",
                __properties=["data-testid"],
                **{"data-testid": "tasks-add-btn"}
            )

        # Filter tabs (UI-AUDIT-2026-01-19: merged backlog)
        with v3.VTabs(
            v_model="tasks_filter_type",
            density="compact",
            __properties=["data-testid"],
            **{"data-testid": "tasks-filter-tabs"}
        ):
            v3.VTab(value="all", text="All")
            v3.VTab(value="available", text="Available")
            v3.VTab(value="mine", text="My Tasks")
            v3.VTab(value="completed", text="Completed")

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "tasks-loading"}
        )

        # Skeleton loaders (GAP-UI-PAGING-001: Loading states)
        with v3.VCardText(v_if="is_loading", style="max-height: 500px;"):
            with v3.VList(density="compact"):
                # Show 5 skeleton items while loading
                with v3.VListItem(v_for="n in 5", **{":key": "'skeleton-' + n"}):
                    with html.Template(v_slot_prepend=True):
                        v3.VSkeletonLoader(type="avatar", width=24, height=24)
                    with v3.VListItemTitle():
                        v3.VSkeletonLoader(type="text", width="60%")
                    with v3.VListItemSubtitle():
                        with html.Div(classes="d-flex align-center mt-1"):
                            v3.VSkeletonLoader(
                                type="chip", width=60, height=20, classes="mr-1"
                            )
                            v3.VSkeletonLoader(
                                type="chip", width=70, height=20, classes="mr-1"
                            )
                            v3.VSkeletonLoader(type="chip", width=80, height=20)
                    with html.Template(v_slot_append=True):
                        v3.VSkeletonLoader(type="chip", width=60, height=24)

        # Filters toolbar (GAP-UI-EXP-004: search/filter/pagination)
        with v3.VToolbar(v_if="!is_loading", density="compact", flat=True):
            v3.VTextField(
                v_model="tasks_search_query",
                label="Search tasks...",
                prepend_icon="mdi-magnify",
                variant="outlined",
                density="compact",
                hide_details=True,
                style="max-width: 300px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-search"}
            )
            v3.VSpacer()
            v3.VSelect(
                v_model="tasks_status_filter",
                items=("task_status_options",),
                label="Status",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 150px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-status"}
            )
            v3.VSelect(
                v_model="tasks_phase_filter",
                items=("task_phase_options",),
                label="Phase",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 150px; margin-left: 8px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-phase"}
            )

        # Tasks list content (GAP-UI-036: scrollable)
        with v3.VCardText(v_if="!is_loading", style="max-height: 500px; overflow-y: auto;"):
            html.Div("{{ tasks.length }} tasks loaded", classes="mb-2 text-grey")
            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "tasks-table"}
            ):
                with v3.VListItem(
                    v_for="task in tasks",
                    v_show=(
                        # Text search filter
                        "(!tasks_search_query || "
                        "((task.task_id || task.id) && (task.task_id || task.id).toLowerCase()"
                        ".includes(tasks_search_query.toLowerCase())) || "
                        "((task.description || task.title || task.name) && "
                        "(task.description || task.title || task.name).toLowerCase()"
                        ".includes(tasks_search_query.toLowerCase()))) && "
                        # Status dropdown filter
                        "(!tasks_status_filter || task.status === tasks_status_filter) && "
                        # Phase dropdown filter
                        "(!tasks_phase_filter || task.phase === tasks_phase_filter) && "
                        # Tab filter (UI-AUDIT-2026-01-19)
                        "(tasks_filter_type === 'all' || "
                        "(tasks_filter_type === 'available' && !task.agent_id && task.status !== 'DONE') || "
                        "(tasks_filter_type === 'mine' && task.agent_id === tasks_agent_id) || "
                        "(tasks_filter_type === 'completed' && task.status === 'DONE'))"
                    ),
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
                            # Resolution badge (GAP-UI-LINKED-SESSIONS-001)
                            v3.VChip(
                                v_if="task.resolution && task.resolution !== 'NONE'",
                                v_text="task.resolution",
                                size="x-small",
                                v_bind_color=(
                                    "task.resolution === 'CERTIFIED' ? 'success' : "
                                    "task.resolution === 'VALIDATED' ? 'info' : "
                                    "task.resolution === 'IMPLEMENTED' ? 'warning' : "
                                    "'grey'"
                                ),
                                variant="flat",
                                prepend_icon=(
                                    "task.resolution === 'CERTIFIED' ? 'mdi-check-decagram' : "
                                    "task.resolution === 'VALIDATED' ? 'mdi-test-tube' : "
                                    "task.resolution === 'IMPLEMENTED' ? 'mdi-code-tags' : "
                                    "'mdi-help-circle'"
                                ),
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
                                prepend_icon="mdi-alert-circle-outline",
                                classes="mr-1"
                            )
                            # Date display (GAP-UI-035)
                            html.Span(
                                v_if="task.created_at",
                                v_text="task.created_at",
                                classes="text-caption text-grey ml-2"
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
                        with html.Div(classes="d-flex align-center"):
                            # Claim button (UI-AUDIT-2026-01-19)
                            v3.VBtn(
                                "Claim",
                                v_if="!task.agent_id && task.status !== 'DONE'",
                                color="primary",
                                size="x-small",
                                variant="tonal",
                                disabled=("!tasks_agent_id",),
                                click_stop=(
                                    "trigger('claim_task', (task.task_id || task.id))"
                                ),
                                title=(
                                    "tasks_agent_id ? '' : "
                                    "'Enter Agent ID above to claim tasks'"
                                ),
                                classes="mr-1",
                                __properties=["data-testid"],
                                **{"data-testid": "task-claim-btn"}
                            )
                            # Complete button (UI-AUDIT-2026-01-19)
                            v3.VBtn(
                                "Complete",
                                v_if=(
                                    "task.agent_id === tasks_agent_id && "
                                    "task.status !== 'DONE'"
                                ),
                                color="success",
                                size="x-small",
                                variant="tonal",
                                click_stop=(
                                    "trigger('complete_task', (task.task_id || task.id))"
                                ),
                                classes="mr-1",
                                __properties=["data-testid"],
                                **{"data-testid": "task-complete-btn"}
                            )
                            v3.VChip(
                                v_text="task.status",
                                color=(
                                    "task.status === 'DONE' ? 'success' : "
                                    "task.status === 'IN_PROGRESS' ? 'info' : "
                                    "task.status === 'BLOCKED' ? 'error' : 'grey'",
                                ),
                                size="small",
                            )

        # Pagination controls (EPIC-DR-005)
        with v3.VCardActions(
            v_if="!is_loading && tasks_pagination.total > 0",
            classes="d-flex justify-space-between align-center px-4 py-2",
            __properties=["data-testid"],
            **{"data-testid": "tasks-pagination"}
        ):
            # Items per page selector
            with html.Div(classes="d-flex align-center"):
                html.Span("Items per page:", classes="text-body-2 mr-2")
                v3.VSelect(
                    v_model="tasks_per_page",
                    items=("tasks_per_page_options",),
                    variant="outlined",
                    density="compact",
                    hide_details=True,
                    style="max-width: 80px",
                    change="trigger('tasks_change_page_size')",
                    __properties=["data-testid"],
                    **{"data-testid": "tasks-per-page"}
                )

            # Page info
            html.Div(
                (
                    "'Page ' + tasks_page + ' of ' + "
                    "Math.ceil(tasks_pagination.total / tasks_per_page) + "
                    "' (' + tasks_pagination.total + ' total)'",
                ),
                classes="text-body-2 text-grey",
                __properties=["data-testid"],
                **{"data-testid": "tasks-page-info"}
            )

            # Navigation buttons
            with html.Div(classes="d-flex align-center"):
                v3.VBtn(
                    icon="mdi-chevron-left",
                    variant="text",
                    size="small",
                    disabled=("tasks_page <= 1",),
                    click="trigger('tasks_prev_page')",
                    __properties=["data-testid"],
                    **{"data-testid": "tasks-prev-btn"}
                )
                v3.VBtn(
                    icon="mdi-chevron-right",
                    variant="text",
                    size="small",
                    disabled=("!tasks_pagination.has_more",),
                    click="trigger('tasks_next_page')",
                    __properties=["data-testid"],
                    **{"data-testid": "tasks-next-btn"}
                )
