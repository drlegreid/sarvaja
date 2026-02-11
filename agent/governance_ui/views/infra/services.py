"""
Infrastructure Services Grid.

Per GAP-INFRA-004: Service status cards for Podman, TypeDB, ChromaDB, etc.
Per DOC-SIZE-01-v1: Split from infra_view.py (710 lines).
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
        build_service_card(
            "podman", "Podman", "mdi-docker", "daemon", required=True
        )
        build_service_card(
            "typedb", "TypeDB", "mdi-database", "1729", required=True
        )
        build_service_card(
            "chromadb", "ChromaDB", "mdi-vector-square", "8001", required=True
        )
        build_service_card(
            "litellm", "LiteLLM", "mdi-api", "4000", required=False
        )
        build_service_card(
            "ollama", "Ollama", "mdi-robot", "11434", required=False
        )
