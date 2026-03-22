"""
Tasks List View Component.

Per RULE-012: Single Responsibility - only tasks list UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html
from .histogram import build_plotly_histogram, has_plotly as has_task_plotly


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
        with v3.VCardText(v_if="is_loading", style="max-height: calc(100vh - 280px);"):
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

        # Task histogram (Phase 9e: interactive type x status chart)
        if has_task_plotly():
            build_plotly_histogram()

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
            # Phase 9: task_type + priority filters
            v3.VSelect(
                v_model="tasks_type_filter",
                items=("task_type_options",),
                label="Type",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 130px; margin-left: 8px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-type"}
            )
            v3.VSelect(
                v_model="tasks_priority_filter",
                items=("task_priority_options",),
                label="Priority",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 130px; margin-left: 8px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-priority"}
            )
            # Phase 9d: Session filter
            v3.VTextField(
                v_model="tasks_session_filter",
                label="Session ID",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 200px; margin-left: 8px",
                prepend_inner_icon="mdi-calendar-clock",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-session"}
            )

        # Date range filters row (Phase 9)
        with v3.VToolbar(
            v_if="!is_loading",
            density="compact", flat=True,
            style="min-height: 48px",
        ):
            v3.VTextField(
                v_model="tasks_created_after",
                label="Created after",
                type="date",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 170px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-created-after"}
            )
            v3.VTextField(
                v_model="tasks_created_before",
                label="Created before",
                type="date",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 170px; margin-left: 8px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-created-before"}
            )
            v3.VSpacer()
            v3.VTextField(
                v_model="tasks_completed_after",
                label="Completed after",
                type="date",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 170px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-completed-after"}
            )
            v3.VTextField(
                v_model="tasks_completed_before",
                label="Completed before",
                type="date",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 170px; margin-left: 8px",
                __properties=["data-testid"],
                **{"data-testid": "tasks-filter-completed-before"}
            )

        # Tasks data table (PLAN-UI-OVERHAUL-001 Task 1.3: Grid with columns)
        with v3.VCardText(v_if="!is_loading"):
            v3.VDataTable(
                items=("tasks",),
                headers=("tasks_headers", [
                    {"title": "Project", "key": "project_name", "width": "120px", "sortable": True},
                    {"title": "Workspace", "key": "workspace_id", "width": "130px", "sortable": True},
                    {"title": "Task ID", "key": "task_id", "width": "150px", "sortable": True},
                    {"title": "Summary", "key": "summary", "sortable": True},
                    {"title": "Priority", "key": "priority", "width": "90px", "sortable": True},
                    {"title": "Type", "key": "task_type", "width": "80px", "sortable": True},
                    {"title": "Status", "key": "status", "width": "100px", "sortable": True},
                    {"title": "Session", "key": "first_session", "width": "160px", "sortable": False},
                    {"title": "Agent", "key": "agent_id", "width": "130px", "sortable": True},
                    {"title": "Created", "key": "created_at", "width": "110px", "sortable": True},
                    {"title": "Completed", "key": "completed_at", "width": "110px", "sortable": True},
                    {"title": "Docs", "key": "doc_count", "width": "70px", "sortable": False},
                ]),
                item_value="task_id",
                density="compact",
                items_per_page=-1,
                hover=True,
                hide_default_footer=True,
                click_row="($event, row) => { trigger('select_task', [row.item.task_id || row.item.id]) }",
                __events=[("click_row", "click:row")],
                __properties=["data-testid"],
                **{"data-testid": "tasks-table"}
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
                    update_modelValue="trigger('tasks_change_page_size')",
                    __properties=["data-testid"],
                    **{"data-testid": "tasks-per-page"}
                )

            # Page info
            html.Span(
                v_text=(
                    "'Page ' + tasks_page + ' of ' + "
                    "Math.max(1, Math.ceil(tasks_pagination.total / tasks_per_page)) + "
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
