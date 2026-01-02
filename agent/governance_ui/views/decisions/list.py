"""
Decisions List View Component.

Per RULE-012: Single Responsibility - only decisions list UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html


def build_decisions_list_view() -> None:
    """
    Build the Decisions list view.

    Shows all strategic decisions with status and date.
    Clicking a decision opens the detail view.
    """
    with v3.VCard(
        v_if="active_view === 'decisions' && !show_decision_detail && !show_decision_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "decisions-list"}
    ):
        # Header with title and add button (GAP-UI-033)
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Strategic Decisions")
            v3.VSpacer()
            v3.VBtn(
                "Add Decision",
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

        # Decisions list content (GAP-UI-036: scrollable)
        with v3.VCardText(style="max-height: 500px; overflow-y: auto;"):
            html.Div(
                "{{ decisions.length }} decisions loaded",
                classes="mb-2 text-grey"
            )
            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "decisions-table"}
            ):
                with v3.VListItem(
                    v_for="decision in decisions",
                    **{":key": "decision.decision_id || decision.id"},
                    click="selected_decision = decision; show_decision_detail = true",
                    __properties=["data-testid"],
                    **{"data-testid": "decision-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon("mdi-scale-balance", color="primary")
                    with v3.VListItemTitle():
                        html.Span(
                            "{{ decision.decision_id || decision.id }}: "
                            "{{ decision.name || decision.title }}"
                        )
                    with v3.VListItemSubtitle():
                        # Status + date (GAP-UI-035)
                        v3.VChip(
                            v_text="decision.status",
                            size="x-small",
                            v_bind_color=(
                                "decision.status === 'APPROVED' ? 'success' : "
                                "decision.status === 'PENDING' ? 'warning' : 'error'"
                            ),
                            variant="tonal",
                            classes="mr-2"
                        )
                        html.Span(
                            v_text="decision.decision_date || decision.date || 'No date'",
                            classes="text-caption text-grey"
                        )
