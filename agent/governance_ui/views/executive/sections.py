"""
Executive Report Sections Components.

Per RULE-012: Single Responsibility - only report sections UI.
Per RULE-032: File size limit (<300 lines).
Per RULE-029: Executive Reporting Pattern.
"""

from trame.widgets import vuetify3 as v3, html


def build_report_sections() -> None:
    """Build report sections with dynamic icons."""
    v3.VDivider(classes="mb-4")
    with html.Div(
        v_for="(section, idx) in executive_report.sections",
        key=("idx",),
    ):
        with v3.VCard(
            variant="outlined",
            classes="mb-3",
            __properties=["data-testid"],
            **{"data-testid": "executive-section"}
        ):
            with v3.VCardTitle(
                density="compact",
                classes="d-flex align-center",
            ):
                v3.VIcon(
                    v_bind_icon=(
                        "section.title.includes('Summary') ? 'mdi-clipboard-text' : "
                        "section.title.includes('Compliance') ? 'mdi-check-decagram' : "
                        "section.title.includes('Risk') ? 'mdi-alert-circle' : "
                        "section.title.includes('Alignment') ? 'mdi-compass' : "
                        "section.title.includes('Resource') ? 'mdi-account-group' : "
                        "section.title.includes('Recommendation') ? 'mdi-lightbulb' : "
                        "section.title.includes('Objective') ? 'mdi-target' : "
                        "'mdi-file-document'",
                    ),
                    classes="mr-2",
                    size="small"
                )
                html.Span("{{ section.title }}")
                v3.VSpacer()
                v3.VChip(
                    v_if="section.status",
                    v_text="section.status",
                    v_bind_color=(
                        "section.status === 'success' ? 'success' : "
                        "section.status === 'warning' ? 'warning' : 'error'"
                    ),
                    size="small",
                    density="compact",
                )
            with v3.VCardText():
                html.P("{{ section.content }}", classes="mb-0")
