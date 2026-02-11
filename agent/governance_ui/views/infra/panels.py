"""
Infrastructure Operational Panels.

Per GAP-INFRA-004: DSP alerts, process viewer, logs, recovery actions.
Per DOC-SIZE-01-v1: Split from infra_view.py (710 lines).
"""

from trame.widgets import vuetify3 as v3, html


def build_dsp_alert() -> None:
    """Build DSP alert panel. Per SESSION-DSP-NOTIFY-01-v1.

    Shows prominent warning when DSP (Deep Sleep Protocol) is suggested.
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


def build_python_procs_panel() -> None:
    """Build Python process drill-down panel. Per C.4."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VExpansionPanels(
                v_model=("show_python_procs",),
                __properties=["data-testid"],
                **{"data-testid": "infra-python-procs-panel"}
            ):
                with v3.VExpansionPanel():
                    with v3.VExpansionPanelTitle(
                        click="trigger('load_python_processes')",
                    ):
                        v3.VIcon("mdi-language-python", classes="mr-2")
                        html.Span("Python Process Details")
                        v3.VSpacer()
                        v3.VChip(
                            v_text=(
                                "(infra_python_procs || []).length + ' processes'",
                            ),
                            size="small",
                            variant="tonal",
                        )
                    with v3.VExpansionPanelText():
                        with v3.VTable(
                            v_if="infra_python_procs && infra_python_procs.length > 0",
                            density="compact",
                        ):
                            with html.Thead():
                                with html.Tr():
                                    html.Th("PID")
                                    html.Th("CPU %")
                                    html.Th("MEM %")
                                    html.Th("Command")
                            with html.Tbody():
                                with html.Tr(
                                    v_for="proc in infra_python_procs",
                                ):
                                    html.Td(
                                        "{{ proc.pid }}",
                                        classes="font-weight-medium",
                                    )
                                    html.Td("{{ proc.cpu }}%")
                                    html.Td("{{ proc.mem }}%")
                                    html.Td(
                                        "{{ proc.command }}",
                                        classes="text-caption",
                                        style="max-width: 400px; overflow: hidden; "
                                              "text-overflow: ellipsis;",
                                    )
                        v3.VAlert(
                            v_if="!infra_python_procs || infra_python_procs.length === 0",
                            type="info",
                            density="compact",
                            text="No Python processes found.",
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
