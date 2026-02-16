"""
Rules View for Governance Dashboard.

Per RULE-012: Single Responsibility - only rules list/detail/form UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-MCP-008: Semantic rule ID display support.
Per UI-NAV-01-v1: Entity Navigation - task click with back source.
Per DOC-SIZE-01-v1: Detail view in rules_view_detail.py.

This module builds the Rules view components using Trame/Vuetify 3.
"""

from trame.widgets import vuetify3 as v3, html

from .rules_view_detail import build_rule_detail_view  # noqa: F401 — re-export


def build_rules_view() -> None:
    """Build the complete Rules view including list, detail, and form."""
    build_rules_list_view()
    build_rule_detail_view()
    build_rule_form_view()


def build_rules_list_view() -> None:
    """Build the rules list view card."""
    with v3.VCard(
        v_if="active_view === 'rules' && !show_rule_detail && !show_rule_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "rules-list"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Governance Rules")
            v3.VSpacer()
            v3.VBtn(
                "Add Rule",
                color="primary",
                prepend_icon="mdi-plus",
                click="trigger('open_rule_form', ['create'])",
                __properties=["data-testid"],
                **{"data-testid": "rules-add-btn"},
            )

        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "rules-loading"},
        )

        with v3.VToolbar(density="compact", flat=True):
            v3.VTextField(
                v_model="rules_search_query",
                label="Search rules...",
                prepend_icon="mdi-magnify",
                variant="outlined",
                density="compact",
                hide_details=True,
                style="max-width: 300px",
                __properties=["data-testid"],
                **{"data-testid": "rules-search"},
            )
            v3.VSpacer()
            v3.VSelect(
                v_model="rules_status_filter",
                items=("status_options",),
                label="Status",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 150px",
                __properties=["data-testid"],
                **{"data-testid": "rules-filter-status"},
            )
            v3.VSelect(
                v_model="rules_category_filter",
                items=("category_options",),
                label="Category",
                variant="outlined",
                density="compact",
                hide_details=True,
                clearable=True,
                style="max-width: 150px; margin-left: 8px",
                __properties=["data-testid"],
                **{"data-testid": "rules-filter-category"},
            )

        with v3.VCardText():
            v3.VDataTable(
                items=("rules",),
                headers=("rules_headers", [
                    {"title": "Rule ID", "key": "id", "width": "180px", "sortable": True},
                    {"title": "Name", "key": "name", "sortable": True},
                    {"title": "Status", "key": "status", "width": "100px", "sortable": True},
                    {"title": "Category", "key": "category", "width": "120px", "sortable": True},
                    {"title": "Priority", "key": "priority", "width": "100px", "sortable": True},
                    {"title": "Applicability", "key": "applicability", "width": "120px", "sortable": True},
                    {"title": "Tasks", "key": "linked_tasks_count", "width": "80px", "sortable": True},
                    {"title": "Sessions", "key": "linked_sessions_count", "width": "90px", "sortable": True},
                    {"title": "Created", "key": "created_date", "width": "120px", "sortable": True},
                ]),
                item_value="id",
                search=("rules_search_query",),
                density="compact",
                items_per_page=25,
                hover=True,
                click_row="($event, row) => { trigger('select_rule', [row.item.id]) }",
                __events=[("click_row", "click:row")],
                __properties=["data-testid"],
                **{"data-testid": "rules-table"},
            )


def build_rule_form_view() -> None:
    """Build the rule create/edit form view."""
    with v3.VCard(
        v_if="active_view === 'rules' && show_rule_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "rule-form"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="trigger('close_rule_form')",
                __properties=["data-testid"],
                **{"data-testid": "rule-form-back-btn"},
            )
            html.Span("{{ rule_form_mode === 'create' ? 'Create Rule' : 'Edit Rule' }}")

        with v3.VCardText():
            with v3.VForm():
                v3.VTextField(
                    v_model="form_rule_id",
                    label="Rule ID",
                    placeholder="RULE-XXX",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-id"},
                )
                v3.VTextField(
                    v_model="form_rule_title",
                    label="Name",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-name"},
                )
                v3.VTextarea(
                    v_model="form_rule_directive",
                    label="Directive",
                    variant="outlined",
                    rows=4,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-directive"},
                )
                v3.VSelect(
                    v_model="form_rule_category",
                    items=("category_options",),
                    label="Category",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-category"},
                )
                v3.VSelect(
                    v_model="form_rule_priority",
                    items=("['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']",),
                    label="Priority",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-priority"},
                )
                v3.VSelect(
                    v_model="form_rule_applicability",
                    items=("['MANDATORY', 'RECOMMENDED', 'CONDITIONAL', 'FORBIDDEN']",),
                    label="Applicability",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-applicability"},
                )

        with v3.VCardActions():
            v3.VSpacer()
            v3.VBtn(
                "Cancel",
                variant="text",
                click="trigger('close_rule_form')",
                __properties=["data-testid"],
                **{"data-testid": "rule-form-cancel-btn"},
            )
            v3.VBtn(
                "Save",
                color="primary",
                click="trigger('submit_rule_form')",
                __properties=["data-testid"],
                **{"data-testid": "rule-form-save-btn"},
            )
