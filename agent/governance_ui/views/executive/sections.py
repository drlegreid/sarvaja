"""
Executive Report Sections Components.

Per RULE-012: Single Responsibility - only report sections UI.
Per RULE-032: File size limit (<300 lines).
Per RULE-029: Executive Reporting Pattern.
Per PLAN-UI-OVERHAUL-001 Task 4.1: Expansion panels + section metrics.
"""

from trame.widgets import vuetify3 as v3, html


def build_report_sections() -> None:
    """Build report sections with expansion panels, metrics, and dynamic icons."""
    v3.VDivider(classes="mb-4")
    with v3.VExpansionPanels(
        v_model="executive_expanded_sections",
        multiple=True,
        __properties=["data-testid"],
        **{"data-testid": "executive-sections"}
    ):
        with v3.VExpansionPanel(
            v_for="(section, idx) in executive_report.sections",
            key=("idx",),
            __properties=["data-testid"],
            **{"data-testid": "executive-section"}
        ):
            with v3.VExpansionPanelTitle(classes="d-flex align-center"):
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
                html.Span("{{ section.title }}", classes="font-weight-medium")
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
                    classes="mr-2",
                )
            with v3.VExpansionPanelText():
                # Section-level metrics chips
                with html.Div(
                    v_if="section.metrics && Object.keys(section.metrics).length > 0",
                    classes="d-flex flex-wrap ga-1 mb-3"
                ):
                    v3.VChip(
                        v_for="(val, key) in section.metrics",
                        v_text="key + ': ' + val",
                        size="small",
                        variant="tonal",
                        color="primary",
                    )
                # Section content
                html.Pre(
                    "{{ section.content }}",
                    style="white-space: pre-wrap; font-family: inherit; "
                          "font-size: 0.875rem; margin: 0;",
                )
