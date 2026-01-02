"""
Executive Header Components.

Per RULE-012: Single Responsibility - only executive header UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-046: Reports are per-session, not quarterly/monthly.
"""

from trame.widgets import vuetify3 as v3, html


def build_session_selector() -> None:
    """Build session selector for executive reports (GAP-UI-046)."""
    with html.Div(classes="d-flex align-center", style="gap: 8px;"):
        v3.VSelect(
            v_model="executive_session_id",
            items=(
                "sessions.map(s => ({title: s.session_id || s.id, "
                "value: s.session_id || s.id}))",
            ),
            label="Select Session",
            variant="outlined",
            density="compact",
            hide_details=True,
            style="max-width: 300px;",
            __properties=["data-testid"],
            **{"data-testid": "executive-session-select"}
        )
        v3.VBtn(
            "Generate Report",
            prepend_icon="mdi-file-chart",
            color="primary",
            size="small",
            click="trigger('load_executive_report')",
            disabled=("!executive_session_id",),
            __properties=["data-testid"],
            **{"data-testid": "executive-generate-btn"}
        )


def build_executive_header() -> None:
    """Build executive report header with session selector (GAP-UI-046)."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-chart-box", classes="mr-2")
        html.Span("Executive Report")
        v3.VSpacer()
        # Session selector (replaces period selector per GAP-UI-046)
        build_session_selector()
