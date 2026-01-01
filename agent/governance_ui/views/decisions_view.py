"""
Decisions View for Governance Dashboard.

Per RULE-012: Single Responsibility - only decisions list/detail UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 2106-2229.
"""

from trame.widgets import vuetify3 as v3, html


def build_decisions_list_view() -> None:
    """
    Build the Decisions list view.

    Shows all strategic decisions with status and date.
    Clicking a decision opens the detail view.
    """
    with v3.VCard(
        v_if="active_view === 'decisions' && !show_decision_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "decisions-list"}
    ):
        v3.VCardTitle("Strategic Decisions")
        with v3.VCardText():
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
                        html.Span("{{ decision.date }} | {{ decision.status }}")


def build_decision_metadata_chips() -> None:
    """Build decision metadata chips."""
    with v3.VChipGroup(classes="mt-3"):
        v3.VChip(
            v_text="selected_decision.status || 'N/A'",
            color=(
                "selected_decision.status === 'APPROVED' ? 'success' : "
                "selected_decision.status === 'REJECTED' ? 'error' : 'info'",
            ),
            __properties=["data-testid"],
            **{"data-testid": "decision-detail-status"}
        )
        v3.VChip(
            v_text="selected_decision.date || 'No date'",
            prepend_icon="mdi-calendar",
            __properties=["data-testid"],
            **{"data-testid": "decision-detail-date"}
        )


def build_decision_info_cards() -> None:
    """Build decision information and impact cards."""
    with v3.VRow(classes="mt-4"):
        # Left column: Decision information
        with v3.VCol(cols=6):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-info"}
            ):
                v3.VCardTitle("Decision Information", density="compact")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            title="Decision ID",
                            subtitle=(
                                "selected_decision.decision_id || selected_decision.id",
                            ),
                            prepend_icon="mdi-identifier",
                        )
                        v3.VListItem(
                            title="Date",
                            subtitle=("selected_decision.date || 'N/A'",),
                            prepend_icon="mdi-calendar",
                        )
                        v3.VListItem(
                            title="Status",
                            subtitle=("selected_decision.status || 'N/A'",),
                            prepend_icon="mdi-check-circle",
                        )
        # Right column: Impact
        with v3.VCol(cols=6):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-impact"}
            ):
                v3.VCardTitle("Impact", density="compact")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            title="Affected Rules",
                            subtitle=(
                                "(selected_decision.affected_rules || []).length + "
                                "' rules'",
                            ),
                            prepend_icon="mdi-gavel",
                        )
                        v3.VListItem(
                            title="Category",
                            subtitle=("selected_decision.category || 'N/A'",),
                            prepend_icon="mdi-tag",
                        )


def build_decision_detail_view() -> None:
    """
    Build the Decision detail view.

    Shows decision details including rationale and impact.
    """
    with v3.VCard(
        v_if="active_view === 'decisions' && show_decision_detail && selected_decision",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "decision-detail"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_decision_detail = false; selected_decision = null",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-back-btn"}
            )
            html.Span(
                "{{ selected_decision.decision_id || selected_decision.id }}",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-id"}
            )

        with v3.VCardText():
            # Decision title
            html.H2(
                "{{ selected_decision.name || selected_decision.title }}",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-title"}
            )

            # Metadata chips
            build_decision_metadata_chips()

            # Decision rationale
            v3.VDivider(classes="my-4")
            html.H3("Rationale")
            html.P(
                "{{ selected_decision.rationale || selected_decision.description || "
                "'No rationale provided' }}",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-rationale"}
            )

            # Decision details
            build_decision_info_cards()


def build_decisions_view() -> None:
    """
    Build the complete Decisions view including list and detail.

    This is the main entry point for the decisions view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    """
    build_decisions_list_view()
    build_decision_detail_view()
