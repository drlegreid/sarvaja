"""
Session Tool Calls Drill-Down Component.

Per RULE-012: Single Responsibility - only tool call display UI.
Per RULE-032: File size limit (<300 lines).
Per PLAN-UI-OVERHAUL-001 Task 5.2: Session Drill-Down with tool call metadata.
"""

from trame.widgets import vuetify3 as v3, html


def build_tool_calls_card() -> None:
    """Build tool calls drill-down section for session detail."""
    with v3.VCard(
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-tool-calls"}
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-tools", size="small", classes="mr-2")
            html.Span("Tool Calls")
            v3.VSpacer()
            v3.VProgressCircular(
                v_if="session_tool_calls_loading",
                indeterminate=True,
                size=20,
                width=2
            )
            v3.VChip(
                v_if="!session_tool_calls_loading && session_tool_calls",
                v_text="session_tool_calls.length",
                size="x-small",
                color="primary",
                classes="ml-2"
            )
        with v3.VCardText():
            # No tool calls message
            html.Div(
                "No tool call data available for this session",
                v_if=(
                    "!session_tool_calls_loading && "
                    "(!session_tool_calls || session_tool_calls.length === 0)"
                ),
                classes="text-grey text-center py-4"
            )

            # Tool calls expansion panels
            with v3.VExpansionPanels(
                v_if="session_tool_calls && session_tool_calls.length > 0",
                variant="accordion",
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "tool-calls-panels"}
            ):
                with v3.VExpansionPanel(
                    v_for="(call, idx) in session_tool_calls",
                    # BUG-290-TC-001: Use dynamic Vue key binding, not static tuple
                    **{":key": "idx"},
                ):
                    with v3.VExpansionPanelTitle(classes="d-flex align-center"):
                        v3.VIcon(
                            v_bind_icon=(
                                "call.is_mcp ? 'mdi-cloud-outline' : 'mdi-wrench'"
                            ),
                            size="small",
                            classes="mr-2"
                        )
                        # BUG-427-XSS-001: Use v_text instead of mustache to prevent XSS on tool_name
                        html.Span(
                            v_text="call.tool_name",
                            classes="font-weight-medium"
                        )
                        v3.VSpacer()
                        v3.VChip(
                            v_if="call.latency_ms",
                            v_text="call.latency_ms + 'ms'",
                            size="x-small",
                            variant="tonal",
                            color="info",
                            classes="mr-2"
                        )
                        v3.VChip(
                            v_if="call.is_mcp",
                            v_text="call.server_name || 'MCP'",
                            size="x-small",
                            variant="tonal",
                            color="secondary"
                        )
                    with v3.VExpansionPanelText():
                        # Input summary
                        with html.Div(classes="mb-2"):
                            html.Div("Input", classes="text-caption text-grey")
                            # BUG-350-XSS-002: Use v_text instead of mustache to prevent XSS
                            html.Pre(
                                v_text="call.input_summary || 'N/A'",
                                style="white-space: pre-wrap; font-family: monospace; "
                                      "font-size: 0.8rem; padding: 8px; "
                                      "border-radius: 4px; margin: 0;",
                                classes="bg-surface-variant"
                            )
                        # Output/result
                        with html.Div(
                            v_if="call.output_summary",
                        ):
                            html.Div("Output", classes="text-caption text-grey")
                            # BUG-350-XSS-002: Use v_text instead of mustache to prevent XSS
                            html.Pre(
                                v_text="call.output_summary",
                                style="white-space: pre-wrap; font-family: monospace; "
                                      "font-size: 0.8rem; padding: 8px; "
                                      "border-radius: 4px; margin: 0; "
                                      "max-height: 200px; overflow-y: auto;",
                                classes="bg-surface-variant"
                            )

    # Thinking items section
    _build_thinking_items_card()


def _build_thinking_items_card() -> None:
    """Build thinking/reasoning items display for session detail."""
    with v3.VCard(
        v_if="session_thinking_items && session_thinking_items.length > 0",
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-thinking-items"}
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-head-lightbulb-outline", size="small", classes="mr-2")
            html.Span("Thinking / Reasoning")
            v3.VSpacer()
            v3.VChip(
                v_text="session_thinking_items.length",
                size="x-small",
                color="warning",
                classes="ml-2"
            )
        with v3.VCardText():
            with v3.VExpansionPanels(
                variant="accordion",
                density="compact",
            ):
                with v3.VExpansionPanel(
                    v_for="(thought, idx) in session_thinking_items",
                    # BUG-290-TC-001: Use dynamic Vue key binding, not static tuple
                    **{":key": "idx"},
                ):
                    with v3.VExpansionPanelTitle():
                        v3.VIcon("mdi-thought-bubble", size="small", classes="mr-2")
                        html.Span(
                            "{{ 'Thinking block #' + (idx + 1) + "
                            "' (' + (thought.chars || 0) + ' chars)' }}"
                        )
                    with v3.VExpansionPanelText():
                        # BUG-350-XSS-002: Use v_text instead of mustache to prevent XSS
                        html.Pre(
                            v_text="thought.content",
                            style="white-space: pre-wrap; font-family: monospace; "
                                  "font-size: 0.8rem; padding: 8px; "
                                  "border-radius: 4px; margin: 0; "
                                  "max-height: 400px; overflow-y: auto;",
                            classes="bg-surface-variant"
                        )
