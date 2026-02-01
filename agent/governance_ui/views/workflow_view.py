"""
Workflow Compliance Dashboard View.

Per RD-WORKFLOW Phase 4: Reporting & Alerts Dashboard.
Per RULE-020: Test Before Claim Protocol.
Per RULE-012: Single Responsibility - only workflow compliance UI.

Shows:
- Workflow compliance status
- Validation checks (pass/fail/warning)
- Rule violations and recommendations
- Gap lifecycle tracking
"""

from trame.widgets import vuetify3 as v3, html


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
        # Overall Status Card
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
                    html.Div(
                        "Compliance Status",
                        classes="text-caption text-grey"
                    )

        # Checks Passed
        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "workflow-passed-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(
                        icon="mdi-check",
                        size="64",
                        color="success"
                    )
                    html.Div(
                        "{{ workflow_status.passed || 0 }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div(
                        "Checks Passed",
                        classes="text-caption text-grey"
                    )

        # Issues
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
                    html.Div(
                        "Issues Found",
                        classes="text-caption text-grey"
                    )


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
                    # Use VList instead of VDataTable for better Trame binding
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
                    # Show empty state if no checks
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


def build_proposal_graph_panel() -> None:
    """Build LangGraph workflow graph visualization."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "workflow-graph-panel"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    v3.VIcon("mdi-graph", classes="mr-2", color="primary")
                    html.Span("Governance Proposal Workflow")
                    v3.VSpacer()
                    v3.VChip(
                        v_text=(
                            "workflow_info && workflow_info.langgraph_available "
                            "? 'LangGraph Active' : 'Fallback Mode'",
                        ),
                        size="small",
                        color=(
                            "workflow_info && workflow_info.langgraph_available "
                            "? 'success' : 'warning'",
                        ),
                        variant="tonal"
                    )
                with v3.VCardText():
                    # Phase stepper visualization
                    with v3.VStepper(
                        v_if="workflow_info && workflow_info.phases",
                        non_linear=True,
                        alt_labels=True,
                        __properties=["data-testid"],
                        **{"data-testid": "workflow-phase-stepper"}
                    ):
                        with v3.VStepperHeader():
                            # Build phase steps dynamically
                            with html.Template(
                                v_for="(phase, idx) in (workflow_info.phases || [])",
                            ):
                                v3.VStepperItem(
                                    v_bind_title="phase.name",
                                    v_bind_icon="phase.icon",
                                    v_bind_value="idx + 1",
                                    color="primary",
                                    complete=True,
                                )
                                v3.VDivider(v_if="idx < (workflow_info.phases || []).length - 1")
                    # Threshold info
                    with v3.VRow(
                        dense=True,
                        classes="mt-3",
                        v_if="workflow_info && workflow_info.thresholds"
                    ):
                        with v3.VCol(cols=4):
                            with v3.VChip(size="small", variant="tonal", color="info"):
                                html.Span(
                                    "Quorum: {{ (workflow_info.thresholds.quorum * 100) }}%"
                                )
                        with v3.VCol(cols=4):
                            with v3.VChip(size="small", variant="tonal", color="success"):
                                html.Span(
                                    "Approval: {{ (workflow_info.thresholds.approval * 100).toFixed(0) }}%"
                                )
                        with v3.VCol(cols=4):
                            with v3.VChip(size="small", variant="tonal", color="warning"):
                                html.Span(
                                    "Dispute: {{ (workflow_info.thresholds.dispute * 100) }}%"
                                )
                    # Not loaded
                    v3.VAlert(
                        v_if="!workflow_info",
                        type="info",
                        density="compact",
                        text="Click Refresh to load workflow graph information."
                    )


def build_proposal_form() -> None:
    """Build proposal submission form."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "proposal-form-panel"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    v3.VIcon("mdi-send", classes="mr-2", color="primary")
                    html.Span("Submit Governance Proposal")
                with v3.VCardText():
                    with v3.VRow(dense=True):
                        with v3.VCol(cols=12, md=4):
                            v3.VSelect(
                                v_model=("proposal_action",),
                                items=("['create', 'modify', 'deprecate']",),
                                label="Action",
                                density="compact",
                                __properties=["data-testid"],
                                **{"data-testid": "proposal-action"}
                            )
                        with v3.VCol(cols=12, md=4):
                            v3.VTextField(
                                v_model=("proposal_rule_id",),
                                label="Rule ID (for modify/deprecate)",
                                density="compact",
                                __properties=["data-testid"],
                                **{"data-testid": "proposal-rule-id"}
                            )
                        with v3.VCol(cols=12, md=4):
                            v3.VSwitch(
                                v_model=("proposal_dry_run",),
                                label="Dry Run",
                                density="compact",
                                color="primary",
                                hide_details=True,
                            )
                    v3.VTextarea(
                        v_model=("proposal_hypothesis",),
                        label="Hypothesis (what and why)",
                        rows=2,
                        density="compact",
                        __properties=["data-testid"],
                        **{"data-testid": "proposal-hypothesis"}
                    )
                    v3.VTextarea(
                        v_model=("proposal_evidence",),
                        label="Evidence (comma-separated)",
                        rows=2,
                        density="compact",
                        __properties=["data-testid"],
                        **{"data-testid": "proposal-evidence"}
                    )
                    v3.VTextarea(
                        v_model=("proposal_directive",),
                        label="Directive (for create/modify)",
                        rows=2,
                        density="compact",
                        __properties=["data-testid"],
                        **{"data-testid": "proposal-directive"}
                    )
                with v3.VCardActions():
                    v3.VBtn(
                        "Submit Proposal",
                        prepend_icon="mdi-send",
                        color="primary",
                        variant="tonal",
                        click="trigger('submit_proposal')",
                        loading=("proposal_submitting",),
                        __properties=["data-testid"],
                        **{"data-testid": "proposal-submit-btn"}
                    )

    # Result display
    with v3.VRow(classes="mt-2", v_if="proposal_result"):
        with v3.VCol(cols=12):
            with v3.VAlert(
                type=(
                    "proposal_result.decision === 'approved' ? 'success' : "
                    "proposal_result.decision === 'rejected' ? 'error' : 'info'",
                ),
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "proposal-result"}
            ):
                html.Div(
                    "Proposal {{ proposal_result.proposal_id }}: "
                    "{{ proposal_result.decision.toUpperCase() }}",
                    classes="font-weight-bold"
                )
                html.Div("{{ proposal_result.decision_reasoning }}")
                with v3.VRow(dense=True, classes="mt-2"):
                    with v3.VCol(cols=3):
                        html.Span(
                            "Impact: {{ proposal_result.impact_score }}",
                            classes="text-caption"
                        )
                    with v3.VCol(cols=3):
                        html.Span(
                            "Risk: {{ proposal_result.risk_level }}",
                            classes="text-caption"
                        )
                    with v3.VCol(cols=3):
                        html.Span(
                            "Votes: {{ proposal_result.votes_for.toFixed(1) }} / "
                            "{{ proposal_result.votes_against.toFixed(1) }}",
                            classes="text-caption"
                        )
                    with v3.VCol(cols=3):
                        html.Span(
                            "Phases: {{ proposal_result.phases_completed.join(' → ') }}",
                            classes="text-caption"
                        )


