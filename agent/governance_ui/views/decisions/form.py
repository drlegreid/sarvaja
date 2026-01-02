"""
Decision Form Component.

Per RULE-012: Single Responsibility - only decision form UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-033: Decision CRUD operations.
"""

from trame.widgets import vuetify3 as v3, html


def build_decision_form_view() -> None:
    """
    Build the Decision create/edit form view.

    Per GAP-UI-033: Decision CRUD operations.
    """
    with v3.VCard(
        v_if="active_view === 'decisions' && show_decision_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "decision-form"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_decision_form = false",
                __properties=["data-testid"],
                **{"data-testid": "decision-form-back-btn"}
            )
            html.Span(
                "{{ decision_form_mode === 'create' ? 'Create Decision' : 'Edit Decision' }}"
            )

        with v3.VCardText():
            with v3.VForm():
                v3.VTextField(
                    v_model="form_decision_id",
                    label="Decision ID",
                    placeholder="DECISION-XXX",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    disabled=("decision_form_mode === 'edit'",),
                    __properties=["data-testid"],
                    **{"data-testid": "decision-form-id"}
                )
                v3.VTextField(
                    v_model="form_decision_name",
                    label="Name/Title",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "decision-form-name"}
                )
                v3.VTextarea(
                    v_model="form_decision_context",
                    label="Context",
                    hint="Problem statement or context for this decision",
                    variant="outlined",
                    rows=3,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "decision-form-context"}
                )
                v3.VTextarea(
                    v_model="form_decision_rationale",
                    label="Rationale",
                    hint="Reasoning and justification for the decision",
                    variant="outlined",
                    rows=4,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "decision-form-rationale"}
                )
                v3.VSelect(
                    v_model="form_decision_status",
                    items=("['PENDING', 'APPROVED', 'REJECTED', 'IMPLEMENTED']",),
                    label="Status",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "decision-form-status"}
                )

        with v3.VCardActions():
            v3.VSpacer()
            v3.VBtn(
                "Cancel",
                variant="text",
                click="show_decision_form = false",
                __properties=["data-testid"],
                **{"data-testid": "decision-form-cancel-btn"}
            )
            v3.VBtn(
                "Save",
                color="primary",
                click="submit_decision_form",
                __properties=["data-testid"],
                **{"data-testid": "decision-form-save-btn"}
            )
