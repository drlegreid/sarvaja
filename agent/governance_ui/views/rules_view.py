"""
Rules View for Governance Dashboard.

Per RULE-012: Single Responsibility - only rules list/detail/form UI.
Per RULE-019: UI/UX Standards - consistent view patterns.

This module builds the Rules view components using Trame/Vuetify 3.
"""

from trame.widgets import vuetify3 as v3, html


def build_rules_view() -> None:
    """
    Build the complete Rules view including list, detail, and form.

    Must be called within a v3.VContainer context.
    State is accessed through Trame bindings, not passed as argument.
    """
    build_rules_list_view()
    build_rule_detail_view()
    build_rule_form_view()


def build_rules_list_view() -> None:
    """Build the rules list view card."""
    with v3.VCard(
        v_if="active_view === 'rules' && !show_rule_detail && !show_rule_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "rules-list"}
    ):
        # Header with title and add button
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Governance Rules")
            v3.VSpacer()
            v3.VBtn(
                "Add Rule",
                color="primary",
                prepend_icon="mdi-plus",
                click="rule_form_mode = 'create'; show_rule_form = true",
                __properties=["data-testid"],
                **{"data-testid": "rules-add-btn"}
            )

        # Filters toolbar
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
                **{"data-testid": "rules-search"}
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
                **{"data-testid": "rules-filter-status"}
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
                **{"data-testid": "rules-filter-category"}
            )

        # Rules list content
        with v3.VCardText():
            html.Div("{{ rules.length }} rules loaded", classes="mb-2 text-grey")

            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "rules-table"}
            ):
                with v3.VListItem(
                    v_for="rule in rules",
                    v_show="!rules_search_query || (rule.id && rule.id.toLowerCase().includes(rules_search_query.toLowerCase())) || (rule.name && rule.name.toLowerCase().includes(rules_search_query.toLowerCase()))",
                    click="selected_rule = rule; show_rule_detail = true",
                    **{":key": "rule.id"},
                    __properties=["data-testid"],
                    **{"data-testid": "rule-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon("mdi-gavel", color="primary")
                    with v3.VListItemTitle():
                        html.Span("{{ rule.id }}: {{ rule.name }}")
                    with v3.VListItemSubtitle():
                        html.Span("{{ rule.category }} | {{ rule.status }} | {{ rule.priority }}")


def build_rule_detail_view() -> None:
    """Build the rule detail view card."""
    with v3.VCard(
        v_if="active_view === 'rules' && show_rule_detail && selected_rule",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "rule-detail"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_rule_detail = false; selected_rule = null",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-back-btn"}
            )
            html.Span(
                "{{ selected_rule.rule_id || selected_rule.id }}",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-id"}
            )
            v3.VSpacer()
            v3.VBtn(
                "Edit",
                color="primary",
                prepend_icon="mdi-pencil",
                click="rule_form_mode = 'edit'; show_rule_form = true",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-edit-btn"}
            )
            v3.VBtn(
                "Delete",
                color="error",
                prepend_icon="mdi-delete",
                click="delete_rule",
                classes="ml-2",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-delete-btn"}
            )

        with v3.VCardText():
            # Rule info fields
            with v3.VRow():
                with v3.VCol(cols="6"):
                    html.Div("Name", classes="text-caption text-grey")
                    html.Div("{{ selected_rule.name }}", classes="text-body-1")
                with v3.VCol(cols="3"):
                    html.Div("Category", classes="text-caption text-grey")
                    v3.VChip(
                        "{{ selected_rule.category }}",
                        size="small",
                        color="primary"
                    )
                with v3.VCol(cols="3"):
                    html.Div("Priority", classes="text-caption text-grey")
                    v3.VChip(
                        "{{ selected_rule.priority }}",
                        size="small",
                        v_bind_color="selected_rule.priority === 'CRITICAL' ? 'error' : selected_rule.priority === 'HIGH' ? 'warning' : 'info'"
                    )

            v3.VDivider(classes="my-4")

            html.Div("Directive", classes="text-caption text-grey mb-2")
            html.Div(
                "{{ selected_rule.directive || 'No directive specified' }}",
                classes="text-body-1",
                style="white-space: pre-wrap"
            )


def build_rule_form_view() -> None:
    """Build the rule create/edit form view."""
    with v3.VCard(
        v_if="active_view === 'rules' && show_rule_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "rule-form"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_rule_form = false",
                __properties=["data-testid"],
                **{"data-testid": "rule-form-back-btn"}
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
                    **{"data-testid": "rule-form-id"}
                )
                v3.VTextField(
                    v_model="form_rule_title",
                    label="Name",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-name"}
                )
                v3.VTextarea(
                    v_model="form_rule_directive",
                    label="Directive",
                    variant="outlined",
                    rows=4,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-directive"}
                )
                v3.VSelect(
                    v_model="form_rule_category",
                    items=("category_options",),
                    label="Category",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-category"}
                )
                v3.VSelect(
                    v_model="form_rule_priority",
                    items=("['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']",),
                    label="Priority",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "rule-form-priority"}
                )

        with v3.VCardActions():
            v3.VSpacer()
            v3.VBtn(
                "Cancel",
                variant="text",
                click="show_rule_form = false",
                __properties=["data-testid"],
                **{"data-testid": "rule-form-cancel-btn"}
            )
            v3.VBtn(
                "Save",
                color="primary",
                click="submit_rule_form",
                __properties=["data-testid"],
                **{"data-testid": "rule-form-save-btn"}
            )
