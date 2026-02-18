"""
Executive Metrics Components.

Per RULE-012: Single Responsibility - only metrics summary UI.
Per RULE-032: File size limit (<300 lines).
Per RULE-029: Executive Reporting Pattern.
"""

from trame.widgets import vuetify3 as v3, html


def build_metrics_summary() -> None:
    """Build clickable metrics summary cards. Per UI-RESP-01-v1, PLAN-UI-OVERHAUL-001 Task 4.1."""
    with v3.VRow(classes="mb-4"):
        with v3.VCol(cols=12, sm=6, md=3):
            with v3.VCard(
                variant="outlined",
                classes="text-center pa-2",
                hover=True,
                click="active_view = 'rules'",
                style="cursor: pointer",
                __properties=["data-testid"],
                **{"data-testid": "metric-rules-card"},
            ):
                v3.VIcon("mdi-gavel", size="large", color="primary")
                html.Div(
                    "{{ executive_report.metrics_summary?.total_rules || 0 }}",
                    classes="text-h5 mt-1"
                )
                html.Div("Rules", classes="text-caption")
        with v3.VCol(cols=12, sm=6, md=3):
            with v3.VCard(
                variant="outlined",
                classes="text-center pa-2",
                hover=True,
                click="active_view = 'agents'",
                style="cursor: pointer",
                __properties=["data-testid"],
                **{"data-testid": "metric-agents-card"},
            ):
                v3.VIcon("mdi-robot", size="large", color="info")
                html.Div(
                    "{{ executive_report.metrics_summary?.total_agents || 0 }}",
                    classes="text-h5 mt-1"
                )
                html.Div("Agents", classes="text-caption")
        with v3.VCol(cols=12, sm=6, md=3):
            with v3.VCard(
                variant="outlined",
                classes="text-center pa-2",
                hover=True,
                click="active_view = 'tasks'",
                style="cursor: pointer",
                __properties=["data-testid"],
                **{"data-testid": "metric-tasks-card"},
            ):
                v3.VIcon("mdi-checkbox-marked", size="large", color="success")
                html.Div(
                    "{{ executive_report.metrics_summary?.tasks_completed || 0 }}",
                    classes="text-h5 mt-1"
                )
                html.Div("Tasks Done", classes="text-caption")
        with v3.VCol(cols=12, sm=6, md=3):
            with v3.VCard(
                variant="outlined",
                classes="text-center pa-2",
                hover=True,
                # BUG-223-COMPLIANCE-001: 'compliance' is not a valid view; use 'rules'
                click="active_view = 'rules'",
                style="cursor: pointer",
                __properties=["data-testid"],
                **{"data-testid": "metric-compliance-card"},
            ):
                v3.VIcon("mdi-percent", size="large", color="warning")
                html.Div(
                    # BUG-282-EXEC-001: Guard against Infinity/NaN from division-by-zero
                    "{{ isFinite(executive_report.metrics_summary?.compliance_rate)"
                    " ? (executive_report.metrics_summary.compliance_rate).toFixed(0)"
                    " : '0' }}%",
                    classes="text-h5 mt-1"
                )
                html.Div("Compliance", classes="text-caption")
