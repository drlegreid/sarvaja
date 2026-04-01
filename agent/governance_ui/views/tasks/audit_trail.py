"""Task Audit Trail Component — SRVJ-FEAT-AUDIT-TRAIL-01 P3.

Collapsible VCard with VTimeline showing chronological audit entries.
Per SRP: component ONLY renders. No API calls. No state mutation.
Per DRY: reuses VTimeline pattern from execution.py.
"""

from trame.widgets import vuetify3 as v3, html


# Icon + color mapping for action types (exported for unit tests)
AUDIT_ACTION_ICONS = {
    "CREATE": {"icon": "mdi-plus-circle", "color": "success"},
    "UPDATE": {"icon": "mdi-swap-horizontal", "color": "warning"},
    "LINK": {"icon": "mdi-link-variant", "color": "info"},
    "UNLINK": {"icon": "mdi-link-variant-off", "color": "grey"},
    "COMMENT": {"icon": "mdi-comment-text", "color": "purple"},
    "DELETE": {"icon": "mdi-delete", "color": "error"},
    "_default": {"icon": "mdi-circle-small", "color": "grey"},
}


def _build_audit_timeline() -> None:
    """Build the VTimeline of audit entries."""
    with v3.VTimeline(
        v_if="!task_audit_loading && (task_audit_entries || []).length > 0",
        density="compact",
        side="end",
        __properties=["data-testid"],
        **{"data-testid": "task-audit-timeline"},
    ):
        with v3.VTimelineItem(
            v_for="(entry, idx) in task_audit_entries",
            **{":key": "idx"},
            dot_color=(
                "entry.action_type === 'CREATE' ? 'success' : "
                "entry.action_type === 'UPDATE' ? 'warning' : "
                "entry.action_type === 'LINK' ? 'info' : "
                "entry.action_type === 'UNLINK' ? 'grey' : "
                "entry.action_type === 'COMMENT' ? 'purple' : "
                "entry.action_type === 'DELETE' ? 'error' : 'grey'",
            ),
            size="small",
            __properties=["data-testid"],
            **{"data-testid": "task-audit-entry"},
        ):
            # Opposite slot: timestamp
            with html.Template(v_slot_opposite=True):
                html.Span(
                    "{{ entry.timestamp ? "
                    "entry.timestamp.substring(0, 19).replace('T', ' ') : '' }}",
                    classes="text-caption text-grey",
                )

            # Content
            with html.Div():
                # Action type + actor chip
                with html.Div(classes="d-flex align-center"):
                    v3.VIcon(
                        icon=(
                            "entry.action_type === 'CREATE' ? 'mdi-plus-circle' : "
                            "entry.action_type === 'UPDATE' ? 'mdi-swap-horizontal' : "
                            "entry.action_type === 'LINK' ? 'mdi-link-variant' : "
                            "entry.action_type === 'UNLINK' ? 'mdi-link-variant-off' : "
                            "entry.action_type === 'COMMENT' ? 'mdi-comment-text' : "
                            "entry.action_type === 'DELETE' ? 'mdi-delete' : "
                            "'mdi-circle-small'",
                        ),
                        size="small",
                        classes="mr-2",
                    )
                    html.Strong(
                        "{{ entry.action_type ? (entry.action_type.charAt(0).toUpperCase()"
                        " + entry.action_type.slice(1).toLowerCase()) : 'Unknown' }}",
                        classes="text-body-2",
                    )
                    v3.VChip(
                        v_if="entry.actor_id",
                        v_text="entry.actor_id",
                        size="x-small",
                        color="secondary",
                        variant="tonal",
                        classes="ml-2",
                    )

                # UPDATE: old -> new value
                html.Div(
                    "{{ entry.old_value || '?' }} → {{ entry.new_value || '?' }}",
                    v_if=(
                        "entry.action_type === 'UPDATE' && "
                        "(entry.old_value || entry.new_value)"
                    ),
                    classes="text-body-2 text-grey mt-1",
                )

                # LINK/UNLINK: linked entity info
                html.Div(
                    "{{ entry.metadata && entry.metadata.linked_entity ? "
                    "(entry.metadata.linked_entity.type + ': ' + "
                    "entry.metadata.linked_entity.id) : '' }}",
                    v_if=(
                        "(entry.action_type === 'LINK' || "
                        "entry.action_type === 'UNLINK') && "
                        "entry.metadata && entry.metadata.linked_entity"
                    ),
                    classes="text-body-2 text-grey mt-1",
                )

                # COMMENT: body preview
                html.Div(
                    "{{ entry.metadata && entry.metadata.body ? "
                    "entry.metadata.body.substring(0, 100) : '' }}",
                    v_if=(
                        "entry.action_type === 'COMMENT' && "
                        "entry.metadata && entry.metadata.body"
                    ),
                    classes="text-body-2 text-grey mt-1 font-italic",
                )


