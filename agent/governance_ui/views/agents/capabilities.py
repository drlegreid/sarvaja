"""
Agent Capabilities Panel Component.

Per RULE-012: Single Responsibility - only agent capability bindings.
Per RULE-032: File size limit (<300 lines).
Shows which governance rules are bound to the selected agent.
"""

from trame.widgets import vuetify3 as v3, html


def build_agent_capabilities_card() -> None:
    """Build agent capabilities card showing rule→agent bindings."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-capabilities-card"}
    ):
        with v3.VCardTitle(
            classes="d-flex align-center", density="compact"
        ):
            v3.VIcon("mdi-shield-key", size="small", classes="mr-2")
            html.Span("Governing Rules")
            v3.VSpacer()
            v3.VChip(
                v_text="(agent_capabilities || []).length + ' bindings'",
                size="x-small",
                color="info",
                variant="tonal",
            )

        with v3.VCardText():
            # Loading state
            v3.VProgressLinear(
                v_if="agent_capabilities_loading",
                indeterminate=True,
                color="primary",
                height=2,
            )

            # Empty state
            with html.Div(
                v_if="!agent_capabilities_loading && "
                     "(!agent_capabilities || agent_capabilities.length === 0)",
                classes="text-grey text-center py-4"
            ):
                v3.VIcon(
                    "mdi-shield-off-outline",
                    size="large",
                    color="grey",
                    classes="mb-2"
                )
                html.Div("No governance rules bound to this agent")

            # Capabilities list
            with v3.VList(
                v_if="agent_capabilities && agent_capabilities.length > 0",
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "capabilities-list"}
            ):
                with v3.VListItem(
                    v_for="cap in agent_capabilities",
                    **{":key": "cap.rule_id"},
                    __properties=["data-testid"],
                    **{"data-testid": "capability-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon(
                            "mdi-gavel",
                            size="small",
                            color=(
                                "cap.status === 'active' ? 'success' : 'grey'",
                            ),
                        )
                    with v3.VListItemTitle():
                        html.Span("{{ cap.rule_id }}")
                    with v3.VListItemSubtitle():
                        html.Span(
                            "{{ cap.category || 'general' }}"
                        )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="cap.status || 'active'",
                            size="x-small",
                            color=(
                                "cap.status === 'active' ? 'success' : 'grey'",
                            ),
                            variant="tonal",
                        )