def build_proposal_history() -> None:
    """Build proposal history panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "proposal-history-panel"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    v3.VIcon("mdi-history", classes="mr-2")
                    html.Span("Proposal History")
                    v3.VSpacer()
                    v3.VChip(
                        v_text="(proposal_history || []).length + ' proposals'",
                        size="small",
                        variant="tonal"
                    )
                with v3.VCardText():
                    with v3.VList(
                        v_if="proposal_history && proposal_history.length > 0",
                        density="compact"
                    ):
                        with v3.VListItem(
                            v_for="(p, idx) in proposal_history",
                            key="idx",
                        ):
                            with html.Template(v_slot_prepend=True):
                                v3.VIcon(
                                    icon=(
                                        "p.decision === 'approved' ? 'mdi-check-circle' : "
                                        "p.decision === 'rejected' ? 'mdi-close-circle' : "
                                        "'mdi-clock-outline'"
                                    ),
                                    color=(
                                        "p.decision === 'approved' ? 'success' : "
                                        "p.decision === 'rejected' ? 'error' : 'info'"
                                    ),
                                    size="small"
                                )
                            v3.VListItemTitle(
                                "{{ p.proposal_id }} — {{ p.action }} "
                                "{{ p.decision.toUpperCase() }}"
                            )
                            v3.VListItemSubtitle(
                                "Impact: {{ p.impact_score }} | "
                                "Risk: {{ p.risk_level }} | "
                                "{{ p.dry_run ? '[DRY RUN]' : '[LIVE]' }}"
                            )
                    v3.VAlert(
                        v_if="!proposal_history || proposal_history.length === 0",
                        type="info",
                        density="compact",
                        text="No proposals submitted yet. Use the form above to submit a governance proposal."
                    )


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
            # LangGraph proposal workflow graph
            build_proposal_graph_panel()

            # Proposal submission form
            build_proposal_form()

            # Proposal history
            build_proposal_history()

            # Compliance summary
            build_compliance_summary()

            # Validation checks table
            build_validation_checks()

            # Violations panel
            build_violations_panel()

            # Recommendations
            build_recommendations()