def _build_audit_filter() -> None:
    """Build action type filter dropdown."""
    v3.VSelect(
        v_model=("task_audit_filter_action", None),
        items=("['CREATE', 'UPDATE', 'LINK', 'UNLINK', 'COMMENT', 'DELETE']",),
        label="Filter",
        clearable=True,
        density="compact",
        variant="outlined",
        hide_details=True,
        style="max-width: 160px;",
        update_modelValue=(
            "task_audit_page = 1; "
            "selected_task && trigger('load_task_audit', "
            "[selected_task.task_id || selected_task.id])"
        ),
        __properties=["data-testid"],
        **{"data-testid": "task-audit-filter"},
    )


def _build_audit_pagination() -> None:
    """Build pagination controls for audit trail."""
    with html.Div(
        v_if="(task_audit_entries || []).length > 0",
        classes="d-flex align-center justify-center mt-2",
    ):
        v3.VBtn(
            icon="mdi-chevron-left",
            size="small",
            variant="text",
            disabled=("task_audit_page <= 1",),
            click=(
                "task_audit_page = Math.max(1, task_audit_page - 1); "
                "selected_task && trigger('load_task_audit', "
                "[selected_task.task_id || selected_task.id])"
            ),
            __properties=["data-testid"],
            **{"data-testid": "task-audit-prev-page"},
        )
        html.Span(
            "{{ 'Page ' + task_audit_page }}",
            classes="text-caption mx-2",
            __properties=["data-testid"],
            **{"data-testid": "task-audit-page-info"},
        )
        v3.VBtn(
            icon="mdi-chevron-right",
            size="small",
            variant="text",
            disabled=(
                "(task_audit_entries || []).length < task_audit_per_page",
            ),
            click=(
                "task_audit_page = task_audit_page + 1; "
                "selected_task && trigger('load_task_audit', "
                "[selected_task.task_id || selected_task.id])"
            ),
            __properties=["data-testid"],
            **{"data-testid": "task-audit-next-page"},
        )


def build_task_audit_trail() -> None:
    """Build the task audit trail section (SRVJ-FEAT-AUDIT-TRAIL-01 P3).

    Collapsible card with VTimeline, filter, and pagination.
    """
    v3.VDivider(v_if="!edit_task_mode", classes="my-4")
    with v3.VCard(
        v_if="!edit_task_mode",
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "task-audit-trail-card"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon(icon="mdi-history", classes="mr-2")
            html.Span("Audit Trail")
            v3.VChip(
                v_text="(task_audit_entries || []).length",
                size="x-small",
                color="grey",
                variant="tonal",
                classes="ml-2",
                __properties=["data-testid"],
                **{"data-testid": "task-audit-count-chip"},
            )
            v3.VSpacer()
            _build_audit_filter()
            v3.VBtn(
                "Refresh",
                variant="text",
                size="small",
                prepend_icon="mdi-refresh",
                click=(
                    "selected_task && trigger('load_task_audit', "
                    "[selected_task.task_id || selected_task.id])"
                ),
                loading=("task_audit_loading",),
                classes="ml-2",
                __properties=["data-testid"],
                **{"data-testid": "task-audit-refresh"},
            )
            with v3.VBtn(
                icon=True,
                variant="text",
                size="small",
                click="show_task_audit_inline = !show_task_audit_inline",
                __properties=["data-testid"],
                **{"data-testid": "task-audit-expand-btn"},
            ):
                v3.VIcon(
                    v_bind_icon=(
                        "show_task_audit_inline ? 'mdi-chevron-up' : 'mdi-chevron-down'",
                    )
                )

        with v3.VExpandTransition():
            with html.Div(v_if="show_task_audit_inline"):
                with v3.VCardText():
                    # Loading state
                    with v3.VProgressLinear(
                        v_if="task_audit_loading",
                        indeterminate=True,
                        color="primary",
                    ):
                        pass

                    # Empty state
                    html.Div(
                        "No audit entries recorded",
                        v_if=(
                            "!task_audit_loading && "
                            "(task_audit_entries || []).length === 0"
                        ),
                        classes="text-grey text-center py-4",
                    )

                    # Timeline
                    _build_audit_timeline()

                    # Pagination
                    _build_audit_pagination()
