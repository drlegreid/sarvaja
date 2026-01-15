"""
Trace Bar View Component.

Per GAP-UI-048: Bottom bar with technical traces.
Per TEST-UI-VERIFY-01-v1: UI must render, not just data layer.

Created: 2026-01-14
"""

from trame.widgets import vuetify3 as v3, html


def build_trace_bar() -> None:
    """
    Build the trace bar footer component.

    Shows:
    - Collapsed: Summary badge with last event
    - Expanded: Full trace event list with filtering
    """
    with v3.VFooter(
        app=True,
        color="grey-darken-4",
        height=("trace_bar_expanded ? 200 : 48",),
        __properties=["data-testid"],
        **{"data-testid": "trace-bar"}
    ):
        with v3.VContainer(fluid=True, classes="pa-0"):
            # Header row (always visible)
            with v3.VRow(
                no_gutters=True,
                align="center",
                classes="pa-2",
                style="cursor: pointer;",
                click="trace_bar_expanded = !trace_bar_expanded",
            ):
                # Left: Toggle icon and label
                v3.VIcon(
                    "mdi-console",
                    size="small",
                    color="white",
                    classes="mr-2",
                )
                html.Span("Trace", classes="text-white text-body-2 mr-4")

                # Summary badges (use array.length for Vue reactivity like rules view)
                v3.VChip(
                    "{{ trace_events.length }} events",
                    size="x-small",
                    color="grey",
                    variant="flat",
                    classes="mr-2",
                    __properties=["data-testid"],
                    **{"data-testid": "trace-total-badge"}
                )
                v3.VChip(
                    "{{ trace_events.filter(e => e.status_code >= 400 || e.event_type === 'error').length }} errors",
                    v_if="trace_events.filter(e => e.status_code >= 400 || e.event_type === 'error').length > 0",
                    size="x-small",
                    color="error",
                    variant="flat",
                    classes="mr-2",
                    __properties=["data-testid"],
                    **{"data-testid": "trace-error-badge"}
                )
                v3.VChip(
                    "{{ trace_events.filter(e => e.event_type === 'api_call').length }} API",
                    size="x-small",
                    color="info",
                    variant="flat",
                    classes="mr-2",
                )

                v3.VSpacer()

                # Last event preview (collapsed)
                html.Span(
                    "{{ trace_last_event }}",
                    v_if="!trace_bar_expanded && trace_last_event",
                    classes="text-grey text-caption mr-4",
                    style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
                )

                # Expand/collapse icon
                v3.VIcon(
                    "{{ trace_bar_expanded ? 'mdi-chevron-down' : 'mdi-chevron-up' }}",
                    size="small",
                    color="grey",
                )

            # Expanded content (trace list)
            with v3.VRow(
                v_if="trace_bar_expanded",
                no_gutters=True,
                classes="pa-2 pt-0",
            ):
                with v3.VCol(cols=12):
                    # Filter toolbar
                    with v3.VRow(no_gutters=True, align="center", classes="mb-2"):
                        with v3.VBtnToggle(
                            v_model="trace_filter",
                            density="compact",
                            variant="outlined",
                            divided=True,
                            color="grey",
                        ):
                            v3.VBtn("All", value=None, size="x-small")
                            v3.VBtn("API", value="api_call", size="x-small")
                            v3.VBtn("UI", value="ui_action", size="x-small")
                            v3.VBtn("Errors", value="error", size="x-small")

                        v3.VSpacer()

                        v3.VBtn(
                            "Clear",
                            variant="text",
                            size="x-small",
                            color="grey",
                            click="trigger('clear_traces')",
                            __properties=["data-testid"],
                            **{"data-testid": "trace-clear-btn"}
                        )

                    # Trace event list
                    with v3.VSheet(
                        color="grey-darken-3",
                        rounded=True,
                        classes="pa-2",
                        style="max-height: 120px; overflow-y: auto;",
                        __properties=["data-testid"],
                        **{"data-testid": "trace-list"}
                    ):
                        # Show events (filtered)
                        with v3.VList(density="compact", bg_color="transparent"):
                            with v3.VListItem(
                                v_for="(event, idx) in trace_events.slice().reverse()",
                                v_show="!trace_filter || event.event_type === trace_filter",
                                key="idx",
                                density="compact",
                            ):
                                # Time
                                html.Span(
                                    "{{ new Date(event.timestamp).toLocaleTimeString() }}",
                                    v_if="event.timestamp",
                                    classes="text-caption mr-2",
                                )
                                # Type icon
                                v3.VIcon(
                                    "mdi-api",
                                    v_if="event.event_type === 'api_call'",
                                    size="x-small",
                                    classes="mr-2",
                                )
                                v3.VIcon(
                                    "mdi-cursor-pointer",
                                    v_if="event.event_type === 'ui_action'",
                                    size="x-small",
                                    classes="mr-2",
                                )
                                v3.VIcon(
                                    "mdi-alert-circle",
                                    v_if="event.event_type === 'error'",
                                    size="x-small",
                                    color="error",
                                    classes="mr-2",
                                )
                                # Message
                                html.Span(
                                    "{{ event.message }}",
                                    classes="text-caption",
                                )
                                # Duration badge
                                v3.VChip(
                                    "{{ event.duration_ms }}ms",
                                    v_if="event.duration_ms",
                                    size="x-small",
                                    variant="text",
                                    classes="ml-2",
                                )
                                # Status badge
                                v3.VChip(
                                    "{{ event.status_code }}",
                                    v_if="event.status_code",
                                    size="x-small",
                                    variant="text",
                                    color="success",
                                    classes="ml-1",
                                )

                        # Empty state
                        html.Div(
                            "No trace events yet",
                            v_if="trace_events.length === 0",
                            classes="text-grey text-center pa-4",
                        )
