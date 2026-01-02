"""
Trust Dashboard Main View Component.

Per RULE-012: Single Responsibility - main dashboard layout.
Per RULE-032: File size limit (<300 lines).
Per RULE-011: Multi-Agent Governance Protocol.
"""

from trame.widgets import vuetify3 as v3

from .stats import build_trust_header, build_governance_stats
from .panels import (
    build_trust_leaderboard,
    build_proposals_panel,
    build_escalated_proposals_alert,
)


def build_trust_dashboard_view() -> None:
    """Build the main trust dashboard view."""
    with v3.VCard(
        v_if="active_view === 'trust' && !show_agent_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "trust-dashboard"}
    ):
        build_trust_header()

        with v3.VCardText():
            # Governance stats cards
            build_governance_stats()

            # Trust leaderboard and proposals
            with v3.VRow(classes="mt-4"):
                build_trust_leaderboard()
                build_proposals_panel()

            # Escalated proposals alert
            build_escalated_proposals_alert()
