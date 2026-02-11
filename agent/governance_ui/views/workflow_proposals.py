"""
Workflow Proposal UI Components.

Per DOC-SIZE-01-v1: Extracted from workflow_view.py (528 lines).
LangGraph proposal graph, submission form, and history panel.
"""

from trame.widgets import vuetify3 as v3, html


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
                    with v3.VStepper(
                        v_if="workflow_info && workflow_info.phases",
                        non_linear=True,
                        alt_labels=True,
                        __properties=["data-testid"],
                        **{"data-testid": "workflow-phase-stepper"}
                    ):
                        with v3.VStepperHeader():
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
