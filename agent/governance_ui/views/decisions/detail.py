"""
Decision Detail View Component.

Per RULE-012: Single Responsibility - only decision detail UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-033: Decision CRUD operations.
"""

from trame.widgets import vuetify3 as v3, html

from .content import build_decision_metadata_chips, build_decision_info_cards


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
            v3.VSpacer()
            # Edit/Delete buttons (GAP-UI-033)
            v3.VBtn(
                "Edit",
                color="primary",
                prepend_icon="mdi-pencil",
                click="decision_form_mode = 'edit'; show_decision_form = true",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-edit-btn"}
            )
            v3.VBtn(
                "Delete",
                color="error",
                prepend_icon="mdi-delete",
                click="delete_decision",
                classes="ml-2",
                __properties=["data-testid"],
                **{"data-testid": "decision-detail-delete-btn"}
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
