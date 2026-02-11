"""
Infrastructure System Stats Panel.

Per GAP-INFRA-004: Memory, process, and health hash displays.
Per DOC-SIZE-01-v1: Split from infra_view.py (710 lines).
"""

from trame.widgets import vuetify3 as v3, html


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
                    with html.Div(classes="d-flex align-center"):
                        html.Div("Memory Usage", classes="text-subtitle-2 text-grey")
                        with v3.VTooltip(location="top"):
                            with html.Template(v_slot_activator="{ props }"):
                                v3.VIcon(
                                    "mdi-information-outline",
                                    size="x-small",
                                    classes="ml-1 text-grey",
                                    v_bind="props",
                                )
                            html.Span("Green: <70% | Yellow: 70-85% | Red: >85%")
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
                    with html.Div(classes="d-flex align-center"):
                        html.Div("Python Processes", classes="text-subtitle-2 text-grey")
                        with v3.VTooltip(location="top"):
                            with html.Template(v_slot_activator="{ props }"):
                                v3.VIcon(
                                    "mdi-information-outline",
                                    size="x-small",
                                    classes="ml-1 text-grey",
                                    v_bind="props",
                                )
                            html.Span("Warning at >20 processes. Normal: 5-15.")
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
                    with html.Div(classes="d-flex align-center"):
                        html.Div("Health Hash", classes="text-subtitle-2 text-grey")
                        with v3.VTooltip(location="top"):
                            with html.Template(v_slot_activator="{ props }"):
                                v3.VIcon(
                                    "mdi-information-outline",
                                    size="x-small",
                                    classes="ml-1 text-grey",
                                    v_bind="props",
                                )
                            html.Span(
                                "8-char hash of service states. "
                                "Changes when any service status changes."
                            )
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
