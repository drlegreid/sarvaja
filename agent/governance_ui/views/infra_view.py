"""
Infrastructure Health Dashboard View.

Per RULE-021: MCP Healthcheck Protocol.
Per GAP-INFRA-004: Docker/Podman health dashboard.
Per RULE-012: Single Responsibility - only infrastructure health UI.

Shows real-time status of:
- Podman daemon
- TypeDB container (port 1729)
- ChromaDB container (port 8001)
- LiteLLM container (port 4000)
- Ollama container (port 11434)
"""

from trame.widgets import vuetify3 as v3, html


def build_infra_header() -> None:
    """Build infrastructure dashboard header."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-server", classes="mr-2")
        html.Span("Infrastructure Health")
        v3.VSpacer()
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            click="trigger('load_infra_status')",
            loading=("infra_loading",),
            __properties=["data-testid"],
            **{"data-testid": "infra-refresh-btn"}
        )


def build_service_card(
    service_id: str,
    title: str,
    icon: str,
    port: str,
    required: bool = True
) -> None:
    """Build a service status card."""
    status_expr = f"infra_services.{service_id}"
    is_ok = f"({status_expr} && {status_expr}.ok)"

    with v3.VCol(cols=12, md=6, lg=4):
        with v3.VCard(
            variant="outlined",
            color=(f"{is_ok} ? 'success' : 'error'",),
            click=(
                f"infra_log_container = '{service_id}'; "
                f"trigger('load_container_logs', ['{service_id}', 50, ''])"
            ),
            style="cursor: pointer;",
            __properties=["data-testid"],
            **{"data-testid": f"infra-card-{service_id}"}
        ):
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon(
                    icon=icon,
                    color=(f"{is_ok} ? 'success' : 'error'",),
                    classes="mr-2"
                )
                html.Span(title)
                v3.VSpacer()
                v3.VChip(
                    v_text=(f"{status_expr} ? {status_expr}.status : 'UNKNOWN'",),
                    color=(f"{is_ok} ? 'success' : 'error'",),
                    size="small",
                    variant="flat"
                )
            with v3.VCardText():
                with v3.VRow(dense=True):
                    with v3.VCol(cols=6):
                        html.Div("Port:", classes="text-caption text-grey")
                        html.Div(port, classes="font-weight-medium")
                    with v3.VCol(cols=6):
                        html.Div("Type:", classes="text-caption text-grey")
                        html.Div(
                            "Required" if required else "Optional",
                            classes="font-weight-medium"
                        )
            with v3.VCardActions(v_if=f"!{is_ok}"):
                v3.VBtn(
                    f"Start {title}",
                    prepend_icon="mdi-play",
                    variant="tonal",
                    color="primary",
                    size="small",
                    click=f"trigger('start_service', {{service: '{service_id}'}})",
                    __properties=["data-testid"],
                    **{"data-testid": f"infra-start-{service_id}"}
                )


def build_services_grid() -> None:
    """Build the services status grid."""
    with v3.VRow():
        # Required services
        build_service_card(
            "podman", "Podman", "mdi-docker", "daemon", required=True
        )
        build_service_card(
            "typedb", "TypeDB", "mdi-database", "1729", required=True
        )
        build_service_card(
            "chromadb", "ChromaDB", "mdi-vector-square", "8001", required=True
        )
        # Optional services
        build_service_card(
            "litellm", "LiteLLM", "mdi-api", "4000", required=False
        )
        build_service_card(
            "ollama", "Ollama", "mdi-robot", "11434", required=False
        )


def build_system_stats() -> None:
    """Build system stats panel."""
    with v3.VRow(classes="mt-4"):
        # Memory usage
        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "infra-stat-memory"}
            ):
                with v3.VCardText():
                    html.Div("Memory Usage", classes="text-subtitle-2 text-grey")
                    html.Div(
                        "{{ infra_stats.memory_pct || 0 }}%",
                        classes="text-h4 font-weight-bold"
                    )
                    v3.VProgressLinear(
                        model_value=("infra_stats.memory_pct || 0",),
                        color=(
                            "infra_stats.memory_pct > 85 ? 'error' : "
                            "infra_stats.memory_pct > 70 ? 'warning' : 'success'"
                        ),
                        height=8,
                        rounded=True
                    )
        # Process count
        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "infra-stat-procs"}
            ):
                with v3.VCardText():
                    html.Div("Python Processes", classes="text-subtitle-2 text-grey")
                    html.Div(
                        "{{ infra_stats.python_procs || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div(
                        v_if="infra_stats.python_procs > 20",
                        classes="text-caption text-warning"
                    ).__setattr__("innerHTML", "Consider cleanup")
        # Frankel Hash with component breakdown (Plan 7.3)
        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "infra-stat-hash"}
            ):
                with v3.VCardText():
                    html.Div("Health Hash", classes="text-subtitle-2 text-grey")
                    html.Div(
                        "{{ infra_stats.frankel_hash || '--------' }}",
                        classes="text-h5 font-weight-bold font-mono"
                    )
                    html.Div(
                        "{{ infra_stats.last_check || 'Never' }}",
                        classes="text-caption text-grey"
                    )
                    # Component hash breakdown
                    with html.Div(
                        v_if=(
                            "infra_stats.component_hashes && "
                            "Object.keys(infra_stats.component_hashes).length > 0"
                        ),
                        classes="mt-2"
                    ):
                        html.Div(
                            "Components",
                            classes="text-caption text-grey mb-1"
                        )
                        with html.Div(
                            v_for=(
                                "(hash, name) in "
                                "(infra_stats.component_hashes || {})"
                            ),
                            classes="d-flex justify-space-between align-center"
                        ):
                            html.Span(
                                "{{ name }}",
                                classes="text-caption"
                            )
                            v3.VChip(
                                v_text="hash",
                                size="x-small",
                                variant="outlined",
                                color=(
                                    "infra_stats.component_statuses && "
                                    "infra_stats.component_statuses[name] === 'OK' "
                                    "? 'success' : 'error'",
                                ),
                                classes="font-mono"
                            )


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
                            ):
                                # Server name
                                html.Td("{{ sname }}", classes="font-weight-medium")
                                # Healthcheck status chip
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
                                # Backend readiness chip
                                with html.Td():
                                    v3.VChip(
                                        v_text="detail.ready",
                                        size="x-small",
                                        color=(
                                            "detail.ready === 'READY' ? 'success' : 'error'",
                                        ),
                                        variant="flat",
                                    )
                                # Tool count
                                html.Td("{{ detail.tools || 0 }}", classes="text-center")
                                # Dependencies
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
                                # Description
                                html.Td(
                                    "{{ detail.desc || detail.comment || '-' }}",
                                    classes="text-caption",
                                )


def build_dsp_alert() -> None:
    """
    Build DSP alert panel. Per SESSION-DSP-NOTIFY-01-v1.

    Shows prominent warning when DSP (Deep Sleep Protocol) is suggested.
    Not buried in JSON health output - dedicated visual alert.
    """
    with v3.VRow(classes="mb-4"):
        with v3.VCol(cols=12):
            with v3.VAlert(
                v_if="infra_stats.dsp_suggested",
                type="warning",
                prominent=True,
                border="start",
                closable=False,
                __properties=["data-testid"],
                **{"data-testid": "infra-dsp-alert"}
            ):
                with v3.VRow(align="center"):
                    with v3.VCol(cols="auto"):
                        v3.VIcon("mdi-sleep", size="x-large", color="warning")
                    with v3.VCol():
                        html.Div(
                            "DSP Required - Document Entropy High",
                            classes="text-h6 font-weight-bold"
                        )
                        html.Div(
                            "{{ infra_stats.dsp_alerts ? infra_stats.dsp_alerts.join(' • ') : 'Run /deep-sleep or type OVERRIDE' }}",
                            classes="text-body-2"
                        )
                    with v3.VCol(cols="auto"):
                        v3.VBtn(
                            "View DSP Guide",
                            prepend_icon="mdi-book-open-outline",
                            variant="tonal",
                            color="warning",
                            href="https://github.com/drlegreid/platform-gai/blob/master/docs/rules/leaf/SESSION-DSM-01-v1.md",
                            target="_blank",
                            __properties=["data-testid"],
                            **{"data-testid": "infra-dsp-guide-btn"}
                        )


def build_logs_panel() -> None:
    """Build container logs viewer panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "infra-logs-panel"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    v3.VIcon("mdi-text-box-outline", classes="mr-2")
                    html.Span("Container Logs")
                    v3.VSpacer()
                    v3.VSelect(
                        v_model=("infra_log_container",),
                        items=("['dashboard', 'typedb', 'chromadb', 'litellm', 'ollama']",),
                        density="compact",
                        hide_details=True,
                        style="max-width: 160px;",
                        classes="mr-2",
                        __properties=["data-testid"],
                        **{"data-testid": "logs-container-select"}
                    )
                    v3.VSelect(
                        v_model=("infra_log_level",),
                        items=("['', 'ERROR', 'WARNING', 'INFO']",),
                        density="compact",
                        hide_details=True,
                        label="Level",
                        clearable=True,
                        style="max-width: 120px;",
                        classes="mr-2"
                    )
                    v3.VBtn(
                        "Load Logs",
                        prepend_icon="mdi-refresh",
                        variant="outlined",
                        size="small",
                        click=(
                            "trigger('load_container_logs', "
                            "[infra_log_container, 50, infra_log_level])"
                        ),
                        __properties=["data-testid"],
                        **{"data-testid": "logs-refresh-btn"}
                    )
                with v3.VCardText():
                    html.Pre(
                        v_if="infra_log_lines && infra_log_lines.length > 0",
                        v_text="infra_log_lines.join('\\n')",
                        style=(
                            "max-height: 300px; overflow-y: auto; "
                            "font-size: 12px; background: #1e1e1e; "
                            "color: #d4d4d4; padding: 12px; border-radius: 4px; "
                            "white-space: pre-wrap; word-break: break-all;"
                        ),
                        __properties=["data-testid"],
                        **{"data-testid": "logs-output"}
                    )
                    v3.VAlert(
                        v_if="!infra_log_lines || infra_log_lines.length === 0",
                        type="info",
                        density="compact",
                        text="Click 'Load Logs' to fetch container logs."
                    )


