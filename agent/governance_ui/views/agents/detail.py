"""
Agent Detail View Component.

Per RULE-012: Single Responsibility - only agent detail UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-040: Effective config display.
Per GAP-UI-041: Agent-to-session/task relation links.
"""

from trame.widgets import vuetify3 as v3, html

from .capabilities import build_agent_capabilities_card
from .config import build_agent_config_card
from .controls import build_agent_controls_card
from .metrics import build_agent_metrics_card, build_trust_history_card
from .relations import build_agent_relations_card


def build_agent_detail_view() -> None:
    """Build agent detail view (GAP-UI-040, GAP-UI-041)."""
    with v3.VCard(
        v_if="active_view === 'agents' && show_agent_detail && selected_agent",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "agent-detail"}
    ):
        # Header
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="trigger('close_agent_detail')",
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-back-btn"}
            )
            with v3.VAvatar(
                color=(
                    "selected_agent.status === 'ACTIVE' ? 'success' : 'grey'",
                ),
                size="32",
                classes="mr-2"
            ):
                v3.VIcon("mdi-robot", color="white", size="small")
            html.Span(
                "{{ selected_agent.name || selected_agent.agent_id }}",
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-name"}
            )
            v3.VSpacer()
            v3.VChip(
                v_text="selected_agent.status",
                color=(
                    "selected_agent.status === 'ACTIVE' ? 'success' : 'grey'",
                ),
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-status"}
            )

        with v3.VCardText():
            # Metrics at top
            build_agent_metrics_card()

            # Trust history (GAP-UI-042)
            build_trust_history_card()

            # Capabilities (rule→agent bindings)
            build_agent_capabilities_card()

            # Config display
            build_agent_config_card()

            # Relations
            build_agent_relations_card()

            # Control actions (PLAN-UI-OVERHAUL-001 Task 3.2)
            build_agent_controls_card()
