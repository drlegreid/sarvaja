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


def build_decision_content_preview() -> None:
    """Build decision context and rationale preview (GAP-UI-037)."""
    # Context preview
    with v3.VCard(
        v_if="selected_decision.context",
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "decision-context-preview"}
    ):
        v3.VCardTitle("Context", density="compact")
        with v3.VCardText():
            html.Pre(
                "{{ selected_decision.context }}",
                style="white-space: pre-wrap; font-family: inherit; "
                      "font-size: 0.875rem; background: #f5f5f5; "
                      "padding: 12px; border-radius: 4px; margin: 0;",
                __properties=["data-testid"],
                **{"data-testid": "decision-context-text"}
            )

    # Rationale preview
    with v3.VCard(
        v_if="selected_decision.rationale",
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "decision-rationale-preview"}
    ):
        v3.VCardTitle("Rationale", density="compact")
        with v3.VCardText():
            html.Pre(
                "{{ selected_decision.rationale }}",
                style="white-space: pre-wrap; font-family: inherit; "
                      "font-size: 0.875rem; background: #e3f2fd; "
                      "padding: 12px; border-radius: 4px; margin: 0;",
                __properties=["data-testid"],
                **{"data-testid": "decision-rationale-text"}
            )


def build_decision_info_cards() -> None:
    """Build decision information and impact cards."""
    # Content previews first (GAP-UI-037)
    build_decision_content_preview()

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

    # Affected rules chips (GAP-UI-037)
    with v3.VCard(
        v_if="selected_decision.affected_rules?.length > 0",
        variant="outlined",
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "decision-affected-rules"}
    ):
        v3.VCardTitle("Affected Rules", density="compact")
        with v3.VCardText():
            v3.VChip(
                v_for="rule in selected_decision.affected_rules",
                v_text="rule",
                size="small",
                color="primary",
                classes="mr-1",
                prepend_icon="mdi-gavel"
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


def build_decisions_view() -> None:
    """
    Build the complete Decisions view including list, detail, and form.

    This is the main entry point for the decisions view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    Per GAP-UI-033: Decision CRUD operations.
    """
    build_decisions_list_view()
    build_decision_detail_view()
    build_decision_form_view()