def build_recovery_panel() -> None:
    """Build recovery actions panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "infra-recovery"}
            ):
                v3.VCardTitle("Recovery Actions")
                with v3.VCardText():
                    with v3.VRow():
                        with v3.VCol(cols=12, md=4):
                            v3.VBtn(
                                "Start All Services",
                                prepend_icon="mdi-play-circle",
                                variant="tonal",
                                color="success",
                                block=True,
                                click="trigger('start_all_services')",
                                __properties=["data-testid"],
                                **{"data-testid": "infra-start-all"}
                            )
                        with v3.VCol(cols=12, md=4):
                            v3.VBtn(
                                "Restart Stack",
                                prepend_icon="mdi-restart",
                                variant="tonal",
                                color="warning",
                                block=True,
                                click="trigger('restart_stack')",
                                __properties=["data-testid"],
                                **{"data-testid": "infra-restart"}
                            )
                        with v3.VCol(cols=12, md=4):
                            v3.VBtn(
                                "Cleanup Zombies",
                                prepend_icon="mdi-broom",
                                variant="tonal",
                                color="error",
                                block=True,
                                click="trigger('cleanup_zombies')",
                                __properties=["data-testid"],
                                **{"data-testid": "infra-cleanup"}
                            )
                with v3.VCardText(v_if="infra_last_action"):
                    v3.VAlert(
                        v_text="infra_last_action",
                        type="info",
                        density="compact",
                        closable=True
                    )


def build_infra_view() -> None:
    """
    Build the Infrastructure Health Dashboard view.

    Main entry point for the infra view module.
    Per GAP-INFRA-004: Docker/Podman health dashboard.
    """
    with v3.VCard(
        v_if="active_view === 'infra'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "infra-dashboard"}
    ):
        build_infra_header()

        with v3.VCardText():
            # DSP Alert (most prominent per SESSION-DSP-NOTIFY-01-v1)
            build_dsp_alert()

            # Services status grid
            build_services_grid()

            # System stats
            build_system_stats()

            # MCP server status (UI-AUDIT-011)
            build_mcp_status_panel()

            # Container logs viewer
            build_logs_panel()

            # Recovery actions
            build_recovery_panel()
