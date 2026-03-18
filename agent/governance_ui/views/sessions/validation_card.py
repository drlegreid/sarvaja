"""
Session Content Validation Card.

Per RELIABILITY-PLAN-01-v1 P1: Surface validation data (thoughts, MCP, tool pairing)
in the session detail view for auditability.
"""

from trame.widgets import vuetify3 as v3, html


def build_validation_card() -> None:
    """Build content validation summary card for session detail.

    Shows metrics from /sessions/{id}/validate endpoint:
    - Tool call pairing (total, orphaned, errors)
    - MCP server distribution
    - Thinking blocks metrics
    - Parse quality
    """
    with v3.VCard(
        v_if="session_validation_data",
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "session-validation-card"}
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-shield-check-outline", size="small", classes="mr-2")
            html.Span("Content Validation")
            v3.VSpacer()
            v3.VProgressCircular(
                v_if="session_validation_loading",
                indeterminate=True,
                size=20,
                width=2
            )
            v3.VChip(
                v_if="session_validation_data && session_validation_data.valid",
                text="Valid",
                size="x-small",
                color="success",
                prepend_icon="mdi-check-circle",
            )
            v3.VChip(
                v_if="session_validation_data && !session_validation_data.valid",
                text="Issues Found",
                size="x-small",
                color="warning",
                prepend_icon="mdi-alert-circle",
            )

        with v3.VCardText():
            # Summary row with key metrics
            with v3.VRow(dense=True, classes="mb-2"):
                # Entries
                with v3.VCol(cols=6, sm=3):
                    _metric_chip("mdi-file-document", "Entries",
                                 "session_validation_data.entry_count || 0", "info")
                # Tool pairing
                with v3.VCol(cols=6, sm=3):
                    _metric_chip(
                        "mdi-link-variant", "Tool Pairs",
                        "session_validation_data.tool_calls_total || 0",
                        "(session_validation_data.orphaned_tool_calls || 0) > 0 ? 'warning' : 'success'"
                    )
                # MCP calls
                with v3.VCol(cols=6, sm=3):
                    _metric_chip("mdi-cloud-outline", "MCP Calls",
                                 "session_validation_data.mcp_calls_total || 0", "secondary")
                # Thinking
                with v3.VCol(cols=6, sm=3):
                    _metric_chip("mdi-head-lightbulb-outline", "Thinking",
                                 "session_validation_data.thinking_blocks_total || 0", "warning")

            # Detail rows
            with v3.VTable(density="compact"):
                with html.Tbody():
                    # Messages
                    _detail_row("User Messages",
                                "session_validation_data.user_messages || 0")
                    _detail_row("Assistant Messages",
                                "session_validation_data.assistant_messages || 0")
                    # Tool pairing detail
                    _detail_row("Tool Calls (total)",
                                "session_validation_data.tool_calls_total || 0")
                    _detail_row("Tool Results",
                                "session_validation_data.tool_results_total || 0")
                    _detail_row("Orphaned Calls",
                                "session_validation_data.orphaned_tool_calls || 0",
                                warn_expr="(session_validation_data.orphaned_tool_calls || 0) > 0")
                    _detail_row("Tool Errors",
                                "session_validation_data.tool_errors || 0",
                                warn_expr="(session_validation_data.tool_errors || 0) > 0")
                    # MCP detail
                    _detail_row("MCP with Server",
                                "session_validation_data.mcp_calls_with_server || 0")
                    _detail_row("MCP without Server",
                                "session_validation_data.mcp_calls_without_server || 0",
                                warn_expr="(session_validation_data.mcp_calls_without_server || 0) > 0")
                    # Thinking
                    _detail_row("Thinking Chars",
                                "session_validation_data.thinking_chars_total || 0")
                    _detail_row("Empty Thinking",
                                "session_validation_data.thinking_blocks_empty || 0",
                                warn_expr="(session_validation_data.thinking_blocks_empty || 0) > 0")
                    # Parse quality
                    _detail_row("Parse Errors",
                                "session_validation_data.parse_errors || 0",
                                warn_expr="(session_validation_data.parse_errors || 0) > 0")

            # MCP Server Distribution
            with html.Div(
                v_if="session_validation_data.mcp_server_distribution "
                     "&& Object.keys(session_validation_data.mcp_server_distribution).length > 0",
                classes="mt-3",
            ):
                html.Div("MCP Server Distribution", classes="text-subtitle-2 mb-1")
                v3.VChip(
                    v_for="(count, server) in session_validation_data.mcp_server_distribution",
                    key="server",
                    v_text="server + ': ' + count",
                    size="small",
                    variant="tonal",
                    color="secondary",
                    classes="mr-1 mb-1",
                    __properties=["data-testid"],
                    **{"data-testid": "mcp-server-chip"}
                )


def _metric_chip(icon: str, label: str, value_expr: str, color: str) -> None:
    """Render a small metric summary chip."""
    with html.Div(classes="text-center"):
        v3.VIcon(icon, size="small", classes="mb-1")
        html.Div(
            v_text=value_expr,
            classes="text-h6 font-weight-bold"
        )
        html.Div(label, classes="text-caption text-grey")


def _detail_row(label: str, value_expr: str, warn_expr: str = None) -> None:
    """Render a key-value table row with optional warning highlight."""
    with html.Tr():
        html.Td(label, classes="text-caption", style="width: 60%")
        with html.Td(
            classes="text-right",
            style="width: 40%",
        ):
            html.Span(
                v_text=value_expr,
                v_bind_class=(
                    f"{warn_expr} ? 'text-warning font-weight-bold' : ''"
                    if warn_expr else "''"
                ),
            )
