"""
Agent Registration Form Component.

Per RULE-012: Single Responsibility - only agent registration UI.
Per RULE-032: File size limit (<300 lines).
Per PLAN-UI-OVERHAUL-001 Task 3.3: Agent Configuration & New Types.
Per ASSESS-PLATFORM-GAPS-2026-02-15: Workspace-aware agent templates.
"""

from trame.widgets import vuetify3 as v3, html

from governance.services.workspace_registry import (
    get_workspace_type,
    list_workspace_types,
)


def _get_agent_templates_for_current_workspace(workspace_type_id: str = "governance"):
    """Get agent templates for the given workspace type."""
    wt = get_workspace_type(workspace_type_id)
    if wt and wt.agent_templates:
        return wt.agent_templates
    # Fallback to governance defaults
    wt = get_workspace_type("governance")
    return wt.agent_templates if wt else []


# Default templates (governance workspace) — used at module load
AGENT_TYPE_TEMPLATES = _get_agent_templates_for_current_workspace("governance")


def build_agent_registration_form() -> None:
    """Build agent registration dialog form."""
    with v3.VDialog(
        v_model=("show_agent_registration",),
        max_width="600px",
        __properties=["data-testid"],
        **{"data-testid": "agent-registration-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Register New Agent")
            with v3.VCardText():
                with v3.VForm():
                    # Agent name
                    v3.VTextField(
                        v_model=("reg_agent_name",),
                        label="Agent Name",
                        placeholder="e.g., Research Assistant",
                        variant="outlined",
                        density="compact",
                        classes="mb-3",
                        __properties=["data-testid"],
                        **{"data-testid": "reg-agent-name"}
                    )
                    # Agent ID
                    v3.VTextField(
                        v_model=("reg_agent_id",),
                        label="Agent ID",
                        placeholder="e.g., agent-research-01",
                        variant="outlined",
                        density="compact",
                        classes="mb-3",
                        __properties=["data-testid"],
                        **{"data-testid": "reg-agent-id"}
                    )
                    # Agent type selection with templates
                    v3.VSelect(
                        v_model=("reg_agent_type",),
                        items=[t["value"] for t in AGENT_TYPE_TEMPLATES],
                        label="Agent Type",
                        variant="outlined",
                        density="compact",
                        classes="mb-3",
                        __properties=["data-testid"],
                        **{"data-testid": "reg-agent-type"}
                    )
                    # Model selection
                    v3.VSelect(
                        v_model=("reg_agent_model",),
                        items=[
                            "claude-sonnet-4-20250514",
                            "claude-opus-4-5-20251101",
                            "llama3.1:latest",
                        ],
                        label="Model",
                        variant="outlined",
                        density="compact",
                        classes="mb-3",
                    )
                    # Rules bundle (pre-filled from type template)
                    v3.VCombobox(
                        v_model=("reg_agent_rules",),
                        label="Rules Bundle",
                        variant="outlined",
                        density="compact",
                        multiple=True,
                        chips=True,
                        closable_chips=True,
                        hint="Rules this agent must comply with",
                        persistent_hint=True,
                        classes="mb-3",
                        __properties=["data-testid"],
                        **{"data-testid": "reg-agent-rules"}
                    )
                    # Instructions
                    v3.VTextarea(
                        v_model=("reg_agent_instructions",),
                        label="Instructions",
                        placeholder="Agent-specific instructions...",
                        variant="outlined",
                        rows=3,
                        classes="mb-3",
                    )

            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click=(
                        "show_agent_registration = false"
                    ),
                )
                v3.VBtn(
                    "Register",
                    color="primary",
                    loading=("reg_agent_loading",),
                    disabled=("!reg_agent_name || !reg_agent_id",),
                    click=(
                        "trigger('register_agent', ["
                        "reg_agent_id, reg_agent_name, reg_agent_type, "
                        "reg_agent_model, reg_agent_rules, reg_agent_instructions"
                        "])"
                    ),
                    __properties=["data-testid"],
                    **{"data-testid": "reg-agent-submit-btn"}
                )
