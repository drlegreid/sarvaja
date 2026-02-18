"""
Agent Metrics and Trust History Components.

Per RULE-012: Single Responsibility - only agent metrics display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-042: Trust score history and explanation.
"""

from trame.widgets import vuetify3 as v3, html


def build_agent_metrics_card() -> None:
    """Build agent metrics display card. Per UI-RESP-01-v1: Responsive."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-metrics-card"}
    ):
        v3.VCardTitle("Metrics", density="compact")
        with v3.VCardText():
            with v3.VRow():
                with v3.VCol(cols=12, sm=4):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ ((selected_agent.trust_score || 0) * 100).toFixed(0) }}%",
                            classes="text-h4"
                        )
                        html.Div("Trust Score", classes="text-caption text-grey")
                with v3.VCol(cols=12, sm=4):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ selected_agent.tasks_executed || 0 }}",
                            classes="text-h4"
                        )
                        html.Div("Tasks Executed", classes="text-caption text-grey")
                with v3.VCol(cols=12, sm=4):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ selected_agent.sessions_count || 0 }}",
                            classes="text-h4"
                        )
                        html.Div("Sessions", classes="text-caption text-grey")

            # Last active
            html.Div(
                v_if="selected_agent.last_active",
                classes="text-center mt-4 text-caption text-grey"
            ).add_child(
                html.Span("Last active: {{ selected_agent.last_active }}")
            )


def build_trust_components_breakdown() -> None:
    """Build trust score components breakdown. Per UI-RESP-01-v1."""
    with v3.VRow(
        v_if="selected_agent.trust_components",
        classes="mb-4"
    ):
        with v3.VCol(cols=6, sm=3):
            with html.Div(classes="text-center"):
                v3.VProgressCircular(
                    model_value=(
                        "(selected_agent.trust_components?.compliance || 0) * 100",
                    ),
                    size=60,
                    width=4,
                    color="primary"
                )
                html.Div("Compliance", classes="text-caption mt-1")
        with v3.VCol(cols=6, sm=3):
            with html.Div(classes="text-center"):
                v3.VProgressCircular(
                    model_value=(
                        "(selected_agent.trust_components?.accuracy || 0) * 100",
                    ),
                    size=60,
                    width=4,
                    color="success"
                )
                html.Div("Accuracy", classes="text-caption mt-1")
        with v3.VCol(cols=6, sm=3):
            with html.Div(classes="text-center"):
                v3.VProgressCircular(
                    model_value=(
                        "(selected_agent.trust_components?.consistency || 0) * 100",
                    ),
                    size=60,
                    width=4,
                    color="warning"
                )
                html.Div("Consistency", classes="text-caption mt-1")
        with v3.VCol(cols=6, sm=3):
            with html.Div(classes="text-center"):
                v3.VProgressCircular(
                    model_value=(
                        "(selected_agent.trust_components?.tenure || 0) * 100",
                    ),
                    size=60,
                    width=4,
                    color="info"
                )
                html.Div("Tenure", classes="text-caption mt-1")


def build_trust_history_timeline() -> None:
    """Build trust score changes timeline."""
    html.Div("Recent Changes", classes="font-weight-bold mb-2")
    with v3.VTimeline(
        v_if="selected_agent.trust_history?.length > 0",
        density="compact",
        align="start",
        __properties=["data-testid"],
        **{"data-testid": "trust-history-timeline"}
    ):
        with v3.VTimelineItem(
            v_for="(event, idx) in selected_agent.trust_history",
            # BUG-186-003: Use dynamic binding, not static string
            **{":key": "idx"},
            dot_color=(
                "event.change > 0 ? 'success' : "
                "event.change < 0 ? 'error' : 'grey'",
            ),
            size="small"
        ):
            with v3.VCard(density="compact", variant="outlined"):
                with v3.VCardText(classes="py-2"):
                    with html.Div(classes="d-flex align-center"):
                        v3.VIcon(
                            # BUG-186-001: Use icon prop, not v_text (renders text, not icon)
                            icon=(
                                "event.change > 0 ? 'mdi-arrow-up' : "
                                "event.change < 0 ? 'mdi-arrow-down' : "
                                "'mdi-minus'"
                            ),
                            color=(
                                "event.change > 0 ? 'success' : "
                                "event.change < 0 ? 'error' : 'grey'",
                            ),
                            size="small",
                            classes="mr-1"
                        )
                        html.Span(
                            # BUG-282-METRICS-001: Guard against null event.change / event.new_score → NaN
                            "{{ event.change > 0 ? '+' : '' }}"
                            "{{ ((event.change || 0) * 100).toFixed(1) }}%",
                            classes="font-weight-bold"
                        )
                        html.Span(
                            " → {{ ((event.new_score || 0) * 100).toFixed(0) }}%",
                            classes="text-grey ml-1"
                        )
                    html.Div(
                        "{{ event.reason || 'No reason provided' }}",
                        classes="text-body-2 mt-1"
                    )
                    html.Div(
                        "{{ event.timestamp }}",
                        classes="text-caption text-grey mt-1"
                    )

    # No history message
    with v3.VAlert(
        v_if="!selected_agent.trust_history?.length",
        type_="info",
        variant="tonal",
        density="compact"
    ):
        html.Span("No trust score changes recorded")


def build_trust_history_card() -> None:
    """Build trust score history card (GAP-UI-042)."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-trust-history-card"}
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            html.Span("Trust Score History")
            v3.VSpacer()
            v3.VBtn(
                icon="mdi-refresh",
                variant="text",
                size="small",
                click="trigger('load_trust_history', [selected_agent.agent_id])",
                __properties=["data-testid"],
                **{"data-testid": "trust-history-refresh"}
            )
        with v3.VCardText():
            # Current trust breakdown (RULE-011 formula)
            with v3.VAlert(
                type_="info",
                variant="tonal",
                density="compact",
                classes="mb-4"
            ):
                html.Div("Trust Formula (RULE-011):", classes="font-weight-bold mb-2")
                html.Div(
                    "(Compliance × 0.4) + (Accuracy × 0.3) + "
                    "(Consistency × 0.2) + (Tenure × 0.1)",
                    classes="text-caption font-italic"
                )

            # Trust components breakdown
            build_trust_components_breakdown()

            # No components message
            with v3.VAlert(
                v_if="!selected_agent.trust_components",
                type_="warning",
                variant="tonal",
                density="compact",
                classes="mb-4"
            ):
                html.Span("Trust component breakdown not available")

            # Trust history timeline
            build_trust_history_timeline()
