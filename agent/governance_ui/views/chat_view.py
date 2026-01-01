"""
Chat View for Governance Dashboard.

Per RULE-012: Single Responsibility - only chat/agent interaction UI.
Per GAP-UI-CHAT-001/002: Agent command interface.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 3033-3211.
"""

from trame.widgets import vuetify3 as v3, html


def build_chat_header() -> None:
    """Build chat header with agent selector."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-chat", classes="mr-2")
        html.Span("Agent Chat")
        v3.VSpacer()
        # Agent selector
        v3.VSelect(
            v_model="chat_selected_agent",
            items=("agents.map(a => ({title: a.name, value: a.agent_id}))",),
            label="Agent",
            variant="outlined",
            density="compact",
            clearable=True,
            style="max-width: 200px;",
            __properties=["data-testid"],
            **{"data-testid": "chat-agent-select"}
        )


def build_chat_welcome() -> None:
    """Build welcome message for new chat."""
    with v3.VAlert(
        v_if="chat_messages.length === 0",
        type_="info",
        variant="tonal",
        classes="mb-4"
    ):
        html.Div("Welcome to Agent Chat! Type a command or ask a question.")
        html.Div("Try /help to see available commands.", classes="text-caption mt-1")


def build_user_message() -> None:
    """Build user message card (right aligned)."""
    with v3.VCard(
        v_if="msg.role === 'user'",
        color="primary",
        variant="tonal",
        classes="ml-auto",
        style="max-width: 80%;"
    ):
        with v3.VCardText(classes="py-2"):
            html.Pre(
                "{{ msg.content }}",
                style="white-space: pre-wrap; margin: 0; font-family: inherit;"
            )
            html.Div(
                "{{ msg.timestamp }}",
                classes="text-caption text-right mt-1"
            )


def build_agent_message() -> None:
    """Build agent message card (left aligned)."""
    with v3.VCard(
        v_if="msg.role === 'agent'",
        color="success",
        variant="tonal",
        classes="mr-auto",
        style="max-width: 80%;"
    ):
        with v3.VCardText(classes="py-2"):
            with html.Div(classes="d-flex align-center mb-1"):
                v3.VIcon("mdi-robot", size="small", classes="mr-1")
                html.Span(
                    "{{ msg.agent_name || 'Agent' }}",
                    classes="text-caption font-weight-bold"
                )
            html.Pre(
                "{{ msg.content }}",
                style="white-space: pre-wrap; margin: 0; font-family: inherit;"
            )
            html.Div(
                "{{ msg.timestamp }}",
                classes="text-caption mt-1"
            )


def build_system_message() -> None:
    """Build system message (centered)."""
    with v3.VAlert(
        v_if="msg.role === 'system'",
        type_="info",
        variant="tonal",
        density="compact"
    ):
        html.Span("{{ msg.content }}")


def build_chat_messages() -> None:
    """Build the chat messages area."""
    with v3.VCardText(
        classes="flex-grow-1 overflow-y-auto",
        style="max-height: calc(100vh - 300px); min-height: 400px;"
    ):
        # System welcome message
        build_chat_welcome()

        # Message list
        with html.Div(
            v_for="(msg, idx) in chat_messages",
            key="idx",
            classes="mb-3"
        ):
            build_user_message()
            build_agent_message()
            build_system_message()

        # Loading indicator
        with html.Div(
            v_if="chat_loading",
            classes="d-flex align-center justify-center pa-4"
        ):
            v3.VProgressCircular(
                indeterminate=True,
                size=24,
                width=2
            )
            html.Span("Agent is thinking...", classes="ml-2")


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
                    "@keyup.enter": "$trigger('send_chat_message')"
                }
            )
            v3.VBtn(
                icon="mdi-send",
                color="primary",
                click="$trigger('send_chat_message')",
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
                click="chat_input = '/help'; $trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-help"}
            )
            v3.VChip(
                "/status",
                size="small",
                variant="outlined",
                click="chat_input = '/status'; $trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-status"}
            )
            v3.VChip(
                "/tasks",
                size="small",
                variant="outlined",
                click="chat_input = '/tasks'; $trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-tasks"}
            )
            v3.VChip(
                "/rules",
                size="small",
                variant="outlined",
                click="chat_input = '/rules'; $trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-rules"}
            )
            v3.VChip(
                "/agents",
                size="small",
                variant="outlined",
                click="chat_input = '/agents'; $trigger('send_chat_message')",
                __properties=["data-testid"],
                **{"data-testid": "chat-cmd-agents"}
            )


def build_chat_view() -> None:
    """
    Build the Agent Chat view.

    This is the main entry point for the chat view module.
    Per ORCH-006: Interactive agent command interface.
    """
    with v3.VCard(
        v_if="active_view === 'chat'",
        classes="fill-height d-flex flex-column",
        __properties=["data-testid"],
        **{"data-testid": "chat-view"}
    ):
        build_chat_header()
        build_chat_messages()
        build_chat_input()
        build_quick_commands()
