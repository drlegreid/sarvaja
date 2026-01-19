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
        # Frankel Hash
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


def build_mcp_status_panel() -> None:
    """Build MCP server status panel. Per UI-AUDIT-011."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "infra-mcp-status"}
            ):
                v3.VCardTitle("MCP Server Status")
                with v3.VCardText():
                    with v3.VRow(dense=True):
                        # Display MCP servers from healthcheck state
                        with v3.VCol(
                            v_for="(status, name) in (infra_stats.mcp_servers || {})",
                            key="name",
                            cols=6,
                            md=3
                        ):
                            with v3.VChip(
                                color=("status === 'OK' ? 'success' : 'warning'",),
                                size="small",
                                variant="flat",
                                classes="ma-1"
                            ):
                                v3.VIcon(
                                    icon=("status === 'OK' ? 'mdi-check-circle' : 'mdi-alert-circle'",),
                                    size="small",
                                    classes="mr-1"
                                )
                                html.Span("{{ name }}")
                    # Empty state
                    v3.VAlert(
                        v_if="!infra_stats.mcp_servers || Object.keys(infra_stats.mcp_servers).length === 0",
                        type="info",
                        density="compact",
                        text="MCP server status not available. Run healthcheck to update."
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
            # Services status grid
            build_services_grid()

            # System stats
            build_system_stats()

            # Recovery actions
            build_recovery_panel()
