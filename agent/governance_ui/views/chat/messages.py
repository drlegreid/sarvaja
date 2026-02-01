"""
Chat Messages Components.

Per RULE-012: Single Responsibility - message display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-CHAT-001: Agent command interface.
"""

from trame.widgets import vuetify3 as v3, html

from .header import build_chat_welcome


def build_user_message() -> None:
    """Build user message card (right aligned)."""
    with v3.VCard(
        v_if="msg.role === 'user'",
        color="primary",
        variant="tonal",
        classes="ml-auto",
        style="max-width: 80%;",
        __properties=["data-testid"],
        **{"data-testid": "chat-user-message"},
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
        style="max-width: 80%;",
        __properties=["data-testid"],
        **{"data-testid": "chat-agent-message"},
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
