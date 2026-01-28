"""
Decision Log View Component.

Per UI-AUDIT-2026-01-19: Repurposed from "Strategic Decisions" to "Decision Log".
Per RULE-012: Single Responsibility - only decision log UI.
Per RULE-032: File size limit (<300 lines).

Decision Log shows:
- Decisions linked to sessions as audit trail
- Claude Code-style options with evidence references
- Customizable options based on user input
"""

from trame.widgets import vuetify3 as v3, html


def build_decisions_list_view() -> None:
    """
    Build the Decision Log list view.

    Per UI-AUDIT-2026-01-19: Session-linked decisions with evidence trail.
    Shows all decisions grouped by session with options and rationale.
    """
    with v3.VCard(
        v_if="active_view === 'decisions' && !show_decision_detail && !show_decision_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "decision-log"}
    ):
        # Header (UI-AUDIT-2026-01-19: renamed to Decision Log)
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon("mdi-file-document-edit", classes="mr-2")
            html.Span("Decision Log")
            v3.VSpacer()
            # Session filter
            v3.VSelect(
                v_model="decision_session_filter",
                items=("decision_session_options",),
                label="Session",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 250px",
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "decision-session-filter"}
            )
            v3.VBtn(
                "Record Decision",
                color="primary",
                prepend_icon="mdi-plus",
                click="decision_form_mode = 'create'; show_decision_form = true",
                __properties=["data-testid"],
                **{"data-testid": "decisions-add-btn"}
            )

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "decisions-loading"}
        )

        # Decision Log content (UI-AUDIT-2026-01-19: session-linked)
        with v3.VCardText(style="max-height: 500px; overflow-y: auto;"):
            html.Div(
                "{{ decisions.length }} decisions in log",
                classes="mb-2 text-grey"
            )
            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "decision-log-list"}
            ):
                with v3.VListItem(
                    v_for="decision in decisions",
                    v_show=(
                        "!decision_session_filter || "
                        "decision.session_id === decision_session_filter"
                    ),
                    **{":key": "decision.decision_id || decision.id"},
                    click="selected_decision = decision; show_decision_detail = true",
                    __properties=["data-testid"],
                    **{"data-testid": "decision-log-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon("mdi-checkbox-marked-circle", color="success")
                    with v3.VListItemTitle():
                        html.Span(
                            "{{ decision.question || decision.name || decision.title }}"
                        )
                    with v3.VListItemSubtitle():
                        # Session link + selected option (UI-AUDIT-2026-01-19)
                        with html.Div(classes="d-flex flex-wrap align-center"):
                            v3.VChip(
                                v_if="decision.session_id",
                                v_text="decision.session_id",
                                size="x-small",
                                color="info",
                                variant="tonal",
                                prepend_icon="mdi-calendar",
                                classes="mr-1"
                            )
                            v3.VChip(
                                v_if="decision.selected_option",
                                v_text="decision.selected_option",
                                size="x-small",
                                color="success",
                                variant="flat",
                                prepend_icon="mdi-check",
                                classes="mr-1"
                            )
                            v3.VChip(
                                v_if="decision.evidence_refs?.length > 0",
                                v_text="decision.evidence_refs.length + ' evidence'",
                                size="x-small",
                                color="warning",
                                variant="tonal",
                                prepend_icon="mdi-file-document",
                                classes="mr-1"
                            )
                            html.Span(
                                v_text="decision.timestamp || decision.date || ''",
                                classes="text-caption text-grey ml-1"
                            )
