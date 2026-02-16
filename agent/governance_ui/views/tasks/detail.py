"""
Tasks Detail View Component.

Per RULE-012: Single Responsibility - only task detail UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
Per UI-NAV-01-v1: Entity Navigation - back to source button.
"""

from trame.widgets import vuetify3 as v3, html

from .forms import (
    build_task_edit_form,
    build_task_content_preview,
    build_task_linked_items,
)
from .execution import build_task_execution_log


def build_task_tech_docs() -> None:
    """Build Technology Solution Documentation sections (TASK-TECH-01-v1).

    Shows business, design, architecture, and test sections if populated.
    """
    _SECTIONS = [
        ("business", "Business Context (Why)", "mdi-briefcase-outline", "primary"),
        ("design", "Design (What)", "mdi-drawing", "info"),
        ("architecture", "Architecture (How)", "mdi-sitemap", "warning"),
        ("test_section", "Test Plan (Verification)", "mdi-test-tube", "success"),
    ]
    with html.Div(
        v_if=(
            "!edit_task_mode && ("
            "selected_task.business || selected_task.design || "
            "selected_task.architecture || selected_task.test_section)"
        ),
        classes="mt-4",
    ):
        html.H3("Solution Documentation", classes="text-subtitle-1 font-weight-bold mb-2")
        for field, label, icon, color in _SECTIONS:
            with v3.VCard(
                v_if=f"selected_task.{field}",
                variant="outlined",
                classes="mb-3",
                __properties=["data-testid"],
                **{"data-testid": f"task-tech-{field}"},
            ):
                with v3.VCardTitle(density="compact"):
                    v3.VIcon(icon, size="small", color=color, classes="mr-2")
                    html.Span(label)
                with v3.VCardText():
                    html.Pre(
                        "{{ selected_task." + field + " }}",
                        style="white-space: pre-wrap; font-family: monospace; "
                              "font-size: 0.85rem; padding: 8px; "
                              "border-radius: 4px; max-height: 250px; "
                              "overflow-y: auto;",
                        classes="bg-surface-variant",
                    )


def build_task_info_cards() -> None:
    """Build task information cards (shown when not in edit mode)."""
    # Content preview first (GAP-UI-037)
    build_task_content_preview()
    build_task_linked_items()

    with v3.VRow(v_if="!edit_task_mode"):
        # Left column: Task information - Per UI-RESP-01-v1: Responsive
        with v3.VCol(cols=12, md=6):
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
        # Right column: Assignment info - Per UI-RESP-01-v1
        with v3.VCol(cols=12, md=6):
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
            # Back to source button (UI-NAV-01-v1) - shown when navigated from another entity
            v3.VBtn(
                ("nav_source_label",),
                v_if="nav_source_view",
                prepend_icon="mdi-arrow-left",
                variant="tonal",
                color="primary",
                size="small",
                click="trigger('navigate_back_to_source')",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-back-to-source"}
            )
            # Simple back button (no navigation source)
            v3.VBtn(
                v_if="!nav_source_view",
                icon="mdi-arrow-left",
                variant="text",
                click="trigger('close_task_detail')",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-back-btn"}
            )
            html.Span(
                "{{ selected_task.task_id || selected_task.id }}",
                classes="ml-2",
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
            # Claim button (EPIC-UI-VALUE-001)
            v3.VBtn(
                "Claim",
                v_if=(
                    "!edit_task_mode && "
                    "(!selected_task.status || selected_task.status === 'OPEN' || "
                    "selected_task.status === 'TODO')"
                ),
                color="success",
                prepend_icon="mdi-hand-pointing-up",
                variant="outlined",
                click="trigger('claim_selected_task')",
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-claim-btn"}
            )
            # Complete button (EPIC-UI-VALUE-001)
            v3.VBtn(
                "Complete",
                v_if=(
                    "!edit_task_mode && "
                    "selected_task.status === 'IN_PROGRESS'"
                ),
                color="success",
                prepend_icon="mdi-check-circle",
                variant="outlined",
                click="trigger('complete_selected_task')",
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "task-detail-complete-btn"}
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
                # Resolution badge (GAP-UI-LINKED-SESSIONS-001)
                v3.VChip(
                    v_if=(
                        "selected_task.resolution && "
                        "selected_task.resolution !== 'NONE'"
                    ),
                    v_text="selected_task.resolution",
                    v_bind_color=(
                        "selected_task.resolution === 'CERTIFIED' ? 'success' : "
                        "selected_task.resolution === 'VALIDATED' ? 'info' : "
                        "selected_task.resolution === 'IMPLEMENTED' ? 'warning' : "
                        "'grey'"
                    ),
                    prepend_icon=(
                        "selected_task.resolution === 'CERTIFIED' ? "
                        "'mdi-check-decagram' : "
                        "selected_task.resolution === 'VALIDATED' ? 'mdi-test-tube' : "
                        "'mdi-code-tags'"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "task-detail-resolution"}
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

            # Technology Solution Documentation (TASK-TECH-01-v1)
            build_task_tech_docs()

            # Execution Log Section (ORCH-007)
            build_task_execution_log()
