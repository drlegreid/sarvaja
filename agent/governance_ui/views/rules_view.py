"""
Rules View for Governance Dashboard.

Per RULE-012: Single Responsibility - only rules list/detail/form UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-MCP-008: Semantic rule ID display support.
Per UI-NAV-01-v1: Entity Navigation - task click with back source.

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

        # Rules data table (PLAN-UI-OVERHAUL-001 Task 1.1: Grid with columns)
        with v3.VCardText():
            v3.VDataTable(
                items=("rules",),
                headers=("rules_headers", [
                    {"title": "Rule ID", "key": "id", "width": "180px", "sortable": True},
                    {"title": "Name", "key": "name", "sortable": True},
                    {"title": "Status", "key": "status", "width": "100px", "sortable": True},
                    {"title": "Category", "key": "category", "width": "120px", "sortable": True},
                    {"title": "Priority", "key": "priority", "width": "100px", "sortable": True},
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
                **{"data-testid": "rules-table"}
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
                click="trigger('edit_rule')",
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
                              "font-size: 0.875rem; "
                              "padding: 12px; border-radius: 4px; margin: 0;",
                        classes="bg-surface-variant",
                        __properties=["data-testid"],
                        **{"data-testid": "rule-directive-text"}
                    )

            # Document link (GAP-UI-AUDIT-001: rule-document linkage)
            with v3.VCard(
                v_if="selected_rule.document_path",
                variant="outlined",
                classes="mt-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-document-link"}
            ):
                with v3.VCardTitle(classes="d-flex align-center", density="compact"):
                    v3.VIcon("mdi-file-document-outline", size="small", classes="mr-2")
                    html.Span("Source Document")
                with v3.VCardText():
                    v3.VBtn(
                        v_text="selected_rule.document_path",
                        variant="tonal",
                        color="secondary",
                        prepend_icon="mdi-open-in-new",
                        click="trigger('load_file_content', [selected_rule.document_path])",
                        __properties=["data-testid"],
                        **{"data-testid": "rule-document-btn"}
                    )
                    html.Div(
                        "Click to view the full rule specification document",
                        classes="text-caption text-grey mt-2"
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
                        "No tasks implementing this rule",
                        v_if="!rule_implementing_tasks_loading && rule_implementing_tasks.length === 0",
                        classes="text-grey",
                        __properties=["data-testid"],
                        **{"data-testid": "rule-no-tasks"}
                    )

                    # Task list (UI-NAV-01-v1: click navigates with source)
                    with v3.VList(
                        v_if="rule_implementing_tasks.length > 0",
                        density="compact"
                    ):
                        with v3.VListItem(
                            v_for="task in rule_implementing_tasks",
                            **{":key": "task.task_id"},
                            click=(
                                "trigger('navigate_to_task', ["
                                "task.task_id, "
                                "'rules', "
                                "selected_rule.rule_id || selected_rule.id, "
                                "'Rule: ' + (selected_rule.rule_id || selected_rule.id)"
                                "])"
                            ),
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
