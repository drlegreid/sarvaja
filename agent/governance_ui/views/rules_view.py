"""
Rules View for Governance Dashboard.

Per RULE-012: Single Responsibility - only rules list/detail/form UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-MCP-008: Semantic rule ID display support.

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

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "rules-loading"}
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

        # Rules list content (GAP-UI-036: scrollable)
        with v3.VCardText(style="max-height: 500px; overflow-y: auto;"):
            html.Div("{{ rules.length }} rules loaded", classes="mb-2 text-grey")

            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "rules-table"}
            ):
                with v3.VListItem(
                    v_for="rule in rules",
                    v_show=(
                        "!rules_search_query || "
                        "(rule.id && rule.id.toLowerCase()"
                        ".includes(rules_search_query.toLowerCase())) || "
                        "(rule.semantic_id && rule.semantic_id.toLowerCase()"
                        ".includes(rules_search_query.toLowerCase())) || "
                        "(rule.name && rule.name.toLowerCase()"
                        ".includes(rules_search_query.toLowerCase())) || "
                        "(rule.directive && rule.directive.toLowerCase()"
                        ".includes(rules_search_query.toLowerCase()))"
                    ),
                    click="selected_rule = rule; show_rule_detail = true",
                    **{":key": "rule.id"},
                    __properties=["data-testid"],
                    **{"data-testid": "rule-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon("mdi-gavel", color="primary")
                    with v3.VListItemTitle():
                        html.Span("{{ rule.id }}: {{ rule.name }}")
                        # Semantic ID (GAP-MCP-008)
                        v3.VChip(
                            v_if="rule.semantic_id",
                            v_text="rule.semantic_id",
                            size="x-small",
                            color="secondary",
                            variant="outlined",
                            classes="ml-2"
                        )
                    with v3.VListItemSubtitle():
                        # Metadata chips
                        with html.Div(classes="d-flex align-center mb-1"):
                            v3.VChip(
                                v_text="rule.category",
                                size="x-small",
                                color="primary",
                                variant="tonal",
                                classes="mr-1"
                            )
                            v3.VChip(
                                v_text="rule.status",
                                size="x-small",
                                v_bind_color=(
                                    "rule.status === 'ACTIVE' ? 'success' : "
                                    "rule.status === 'DRAFT' ? 'warning' : 'grey'"
                                ),
                                variant="tonal",
                                classes="mr-1"
                            )
                            v3.VChip(
                                v_text="rule.priority",
                                size="x-small",
                                v_bind_color=(
                                    "rule.priority === 'CRITICAL' ? 'error' : "
                                    "rule.priority === 'HIGH' ? 'warning' : "
                                    "rule.priority === 'MEDIUM' ? 'info' : 'grey'"
                                ),
                                variant="tonal",
                                classes="mr-1"
                            )
                            # Date display (GAP-UI-035)
                            html.Span(
                                v_if="rule.created_date",
                                v_text="rule.created_date",
                                classes="text-caption text-grey ml-2"
                            )
                        # Directive excerpt (GAP-UI-047)
                        html.Div(
                            v_if="rule.directive",
                            v_text=(
                                "rule.directive.length > 100 ? "
                                "rule.directive.substring(0, 100) + '...' : "
                                "rule.directive"
                            ),
                            classes="text-caption text-grey",
                            style="white-space: nowrap; overflow: hidden; "
                                  "text-overflow: ellipsis; max-width: 600px;",
                            __properties=["data-testid"],
                            **{"data-testid": "rule-directive-excerpt"}
                        )


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
            # Semantic ID display (GAP-MCP-008)
            with html.Div(
                v_if="selected_rule.semantic_id",
                classes="mb-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-semantic-id"}
            ):
                html.Div("Semantic ID", classes="text-caption text-grey")
                v3.VChip(
                    "{{ selected_rule.semantic_id }}",
                    size="small",
                    color="secondary",
                    variant="outlined",
                    prepend_icon="mdi-tag-outline"
                )

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

            # Directive preview (GAP-UI-037)
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "rule-directive-preview"}
            ):
                v3.VCardTitle("Directive", density="compact")
                with v3.VCardText():
                    html.Pre(
                        "{{ selected_rule.directive || 'No directive specified' }}",
                        style="white-space: pre-wrap; font-family: inherit; "
                              "font-size: 0.875rem; background: #f5f5f5; "
                              "padding: 12px; border-radius: 4px; margin: 0;",
                        __properties=["data-testid"],
                        **{"data-testid": "rule-directive-text"}
                    )

            # Rule dependencies (GAP-UI-037)
            with v3.VCard(
                v_if="selected_rule.dependencies?.length > 0",
                variant="outlined",
                classes="mt-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-dependencies"}
            ):
                v3.VCardTitle("Dependencies", density="compact")
                with v3.VCardText():
                    v3.VChip(
                        v_for="dep in selected_rule.dependencies",
                        v_text="dep",
                        size="small",
                        color="secondary",
                        classes="mr-1",
                        prepend_icon="mdi-link"
                    )

            # Implementing tasks (UI-AUDIT-003)
            with v3.VCard(
                variant="outlined",
                classes="mt-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-implementing-tasks"}
            ):
                with v3.VCardTitle(classes="d-flex align-center", density="compact"):
                    html.Span("Implementing Tasks")
                    v3.VSpacer()
                    v3.VProgressCircular(
                        v_if="rule_implementing_tasks_loading",
                        indeterminate=True,
                        size=20,
                        width=2
                    )
                    v3.VChip(
                        v_if="!rule_implementing_tasks_loading",
                        v_text="rule_implementing_tasks.length",
                        size="x-small",
                        color="primary",
                        classes="ml-2"
                    )
                with v3.VCardText():
                    # No tasks message
                    html.Div(
                        v_if="!rule_implementing_tasks_loading && rule_implementing_tasks.length === 0",
                        classes="text-grey",
                        __properties=["data-testid"],
                        **{"data-testid": "rule-no-tasks"}
                    ):
                        html.Content("No tasks implementing this rule")

                    # Task list
                    with v3.VList(
                        v_if="rule_implementing_tasks.length > 0",
                        density="compact"
                    ):
                        with v3.VListItem(
                            v_for="task in rule_implementing_tasks",
                            **{":key": "task.task_id"},
                            __properties=["data-testid"],
                            **{"data-testid": "implementing-task-item"}
                        ):
                            with html.Template(v_slot_prepend=True):
                                v3.VIcon("mdi-checkbox-marked-circle-outline", color="success", size="small")
                            with v3.VListItemTitle():
                                html.Span("{{ task.task_id }}: {{ task.name }}")
                            with v3.VListItemSubtitle():
                                v3.VChip(
                                    v_text="task.status",
                                    size="x-small",
                                    v_bind_color=(
                                        "task.status === 'DONE' ? 'success' : "
                                        "task.status === 'IN_PROGRESS' ? 'warning' : 'grey'"
                                    ),
                                    variant="tonal",
                                    classes="mr-1"
                                )
                                v3.VChip(
                                    v_text="task.priority",
                                    size="x-small",
                                    v_bind_color=(
                                        "task.priority === 'CRITICAL' ? 'error' : "
                                        "task.priority === 'HIGH' ? 'warning' : 'grey'"
                                    ),
                                    variant="tonal"
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
