"""
Chat Header Components.

Per RULE-012: Single Responsibility - chat header display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-CHAT-001: Agent command interface.
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
