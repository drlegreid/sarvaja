"""Task Multi-Session Timeline Component.

Per EPIC-ISSUE-EVIDENCE P18: Chronological merge of all linked session events.
Positioned between execution log and resolution section in task detail view.
Pattern mirrors execution.py (VTimeline + VTimelineItem).
"""

from trame.widgets import vuetify3 as v3, html


def _build_filter_chips() -> None:
    """Entry type filter chips above the timeline."""
    with v3.VChipGroup(
        v_model=("task_timeline_filter_types", []),
        multiple=True,
        classes="mb-2",
    ):
        for entry_type, icon, color in [
            ("tool_call", "mdi-wrench", "primary"),
            ("thought", "mdi-head-cog", "info"),
            ("decision", "mdi-scale-balance", "warning"),
            ("status_change", "mdi-swap-horizontal", "success"),
        ]:
            v3.VChip(
                v_text=f"'{entry_type}'",
                value=entry_type,
                prepend_icon=icon,
                color=color,
                variant="outlined",
                filter=True,
                size="small",
            )


def _build_timeline_items() -> None:
    """Build the VTimeline items from task_timeline_entries."""
    with v3.VTimeline(
        v_if=(
            "!task_timeline_loading && "
            "(task_timeline_entries || []).length > 0"
        ),
        density="compact",
        side="end",
        __properties=["data-testid"],
        **{"data-testid": "task-session-timeline"},
    ):
        with v3.VTimelineItem(
            v_for="(evt, idx) in task_timeline_entries",
            **{":key": "idx"},
            dot_color=("evt.color || 'grey'",),
            size="small",
            __properties=["data-testid"],
            **{"data-testid": "task-timeline-event"},
        ):
            # Opposite slot: timestamp
            with html.Template(v_slot_opposite=True):
                html.Span(
                    "{{ evt.timestamp ? "
                    "evt.timestamp.substring(0, 19).replace('T', ' ') : '' }}",
                    classes="text-caption text-grey",
                )
            # Main slot: icon + title + session chip + detail
            with html.Div():
                with html.Div(classes="d-flex align-center"):
                    v3.VIcon(
                        icon=("evt.icon || 'mdi-circle'",),
                        size="small",
                        classes="mr-2",
                    )
                    html.Strong(
                        "{{ evt.title || 'Event' }}",
                        classes="text-body-2",
                    )
                    # Session chip
                    v3.VChip(
                        v_if="evt.session_id",
                        v_text="evt.session_id.split('-').slice(-2).join('-')",
                        size="x-small",
                        color="secondary",
                        variant="tonal",
                        classes="ml-2",
                        click=(
                            "nav_source_view = 'tasks'; "
                            "nav_source_id = selected_task.task_id || "
                            "selected_task.id; "
                            "nav_source_label = 'Back to Task'; "
                            "trigger('navigate_to_session', "
                            "[evt.session_id])"
                        ),
                    )
                    # Duration chip
                    v3.VChip(
                        v_if="evt.duration_ms",
                        v_text="evt.duration_ms + 'ms'",
                        size="x-small",
                        color="grey",
                        variant="tonal",
                        classes="ml-1",
                    )
                # Detail text
                html.Div(
                    "{{ evt.detail }}",
                    v_if="evt.detail",
                    classes="text-body-2 text-grey mt-1",
                    style="max-height: 60px; overflow: hidden; "
                          "text-overflow: ellipsis;",
                )


def build_task_session_timeline() -> None:
    """Build the multi-session timeline section.

    Only shown when task has linked sessions and not in edit mode.
    """
    with html.Div(
        v_if=(
            "!edit_task_mode && selected_task.linked_sessions && "
            "selected_task.linked_sessions.length > 0"
        ),
    ):
        v3.VDivider(classes="my-4")
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "task-session-timeline-card"},
        ):
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon(icon="mdi-timeline-text", classes="mr-2")
                html.Span("Session Timeline")
                v3.VSpacer()
                v3.VBtn(
                    "Refresh",
                    variant="text",
                    size="small",
                    prepend_icon="mdi-refresh",
                    click=(
                        "selected_task && trigger('load_task_timeline', "
                        "[selected_task.task_id || selected_task.id])"
                    ),
                    loading=("task_timeline_loading",),
                    __properties=["data-testid"],
                    **{"data-testid": "task-timeline-refresh"},
                )
                with v3.VBtn(
                    icon=True,
                    variant="text",
                    size="small",
                    click=(
                        "show_task_timeline_inline = "
                        "!show_task_timeline_inline"
                    ),
                ):
                    v3.VIcon(
                        v_bind_icon=(
                            "show_task_timeline_inline ? "
                            "'mdi-chevron-up' : 'mdi-chevron-down'",
                        ),
                    )

            with v3.VExpandTransition():
                with html.Div(v_if="show_task_timeline_inline"):
                    with v3.VCardText():
                        # Filter chips
                        _build_filter_chips()

                        # Loading state
                        with v3.VProgressLinear(
                            v_if="task_timeline_loading",
                            indeterminate=True,
                            color="primary",
                        ):
                            pass

                        # Empty state
                        html.Div(
                            "No timeline events found for linked sessions",
                            v_if=(
                                "!task_timeline_loading && "
                                "(task_timeline_entries || []).length === 0"
                            ),
                            classes="text-grey text-center py-4",
                        )

                        # Timeline
                        _build_timeline_items()

                        # "Load more" button
                        with html.Div(
                            v_if="task_timeline_has_more",
                            classes="text-center mt-2",
                        ):
                            v3.VBtn(
                                "Load More",
                                variant="text",
                                size="small",
                                click=(
                                    "task_timeline_page = "
                                    "(task_timeline_page || 1) + 1; "
                                    "trigger('load_task_timeline', "
                                    "[selected_task.task_id || "
                                    "selected_task.id])"
                                ),
                            )
