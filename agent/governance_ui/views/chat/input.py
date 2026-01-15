"""
Chat Input Components.

Per RULE-012: Single Responsibility - chat input display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-CHAT-001: Agent command interface.
"""

from trame.widgets import vuetify3 as v3, html


def build_chat_input() -> None:
    """Build the chat input area."""
    v3.VDivider()

    with v3.VCardActions(classes="pa-4"):
        with html.Div(classes="d-flex w-100", style="gap: 8px;"):
            v3.VTextField(
                v_model="chat_input",
                label="Type a message or command...",
                variant="outlined",
                density="compact",
                hide_details=True,
                classes="flex-grow-1",
                __properties=["data-testid", "@keyup.enter"],
                **{
                    "data-testid": "chat-input",
                    "@keyup.enter": "trigger('send_chat_message')"
                }
            )
            v3.VBtn(
                icon="mdi-send",
                color="primary",
                click="trigger('send_chat_message')",
                disabled=("!chat_input || chat_loading",),
                __properties=["data-testid"],
                **{"data-testid": "chat-send-btn"}
            )


def build_quick_commands() -> None:
    """Build quick command chips."""
    with v3.VCardText(classes="pt-0"):
        html.Div("Quick Commands:", classes="text-caption mb-2")
        with html.Div(classes="d-flex flex-wrap", style="gap: 4px;"):
            v3.VChip(
                "/help",
                size="small",
                variant="outlined",
                click="chat_input = '/help'; trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-help"}
            )
            v3.VChip(
                "/status",
                size="small",
                variant="outlined",
                click="chat_input = '/status'; trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-status"}
            )
            v3.VChip(
                "/tasks",
                size="small",
                variant="outlined",
                click="chat_input = '/tasks'; trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-tasks"}
            )
            v3.VChip(
                "/rules",
                size="small",
                variant="outlined",
                click="chat_input = '/rules'; trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-rules"}
            )
            v3.VChip(
                "/agents",
                size="small",
                variant="outlined",
                click="chat_input = '/agents'; trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-agents"}
            )
