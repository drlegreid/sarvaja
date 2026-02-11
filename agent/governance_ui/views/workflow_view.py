"""
Workflow Compliance Dashboard View.

Per RD-WORKFLOW Phase 4: Reporting & Alerts Dashboard.
Per RULE-020: Test Before Claim Protocol.
Per DOC-SIZE-01-v1: Proposals in workflow_proposals.py.

Shows:
- Workflow compliance status
- Validation checks (pass/fail/warning)
- Rule violations and recommendations
- Gap lifecycle tracking
- Governance proposal workflow
"""

from trame.widgets import vuetify3 as v3, html

from .workflow_proposals import (  # noqa: F401 — re-export
    build_proposal_form,
    build_proposal_graph_panel,
    build_proposal_history,
)


def build_workflow_header() -> None:
    """Build workflow dashboard header."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-check-decagram", classes="mr-2")
        html.Span("Workflow Compliance")
        v3.VSpacer()
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            click="trigger('load_workflow_status')",
            loading=("workflow_loading",),
            __properties=["data-testid"],
            **{"data-testid": "workflow-refresh-btn"}
        )


def build_compliance_summary() -> None:
    """Build compliance summary cards."""
    with v3.VRow():
        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                color=(
                    "workflow_status.overall === 'COMPLIANT' ? 'success' : "
                    "workflow_status.overall === 'WARNINGS' ? 'warning' : 'error'"
                ),
                __properties=["data-testid"],
                **{"data-testid": "workflow-status-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(
                        icon=(
                            "workflow_status.overall === 'COMPLIANT' ? 'mdi-check-circle' : "
                            "workflow_status.overall === 'WARNINGS' ? 'mdi-alert' : 'mdi-close-circle'"
                        ),
                        size="64",
                        color=(
                            "workflow_status.overall === 'COMPLIANT' ? 'success' : "
                            "workflow_status.overall === 'WARNINGS' ? 'warning' : 'error'"
                        )
                    )
                    html.Div(
                        "{{ workflow_status.overall || 'UNKNOWN' }}",
                        classes="text-h5 font-weight-bold mt-2"
                    )
                    html.Div("Compliance Status", classes="text-caption text-grey")

        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "workflow-passed-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(icon="mdi-check", size="64", color="success")
                    html.Div(
                        "{{ workflow_status.passed || 0 }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div("Checks Passed", classes="text-caption text-grey")

        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "workflow-issues-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(
                        icon="mdi-alert-circle",
                        size="64",
                        color=(
                            "(workflow_status.failed || 0) > 0 ? 'error' : "
                            "(workflow_status.warnings || 0) > 0 ? 'warning' : 'grey'"
                        )
                    )
                    html.Div(
                        "{{ (workflow_status.failed || 0) + (workflow_status.warnings || 0) }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div("Issues Found", classes="text-caption text-grey")


def build_validation_checks() -> None:
    """Build validation checks list."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "workflow-checks-card"}
            ):
                v3.VCardTitle("Validation Checks")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        with v3.VListItem(
                            v_for="(check, idx) in workflow_checks",
                            key="idx",
                            __properties=["data-testid"],
                            **{"data-testid": "workflow-check-item"}
                        ):
                            with html.Template(v_slot_prepend=True):
                                v3.VIcon(
                                    icon=(
                                        "check.status === 'PASS' ? 'mdi-check-circle' : "
                                        "check.status === 'FAIL' ? 'mdi-close-circle' : "
                                        "check.status === 'WARNING' ? 'mdi-alert' : 'mdi-help-circle'"
                                    ),
                                    color=(
                                        "check.status === 'PASS' ? 'success' : "
                                        "check.status === 'FAIL' ? 'error' : "
                                        "check.status === 'WARNING' ? 'warning' : 'grey'"
                                    ),
                                    size="small"
                                )
                            with v3.VListItemTitle():
                                html.Span(
                                    "{{ check.rule_id }}",
                                    classes="font-weight-bold mr-2"
                                )
                                html.Span(
                                    "{{ check.check_name }}",
                                    classes="text-grey mr-2"
                                )
                            with v3.VListItemSubtitle():
                                html.Span("{{ check.message }}")
                    html.Div(
                        "No compliance checks available",
                        v_if="!workflow_checks || workflow_checks.length === 0",
                        classes="text-center text-grey pa-4"
                    )


def build_violations_panel() -> None:
    """Build violations alert panel."""
    with v3.VRow(classes="mt-4", v_if="workflow_violations && workflow_violations.length > 0"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                color="error",
                __properties=["data-testid"],
                **{"data-testid": "workflow-violations-card"}
            ):
                with v3.VCardTitle(classes="text-error"):
                    v3.VIcon("mdi-alert-octagon", classes="mr-2")
                    html.Span("Violations")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        with v3.VListItem(
                            v_for="(violation, idx) in workflow_violations",
                            key="idx",
                            __properties=["data-testid"],
                            **{"data-testid": "workflow-violation-item"}
                        ):
                            with v3.VListItemTitle():
                                html.Span(
                                    "{{ violation.rule_id }}",
                                    classes="font-weight-bold mr-2"
                                )
                                html.Span("{{ violation.message }}")
                            with html.Template(v_slot_append=True):
                                v3.VBtn(
                                    "Create Task",
                                    size="x-small",
                                    variant="tonal",
                                    color="primary",
                                    prepend_icon="mdi-plus",
                                    click=(
                                        "active_view = 'tasks'; "
                                        "show_task_form = true; "
                                        "form_task_description = "
                                        "'Fix violation: ' + violation.rule_id + ' - ' + violation.message"
                                    ),
                                    __properties=["data-testid"],
                                    **{"data-testid": "violation-create-task-btn"}
                                )


def build_recommendations() -> None:
    """Build recommendations panel."""
    with v3.VRow(
        classes="mt-4",
        v_if="workflow_recommendations && workflow_recommendations.length > 0"
    ):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="tonal",
                color="info",
                __properties=["data-testid"],
                **{"data-testid": "workflow-recommendations-card"}
            ):
                with v3.VCardTitle():
                    v3.VIcon("mdi-lightbulb", classes="mr-2")
                    html.Span("Recommendations")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        with v3.VListItem(
                            v_for="(rec, idx) in workflow_recommendations",
                            key="idx"
                        ):
                            v3.VListItemTitle("{{ rec }}")


def build_workflow_view() -> None:
    """
    Build the Workflow Compliance Dashboard view.

    Main entry point for the workflow view module.
    Per RD-WORKFLOW Phase 4: Reporting & Alerts Dashboard.
    Per GOV-BICAM-01-v1: LangGraph governance proposal workflow.
    """
    with v3.VCard(
        v_if="active_view === 'workflow'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "workflow-dashboard"}
    ):
        build_workflow_header()

        with v3.VCardText():
            build_proposal_graph_panel()
            build_proposal_form()
            build_proposal_history()
            build_compliance_summary()
            build_validation_checks()
            build_violations_panel()
            build_recommendations()
