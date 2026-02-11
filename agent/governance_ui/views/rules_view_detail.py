"""
Rule Detail View.

Per DOC-SIZE-01-v1: Extracted from rules_view.py (426 lines).
Rule detail card with metadata, directive, dependencies, and linked tasks.
"""

from trame.widgets import vuetify3 as v3, html


def build_rule_detail_view() -> None:
    """Build the rule detail view card."""
    with v3.VCard(
        v_if="active_view === 'rules' && show_rule_detail && selected_rule",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "rule-detail"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_rule_detail = false; selected_rule = null",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-back-btn"},
            )
            html.Span(
                "{{ selected_rule.rule_id || selected_rule.id }}",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-id"},
            )
            v3.VSpacer()
            v3.VBtn(
                "Edit",
                color="primary",
                prepend_icon="mdi-pencil",
                click="trigger('edit_rule')",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-edit-btn"},
            )
            v3.VBtn(
                "Delete",
                color="error",
                prepend_icon="mdi-delete",
                click="delete_rule",
                classes="ml-2",
                __properties=["data-testid"],
                **{"data-testid": "rule-detail-delete-btn"},
            )

        with v3.VCardText():
            # Semantic ID display (GAP-MCP-008)
            with html.Div(
                v_if="selected_rule.semantic_id",
                classes="mb-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-semantic-id"},
            ):
                html.Div("Semantic ID", classes="text-caption text-grey")
                v3.VChip(
                    "{{ selected_rule.semantic_id }}",
                    size="small",
                    color="secondary",
                    variant="outlined",
                    prepend_icon="mdi-tag-outline",
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
                        color="primary",
                    )
                with v3.VCol(cols="3"):
                    html.Div("Priority", classes="text-caption text-grey")
                    v3.VChip(
                        "{{ selected_rule.priority }}",
                        size="small",
                        v_bind_color="selected_rule.priority === 'CRITICAL' ? 'error' : selected_rule.priority === 'HIGH' ? 'warning' : 'info'",
                    )

            v3.VDivider(classes="my-4")

            # Directive preview (GAP-UI-037)
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "rule-directive-preview"},
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
                        **{"data-testid": "rule-directive-text"},
                    )

            # Document link (GAP-UI-AUDIT-001)
            with v3.VCard(
                v_if="selected_rule.document_path",
                variant="outlined",
                classes="mt-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-document-link"},
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
                        **{"data-testid": "rule-document-btn"},
                    )
                    html.Div(
                        "Click to view the full rule specification document",
                        classes="text-caption text-grey mt-2",
                    )

            # Rule dependencies (GAP-UI-037)
            with v3.VCard(
                v_if="selected_rule.dependencies?.length > 0",
                variant="outlined",
                classes="mt-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-dependencies"},
            ):
                v3.VCardTitle("Dependencies", density="compact")
                with v3.VCardText():
                    v3.VChip(
                        v_for="dep in selected_rule.dependencies",
                        v_text="dep",
                        size="small",
                        color="secondary",
                        classes="mr-1",
                        prepend_icon="mdi-link",
                    )

            # Implementing tasks (UI-AUDIT-003)
            with v3.VCard(
                variant="outlined",
                classes="mt-4",
                __properties=["data-testid"],
                **{"data-testid": "rule-implementing-tasks"},
            ):
                with v3.VCardTitle(classes="d-flex align-center", density="compact"):
                    html.Span("Implementing Tasks")
                    v3.VSpacer()
                    v3.VProgressCircular(
                        v_if="rule_implementing_tasks_loading",
                        indeterminate=True,
                        size=20,
                        width=2,
                    )
                    v3.VChip(
                        v_if="!rule_implementing_tasks_loading",
                        v_text="rule_implementing_tasks.length",
                        size="x-small",
                        color="primary",
                        classes="ml-2",
                    )
                with v3.VCardText():
                    html.Div(
                        "No tasks implementing this rule",
                        v_if="!rule_implementing_tasks_loading && rule_implementing_tasks.length === 0",
                        classes="text-grey",
                        __properties=["data-testid"],
                        **{"data-testid": "rule-no-tasks"},
                    )

                    # Task list (UI-NAV-01-v1: click navigates with source)
                    with v3.VList(
                        v_if="rule_implementing_tasks.length > 0",
                        density="compact",
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
                            **{"data-testid": "implementing-task-item"},
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
                                    classes="mr-1",
                                )
                                v3.VChip(
                                    v_text="task.priority",
                                    size="x-small",
                                    v_bind_color=(
                                        "task.priority === 'CRITICAL' ? 'error' : "
                                        "task.priority === 'HIGH' ? 'warning' : 'grey'"
                                    ),
                                    variant="tonal",
                                )
