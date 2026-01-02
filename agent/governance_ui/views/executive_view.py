"""
Executive Report View for Governance Dashboard.

Per RULE-012: Single Responsibility - only executive report UI.
Per RULE-029: Executive Reporting Pattern.
Per RULE-032: File size limit - modularized into executive/ subpackage.
Per GAP-UI-046: Reports are per-session, not quarterly/monthly.

Module structure (RULE-032 compliant):
- executive/header.py: Header with session selector (~50 lines)
- executive/metrics.py: Metrics summary cards (~50 lines)
- executive/sections.py: Report sections (~55 lines)
- executive/status.py: Status banner and evidence section (~130 lines)
- executive/content.py: Main content area (~55 lines)
"""

from trame.widgets import vuetify3 as v3

from .executive import build_executive_header, build_executive_content


def build_executive_view() -> None:
    """
    Build the Executive Report view.

    This is the main entry point for the executive view module.
    Per RULE-029: Executive Reporting Pattern.
    Per GAP-UI-046: Reports are per-session with evidence summary.
    """
    with v3.VCard(
        v_if="active_view === 'executive'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "executive-report"}
    ):
        build_executive_header()
        build_executive_content()
