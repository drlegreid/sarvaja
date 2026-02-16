"""
Session Activity Timeline — Collapsible Chronological View.

Per GAP-SESSION-DETAIL-001: Merges tool_calls + thoughts into a
single chronological stream with collapsible detail panels.

Created: 2026-02-15
"""

from trame.widgets import vuetify3 as v3, html


def build_session_timeline_card() -> None:
    """Build collapsible chronological timeline of session activity."""
    with v3.VCard(
        classes="mt-3",
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "session-timeline-card"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon("mdi-timeline-clock-outline", classes="mr-2", size="small")
            html.Span("Activity Timeline")
            v3.VSpacer()
            v3.VChip(
                v_text="(session_timeline || []).length + ' events'",
                size="small",
                color="info",
                variant="tonal",
            )

        with v3.VCardText():
            # Empty state
            html.Div(
                "No activity data available for this session. "
                "Tool calls and thoughts are captured during active chat sessions.",
                v_if="!session_timeline || session_timeline.length === 0",
                classes="text-grey text-center py-4",
            )

            # Timeline list — collapsible items
            with v3.VList(
                v_if="session_timeline && session_timeline.length > 0",
                density="compact",
                lines="two",
            ):
                with v3.VListGroup(
                    v_for="(event, idx) in session_timeline",
                    key="idx",
                ):
                    # Group activator (always visible row)
                    with html.Template(
                        v_slot_activator="{ props }",
                    ):
                        with v3.VListItem(v_bind="props"):
                            with html.Template(v_slot_prepend=""):
                                v3.VIcon(
                                    v_text="event.icon",
                                    size="small",
                                    color=(
                                        "event.type === 'tool_call' "
                                        "? (event.success !== false ? 'success' : 'error') "
                                        ": 'info'"
                                    ),
                                )
                            with v3.VListItemTitle():
                                html.Span(
                                    v_text="event.title",
                                    classes="font-weight-medium",
                                )
                                v3.VChip(
                                    v_if="event.type === 'tool_call'",
                                    v_text="event.subtitle",
                                    size="x-small",
                                    variant="tonal",
                                    classes="ml-2",
                                )
                                v3.VChip(
                                    v_if="event.duration_ms > 0",
                                    v_text="event.duration_ms + 'ms'",
                                    size="x-small",
                                    variant="outlined",
                                    classes="ml-1",
                                )
                            with v3.VListItemSubtitle():
                                html.Span(
                                    v_text="event.timestamp ? event.timestamp.substring(11, 19) : ''",
                                    classes="text-grey",
                                )

                    # Expanded detail content
                    with v3.VListItem(
                        v_if="event.detail",
                    ):
                        html.Pre(
                            v_text="event.detail",
                            classes="text-caption text-grey pa-2",
                            style="white-space: pre-wrap; max-height: 200px; overflow-y: auto;",
                        )
