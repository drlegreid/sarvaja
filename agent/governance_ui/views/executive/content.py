"""
Executive Content Components.

Per RULE-012: Single Responsibility - only executive content area UI.
Per RULE-032: File size limit (<300 lines).
Per RULE-029: Executive Reporting Pattern.
"""

from trame.widgets import vuetify3 as v3, html

from .status import build_status_banner, build_session_evidence_section
from .metrics import build_metrics_summary
from .sections import build_report_sections


def build_executive_content() -> None:
    """Build the executive report content area."""
    with v3.VCardText():
        # Loading state
        with html.Div(v_if="executive_loading", classes="text-center py-8"):
            v3.VProgressCircular(indeterminate=True, color="primary")
            html.Div("Generating report...", classes="mt-2 text-grey")

        # Error state
        with v3.VAlert(
            v_if="executive_report && executive_report.error",
            type="error",
            density="compact",
        ):
            html.Span("{{ executive_report.error }}")

        # Report content
        with html.Div(
            v_if="executive_report && !executive_report.error && !executive_loading"
        ):
            # Status banner
            build_status_banner()

            # Session evidence summary (GAP-UI-046)
            build_session_evidence_section()

            # Metrics summary
            build_metrics_summary()

            # Report sections
            build_report_sections()

        # Empty state
        with html.Div(
            v_if="!executive_report && !executive_loading",
            classes="text-center py-8 text-grey"
        ):
            v3.VIcon("mdi-chart-box-outline", size="64", color="grey")
            html.Div(
                "Select a session and click 'Generate Report' to view executive summary",
                classes="mt-2"
            )
