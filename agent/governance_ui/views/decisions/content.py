"""
Decision Content Components.

Per RULE-012: Single Responsibility - decision content display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-037: Context and rationale preview.
"""

from trame.widgets import vuetify3 as v3, html


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
        # Left column: Decision information - Per UI-RESP-01-v1
        with v3.VCol(cols=12, md=6):
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
        # Right column: Impact - Per UI-RESP-01-v1
        with v3.VCol(cols=12, md=6):
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
