"""
Agent Configuration Card Component.

Per RULE-012: Single Responsibility - only agent config display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-040: Effective config display.
"""

from trame.widgets import vuetify3 as v3, html


def build_agent_config_card() -> None:
    """Build agent configuration display card (GAP-UI-040)."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-config-card"}
    ):
        v3.VCardTitle("Configuration", density="compact")
        with v3.VCardText():
            with v3.VList(density="compact"):
                # Agent ID
                v3.VListItem(
                    title="Agent ID",
                    subtitle=("selected_agent.agent_id",),
                    prepend_icon="mdi-identifier"
                )
                # Agent Type
                v3.VListItem(
                    title="Type",
                    subtitle=("selected_agent.agent_type || 'N/A'",),
                    prepend_icon="mdi-cog"
                )
                # Model
                v3.VListItem(
                    v_if="selected_agent.model",
                    title="Model",
                    subtitle=("selected_agent.model",),
                    prepend_icon="mdi-brain"
                )
                # Instructions (truncated preview)
                v3.VListItem(
                    v_if="selected_agent.instructions",
                    title="Instructions",
                    subtitle=(
                        "(selected_agent.instructions || '').substring(0, 100) + "
                        "(selected_agent.instructions?.length > 100 ? '...' : '')",
                    ),
                    prepend_icon="mdi-text-box"
                )

            # Full instructions expandable
            with v3.VExpansionPanels(
                v_if="selected_agent.instructions?.length > 100",
                variant="accordion",
                classes="mt-2"
            ):
                with v3.VExpansionPanel():
                    v3.VExpansionPanelTitle("Full Instructions")
                    with v3.VExpansionPanelText():
                        html.Pre(
                            "{{ selected_agent.instructions }}",
                            style="white-space: pre-wrap; font-family: inherit; "
                                  "font-size: 0.875rem; margin: 0;",
                            __properties=["data-testid"],
                            **{"data-testid": "agent-instructions-full"}
                        )

            # Tools list
            with html.Div(
                v_if="selected_agent.tools?.length > 0",
                classes="mt-4"
            ):
                html.Div("Tools", classes="text-caption text-grey mb-2")
                v3.VChip(
                    v_for="tool in selected_agent.tools",
                    v_text="tool",
                    size="small",
                    color="secondary",
                    classes="mr-1 mb-1",
                    prepend_icon="mdi-wrench"
                )
