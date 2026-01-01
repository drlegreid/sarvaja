"""
Backlog View for Governance Dashboard.

Per RULE-012: Single Responsibility - only backlog/task queue UI.
Per RULE-014: Autonomous Task Sequencing.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 2874-3007.
"""

from trame.widgets import vuetify3 as v3, html


def build_backlog_header() -> None:
    """Build backlog header with agent ID input and refresh."""
    with v3.VCardTitle(classes="d-flex align-center"):
        html.Span("Agent Task Backlog")
        v3.VSpacer()
        v3.VTextField(
            v_model="backlog_agent_id",
            label="Agent ID",
            variant="outlined",
            density="compact",
            hide_details=True,
            style="max-width: 200px",
            prepend_inner_icon="mdi-robot",
            __properties=["data-testid"],
            **{"data-testid": "backlog-agent-id-input"}
        )
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            color="primary",
            variant="outlined",
            size="small",
            classes="ml-2",
            click="trigger('refresh_backlog')",
            __properties=["data-testid"],
            **{"data-testid": "backlog-refresh-btn"}
        )


def build_available_tasks_column() -> None:
    """Build the available tasks column."""
    with v3.VCol(cols=6):
        with v3.VCard(variant="outlined"):
            with v3.VCardTitle(classes="text-subtitle-1 bg-info"):
                v3.VIcon(icon="mdi-inbox-arrow-down", classes="mr-2")
                html.Span("Available Tasks")
                v3.VSpacer()
                v3.VChip(
                    v_text="available_tasks.length",
                    size="small",
                    color="info",
                )
            with v3.VCardText(style="max-height: 500px; overflow-y: auto"):
                html.Div(
                    "No available tasks",
                    v_if="available_tasks.length === 0",
                    classes="text-grey text-center py-4"
                )
                with v3.VList(
                    density="compact",
                    v_if="available_tasks.length > 0"
                ):
                    with v3.VListItem(
                        v_for="task in available_tasks",
                        **{":key": "task.task_id"},
                        __properties=["data-testid"],
                        **{"data-testid": "backlog-available-task"}
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon(
                                icon="mdi-checkbox-blank-outline",
                                color="grey",
                            )
                        with v3.VListItemTitle():
                            html.Span("{{ task.task_id }}")
                        with v3.VListItemSubtitle():
                            html.Span("{{ task.description || 'No description' }}")
                        with v3.VListItemSubtitle():
                            html.Span("Phase: {{ task.phase }}")
                        with html.Template(v_slot_append=True):
                            v3.VBtn(
                                "Claim",
                                color="primary",
                                size="x-small",
                                variant="tonal",
                                disabled="!backlog_agent_id",
                                click="trigger('claim_backlog_task', task.task_id)",
                                __properties=["data-testid"],
                                **{"data-testid": "backlog-claim-btn"}
                            )


def build_claimed_tasks_column() -> None:
    """Build the claimed tasks column."""
    with v3.VCol(cols=6):
        with v3.VCard(variant="outlined"):
            with v3.VCardTitle(classes="text-subtitle-1 bg-warning"):
                v3.VIcon(icon="mdi-progress-clock", classes="mr-2")
                html.Span("My Tasks")
                v3.VSpacer()
                v3.VChip(
                    v_text="claimed_tasks.length",
                    size="small",
                    color="warning",
                )
            with v3.VCardText(style="max-height: 500px; overflow-y: auto"):
                with html.Div(
                    v_if="!backlog_agent_id",
                    classes="text-grey text-center py-4"
                ):
                    html.Span("Enter Agent ID to see your tasks")
                with html.Div(
                    v_if="backlog_agent_id && claimed_tasks.length === 0",
                    classes="text-grey text-center py-4"
                ):
                    html.Span("No claimed tasks")
                with v3.VList(
                    density="compact",
                    v_if="backlog_agent_id && claimed_tasks.length > 0"
                ):
                    with v3.VListItem(
                        v_for="task in claimed_tasks",
                        **{":key": "task.task_id"},
                        __properties=["data-testid"],
                        **{"data-testid": "backlog-claimed-task"}
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon(
                                icon="mdi-progress-clock",
                                color="warning",
                            )
                        with v3.VListItemTitle():
                            html.Span("{{ task.task_id }}")
                        with v3.VListItemSubtitle():
                            html.Span("{{ task.description || 'No description' }}")
                        with v3.VListItemSubtitle():
                            html.Span("Claimed: {{ task.claimed_at || 'N/A' }}")
                        with html.Template(v_slot_append=True):
                            v3.VBtn(
                                "Complete",
                                color="success",
                                size="x-small",
                                variant="tonal",
                                click="trigger('complete_backlog_task', task.task_id)",
                                __properties=["data-testid"],
                                **{"data-testid": "backlog-complete-btn"}
                            )


def build_backlog_view() -> None:
    """
    Build the Backlog view for task queue management.

    This is the main entry point for the backlog view module.
    Per RULE-014: Autonomous Task Sequencing.
    """
    with v3.VCard(
        v_if="active_view === 'backlog'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "backlog-view"}
    ):
        build_backlog_header()

        with v3.VCardText():
            with v3.VRow():
                build_available_tasks_column()
                build_claimed_tasks_column()
