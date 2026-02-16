"""
Session Form Component.

Per RULE-012: Single Responsibility - only session form UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-034: Session CRUD operations.
"""

from trame.widgets import vuetify3 as v3, html


def build_session_form_view() -> None:
    """
    Build the Session create/edit form view.

    Per GAP-UI-034: Session CRUD operations.
    """
    with v3.VCard(
        v_if="active_view === 'sessions' && show_session_form",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "session-form"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="trigger('close_session_form')",
                __properties=["data-testid"],
                **{"data-testid": "session-form-back-btn"}
            )
            html.Span(
                "{{ session_form_mode === 'create' ? 'Create Session' : 'Edit Session' }}"
            )

        with v3.VCardText():
            with v3.VForm():
                v3.VTextField(
                    v_model="form_session_id",
                    label="Session ID",
                    placeholder="SESSION-YYYY-MM-DD-XXX (auto-generated if empty)",
                    hint="Leave empty to auto-generate",
                    persistent_hint=True,
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    disabled=("session_form_mode === 'edit'",),
                    __properties=["data-testid"],
                    **{"data-testid": "session-form-id"}
                )
                v3.VTextarea(
                    v_model="form_session_description",
                    label="Description",
                    hint="What is this session about?",
                    variant="outlined",
                    rows=3,
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "session-form-description"}
                )
                v3.VTextField(
                    v_model="form_session_agent_id",
                    label="Agent ID (optional)",
                    placeholder="e.g., claude-code",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "session-form-agent"}
                )
                v3.VSelect(
                    v_model="form_session_status",
                    items=("['ACTIVE', 'COMPLETED']",),
                    label="Status",
                    variant="outlined",
                    density="compact",
                    classes="mb-3",
                    __properties=["data-testid"],
                    **{"data-testid": "session-form-status"}
                )

        with v3.VCardActions():
            v3.VSpacer()
            v3.VBtn(
                "Cancel",
                variant="text",
                click="trigger('close_session_form')",
                __properties=["data-testid"],
                **{"data-testid": "session-form-cancel-btn"}
            )
            v3.VBtn(
                "Save",
                color="primary",
                click="trigger('submit_session_form')",
                __properties=["data-testid"],
                **{"data-testid": "session-form-save-btn"}
            )
