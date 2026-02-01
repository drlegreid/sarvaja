"""
Audit Trail Dashboard View.

Per RD-DEBUG-AUDIT Phase 4: Dashboard view for audit history.
Per RULE-012: Single Responsibility - only audit trail UI.

Shows:
- Audit entry statistics (by action, entity, actor)
- Filterable audit trail table
- Entity-specific audit drill-down
- Correlation ID tracking
"""

from trame.widgets import vuetify3 as v3, html


def build_audit_header() -> None:
    """Build audit dashboard header."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-history", classes="mr-2")
        html.Span("Audit Trail")
        v3.VSpacer()
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            click="trigger('load_audit_trail')",
            loading=("audit_loading",),
            __properties=["data-testid"],
            **{"data-testid": "audit-refresh-btn"}
        )


def build_audit_summary() -> None:
    """Build audit summary cards."""
    with v3.VRow():
        # Total Entries Card
        with v3.VCol(cols=12, md=3):
            with v3.VCard(
                variant="tonal",
                color="primary",
                __properties=["data-testid"],
                **{"data-testid": "audit-total-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(icon="mdi-counter", size="48", color="primary")
                    html.Div(
                        "{{ audit_summary.total_entries || 0 }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div("Total Entries", classes="text-caption text-grey")

        # Entity Types Card
        with v3.VCol(cols=12, md=3):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "audit-entities-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(icon="mdi-database", size="48", color="info")
                    html.Div(
                        "{{ Object.keys(audit_summary.by_entity_type || {}).length }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div("Entity Types", classes="text-caption text-grey")

        # Actions Card
        with v3.VCol(cols=12, md=3):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "audit-actions-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(icon="mdi-flash", size="48", color="warning")
                    html.Div(
                        "{{ Object.keys(audit_summary.by_action_type || {}).length }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div("Action Types", classes="text-caption text-grey")

        # Actors Card
        with v3.VCol(cols=12, md=3):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "audit-actors-card"}
            ):
                with v3.VCardText(classes="text-center"):
                    v3.VIcon(icon="mdi-account-group", size="48", color="success")
                    html.Div(
                        "{{ Object.keys(audit_summary.by_actor || {}).length }}",
                        classes="text-h4 font-weight-bold mt-2"
                    )
                    html.Div("Actors", classes="text-caption text-grey")


def build_audit_filters() -> None:
    """Build audit filters section."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12, md=3):
            v3.VSelect(
                v_model=("audit_filter_entity_type",),
                items=("audit_entity_types",),
                label="Entity Type",
                clearable=True,
                density="compact",
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "audit-filter-entity-type"}
            )

        with v3.VCol(cols=12, md=3):
            v3.VSelect(
                v_model=("audit_filter_action_type",),
                items=("audit_action_types",),
                label="Action Type",
                clearable=True,
                density="compact",
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "audit-filter-action-type"}
            )

        with v3.VCol(cols=12, md=3):
            v3.VTextField(
                v_model=("audit_filter_entity_id",),
                label="Entity ID",
                clearable=True,
                density="compact",
                variant="outlined",
                prepend_inner_icon="mdi-magnify",
                __properties=["data-testid"],
                **{"data-testid": "audit-filter-entity-id"}
            )

        with v3.VCol(cols=12, md=3):
            v3.VTextField(
                v_model=("audit_filter_correlation_id",),
                label="Correlation ID",
                clearable=True,
                density="compact",
                variant="outlined",
                prepend_inner_icon="mdi-link",
                __properties=["data-testid"],
                **{"data-testid": "audit-filter-correlation-id"}
            )


def build_audit_table() -> None:
    """Build audit trail table."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "audit-table-card"}
            ):
                v3.VCardTitle("Audit Entries")
                with v3.VCardText():
                    v3.VDataTable(
                        items=("audit_entries",),
                        headers=("audit_headers", [
                            {"title": "Timestamp", "key": "timestamp", "width": "160px"},
                            {"title": "Action", "key": "action_type", "width": "100px"},
                            {"title": "Entity", "key": "entity_type", "width": "80px"},
                            {"title": "Entity ID", "key": "entity_id", "width": "150px"},
                            {"title": "Actor", "key": "actor_id", "width": "120px"},
                            {"title": "Rules Applied", "key": "applied_rules"},
                            {"title": "Correlation", "key": "correlation_id", "width": "200px"},
                        ]),
                        density="compact",
                        items_per_page=20,
                        hover=True,
                        click_row="($event, row) => { trigger('navigate_to_entity', [row.item.entity_type, row.item.entity_id]) }",
                        __events=[("click_row", "click:row")],
                        __properties=["data-testid"],
                        **{"data-testid": "audit-entries-table"}
                    )


def build_action_breakdown() -> None:
    """Build action type breakdown panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12, md=6):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "audit-action-breakdown-card"}
            ):
                with v3.VCardTitle():
                    v3.VIcon("mdi-chart-bar", classes="mr-2")
                    html.Span("Actions by Type")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        with v3.VListItem(
                            v_for="(count, action) in audit_summary.by_action_type",
                            key="action"
                        ):
                            with v3.VListItemTitle(classes="d-flex justify-space-between"):
                                html.Span("{{ action }}")
                                v3.VChip(
                                    size="small",
                                    color="primary",
                                    label=True
                                ).add_child("{{ count }}")

        with v3.VCol(cols=12, md=6):
            with v3.VCard(
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "audit-entity-breakdown-card"}
            ):
                with v3.VCardTitle():
                    v3.VIcon("mdi-database-outline", classes="mr-2")
                    html.Span("Actions by Entity Type")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        with v3.VListItem(
                            v_for="(count, entity) in audit_summary.by_entity_type",
                            key="entity"
                        ):
                            with v3.VListItemTitle(classes="d-flex justify-space-between"):
                                html.Span("{{ entity }}")
                                v3.VChip(
                                    size="small",
                                    color="info",
                                    label=True
                                ).add_child("{{ count }}")


def build_audit_view() -> None:
    """
    Build the Audit Trail Dashboard view.

    Main entry point for the audit view module.
    Per RD-DEBUG-AUDIT Phase 4: Dashboard view for audit history.
    """
    with v3.VCard(
        v_if="active_view === 'audit'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "audit-dashboard"}
    ):
        build_audit_header()

        with v3.VCardText():
            # Summary cards
            build_audit_summary()

            # Filters
            build_audit_filters()

            # Audit table
            build_audit_table()

            # Action breakdown
            build_action_breakdown()
