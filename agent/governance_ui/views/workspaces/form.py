"""
Workspace Create Form View Component.

Per RULE-012: Single Responsibility - only workspace form UI.
Per RULE-032: File size limit (<300 lines).
Inline form for creating new workspaces.
"""

from trame.widgets import vuetify3 as v3, html


def build_workspace_form_view() -> None:
    """Build inline create workspace form."""
    with v3.VCard(
        v_if="active_view === 'workspaces' && show_workspace_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "workspace-form"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="trigger('cancel_workspace_form')",
                __properties=["data-testid"],
                **{"data-testid": "workspace-form-cancel-btn"}
            )
            v3.VIcon("mdi-plus", classes="mr-2")
            html.Span("Create Workspace")

        with v3.VCardText():
            # Error alert
            v3.VAlert(
                v_if="has_error",
                type_="error",
                variant="tonal",
                classes="mb-4",
                v_text="error_message",
                closable=True,
                **{"@click:close": "has_error = false"},
            )

            with v3.VForm(
                __properties=["data-testid"],
                **{"data-testid": "workspace-create-form"}
            ):
                v3.VTextField(
                    v_model="form_workspace_name",
                    label="Workspace Name *",
                    placeholder="e.g. My Dev Workspace",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-form-name"},
                )
                v3.VSelect(
                    v_model="form_workspace_type",
                    label="Workspace Type",
                    items=("workspace_type_options", ['generic']),
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-form-type"},
                )
                v3.VTextarea(
                    v_model="form_workspace_description",
                    label="Description",
                    placeholder="Optional description",
                    density="compact",
                    rows=3,
                    auto_grow=True,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-form-description"},
                )
                v3.VTextField(
                    v_model="form_workspace_project_id",
                    label="Project ID",
                    placeholder="Optional project to link",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-form-project"},
                )

        with v3.VCardActions():
            v3.VSpacer()
            v3.VBtn(
                "Cancel",
                variant="text",
                click="trigger('cancel_workspace_form')",
            )
            v3.VBtn(
                "Create",
                color="primary",
                click="trigger('create_workspace')",
                loading=("is_loading",),
                disabled=("!form_workspace_name",),
                __properties=["data-testid"],
                **{"data-testid": "workspace-form-submit-btn"},
            )
