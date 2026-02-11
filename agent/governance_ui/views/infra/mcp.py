"""
Infrastructure MCP Server Status Panels.

Per UI-AUDIT-011: MCP server readiness and tool counts.
Per DOC-SIZE-01-v1: Split from infra_view.py (710 lines).
"""

from trame.widgets import vuetify3 as v3, html


def build_mcp_status_panel() -> None:
    """Build MCP server status panel with readiness and tool counts."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "infra-mcp-status"}
            ):
                v3.VCardTitle("MCP Server Status")
                with v3.VCardText():
                    # Empty state
                    v3.VAlert(
                        v_if="!infra_stats.mcp_details || Object.keys(infra_stats.mcp_details).length === 0",
                        type="info",
                        density="compact",
                        text="MCP server status not available. Run healthcheck to update."
                    )
                    # Enhanced details table with readiness
                    with v3.VTable(
                        v_if="infra_stats.mcp_details && Object.keys(infra_stats.mcp_details).length > 0",
                        density="compact"
                    ):
                        with html.Thead():
                            with html.Tr():
                                html.Th("Server")
                                html.Th("Status")
                                html.Th("Ready")
                                html.Th("Tools")
                                html.Th("Dependencies")
                                html.Th("Description")
                        with html.Tbody():
                            with html.Tr(
                                v_for="(detail, sname) in infra_stats.mcp_details",
                                key="sname",
                                click="mcp_selected_server = sname; show_mcp_detail = true",
                                style="cursor: pointer;",
                            ):
                                html.Td("{{ sname }}", classes="font-weight-medium")
                                with html.Td():
                                    v3.VChip(
                                        v_text=(
                                            "(infra_stats.mcp_servers || {})[sname] || 'ON-DEMAND'",
                                        ),
                                        size="x-small",
                                        color=(
                                            "(infra_stats.mcp_servers || {})[sname] === 'OK' "
                                            "? 'success' : 'info'",
                                        ),
                                        variant="flat",
                                    )
                                with html.Td():
                                    v3.VChip(
                                        v_text="detail.ready",
                                        size="x-small",
                                        color=(
                                            "detail.ready === 'READY' ? 'success' : 'error'",
                                        ),
                                        variant="flat",
                                    )
                                html.Td("{{ detail.tools || 0 }}", classes="text-center")
                                with html.Td():
                                    v3.VChip(
                                        v_for="dep in (detail.depends_on || [])",
                                        v_text="dep",
                                        size="x-small",
                                        variant="outlined",
                                        classes="mr-1",
                                    )
                                    html.Span(
                                        v_if="!detail.depends_on || detail.depends_on.length === 0",
                                        v_text="'none'",
                                        classes="text-caption text-grey",
                                    )
                                html.Td(
                                    "{{ detail.desc || detail.comment || '-' }}",
                                    classes="text-caption",
                                )


def build_mcp_detail_dialog() -> None:
    """Build MCP server detail dialog. Per C.2."""
    with v3.VDialog(
        v_model=("show_mcp_detail",),
        max_width=600,
    ):
        with v3.VCard(v_if="mcp_selected_server"):
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon("mdi-server-network", classes="mr-2")
                html.Span("{{ mcp_selected_server }}")
                v3.VSpacer()
                v3.VBtn(
                    icon="mdi-close",
                    variant="text",
                    click="show_mcp_detail = false",
                )
            with v3.VCardText():
                # Status chips
                with html.Div(classes="mb-3"):
                    v3.VChip(
                        v_text=(
                            "(infra_stats.mcp_servers || {})"
                            "[mcp_selected_server] || 'ON-DEMAND'",
                        ),
                        color=(
                            "(infra_stats.mcp_servers || {})"
                            "[mcp_selected_server] === 'OK' "
                            "? 'success' : 'info'",
                        ),
                        variant="flat",
                        classes="mr-2",
                    )
                    v3.VChip(
                        v_text=(
                            "infra_stats.mcp_details && "
                            "infra_stats.mcp_details[mcp_selected_server] "
                            "? infra_stats.mcp_details[mcp_selected_server].ready "
                            ": 'UNKNOWN'",
                        ),
                        color=(
                            "infra_stats.mcp_details && "
                            "infra_stats.mcp_details[mcp_selected_server] && "
                            "infra_stats.mcp_details[mcp_selected_server].ready === 'READY' "
                            "? 'success' : 'error'",
                        ),
                        variant="flat",
                    )
                # Command
                with html.Div(classes="mb-3"):
                    html.Div("Command", classes="text-subtitle-2 text-grey")
                    html.Pre(
                        (
                            "infra_stats.mcp_details && "
                            "infra_stats.mcp_details[mcp_selected_server] "
                            "? infra_stats.mcp_details[mcp_selected_server].command "
                            ": 'N/A'",
                        ),
                        style=(
                            "font-size: 12px; background: #1e1e1e; "
                            "color: #d4d4d4; padding: 8px; border-radius: 4px; "
                            "white-space: pre-wrap; word-break: break-all;"
                        ),
                    )
                # Tools & Dependencies
                with v3.VRow():
                    with v3.VCol(cols=6):
                        html.Div("Registered Tools", classes="text-subtitle-2 text-grey")
                        html.Div(
                            (
                                "infra_stats.mcp_details && "
                                "infra_stats.mcp_details[mcp_selected_server] "
                                "? infra_stats.mcp_details[mcp_selected_server].tools "
                                ": 0",
                            ),
                            classes="text-h5 font-weight-bold",
                        )
                    with v3.VCol(cols=6):
                        html.Div("Dependencies", classes="text-subtitle-2 text-grey")
                        with html.Div(classes="d-flex flex-wrap ga-1 mt-1"):
                            v3.VChip(
                                v_for=(
                                    "dep in ("
                                    "infra_stats.mcp_details && "
                                    "infra_stats.mcp_details[mcp_selected_server] "
                                    "? infra_stats.mcp_details[mcp_selected_server].depends_on "
                                    ": [])"
                                ),
                                v_text="dep",
                                size="small",
                                variant="outlined",
                            )
                            html.Span(
                                "None",
                                v_if=(
                                    "!infra_stats.mcp_details || "
                                    "!infra_stats.mcp_details[mcp_selected_server] || "
                                    "!infra_stats.mcp_details[mcp_selected_server].depends_on || "
                                    "infra_stats.mcp_details[mcp_selected_server]"
                                    ".depends_on.length === 0"
                                ),
                                classes="text-caption text-grey",
                            )
                # Description
                with html.Div(classes="mt-3"):
                    html.Div("Description", classes="text-subtitle-2 text-grey")
                    html.Div(
                        (
                            "infra_stats.mcp_details && "
                            "infra_stats.mcp_details[mcp_selected_server] "
                            "? (infra_stats.mcp_details[mcp_selected_server].desc || "
                            "infra_stats.mcp_details[mcp_selected_server].comment || "
                            "'N/A') : 'N/A'",
                        ),
                        classes="text-body-2",
                    )
