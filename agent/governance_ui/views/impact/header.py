"""
Impact Header Components.

Per RULE-012: Single Responsibility - only impact header UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html


def build_impact_header() -> None:
    """Build impact analyzer header with view toggle."""
    with v3.VCardTitle(classes="d-flex align-center"):
        html.Span("Rule Impact Analyzer")
        v3.VSpacer()
        # Graph/List toggle
        with v3.VBtnToggle(
            v_model="show_graph_view",
            density="compact",
            color="primary",
            mandatory=True,
            __properties=["data-testid"],
            **{"data-testid": "impact-view-toggle"}
        ):
            v3.VBtn(
                icon="mdi-graph",
                value=True,
                __properties=["data-testid"],
                **{"data-testid": "impact-graph-btn"}
            )
            v3.VBtn(
                icon="mdi-format-list-bulleted",
                value=False,
                __properties=["data-testid"],
                **{"data-testid": "impact-list-btn"}
            )


def build_rule_selector() -> None:
    """Build rule selector dropdown."""
    with v3.VRow():
        with v3.VCol(cols=4):
            v3.VSelect(
                v_model="impact_selected_rule",
                items=("rules.map(r => r.rule_id || r.id)",),
                label="Select Rule to Analyze",
                variant="outlined",
                density="compact",
                clearable=True,
                __properties=["data-testid"],
                **{"data-testid": "impact-rule-select"}
            )
