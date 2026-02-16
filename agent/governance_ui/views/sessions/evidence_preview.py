"""
Session Evidence Preview — Rendered HTML Display.

Per GAP-SESSION-DETAIL-002: Shows rendered evidence markdown
inline in session detail, instead of requiring file viewer.

Created: 2026-02-15
"""

from trame.widgets import vuetify3 as v3, html


def build_evidence_preview_card() -> None:
    """Build inline evidence preview with rendered HTML."""
    with v3.VCard(
        v_if="session_evidence_html",
        classes="mt-3",
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "session-evidence-preview"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon("mdi-file-document-check", classes="mr-2", size="small")
            html.Span("Evidence Preview")
            v3.VSpacer()
            v3.VChip(
                "Rendered",
                size="x-small",
                color="success",
                variant="tonal",
            )

        with v3.VCardText():
            # Loading state
            v3.VProgressLinear(
                v_if="session_evidence_loading",
                indeterminate=True,
                color="primary",
            )
            # Rendered HTML content
            html.Div(
                v_if="session_evidence_html && !session_evidence_loading",
                v_html="session_evidence_html",
                classes="evidence-rendered pa-2",
                style=(
                    "max-height: 400px; overflow-y: auto; "
                    "font-size: 0.875rem; line-height: 1.5;"
                ),
            )
