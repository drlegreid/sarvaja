"""
Chat View for Governance Dashboard.

Per RULE-012: Single Responsibility - only chat/agent interaction UI.
Per RULE-032: File size limit - modularized into chat/ subpackage.
Per GAP-UI-CHAT-001/002: Agent command interface.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- chat/header.py: Chat header and welcome (~45 lines)
- chat/messages.py: Message components and area (~100 lines)
- chat/input.py: Input area and quick commands (~85 lines)
- chat/execution.py: Task execution button and viewer (~140 lines)
"""

from trame.widgets import vuetify3 as v3

from .chat import (
    build_chat_header,
    build_chat_messages,
    build_chat_input,
    build_quick_commands,
    build_task_execution_button,
    build_task_execution_viewer,
)


def build_chat_view() -> None:
    """
    Build the Agent Chat view.

    This is the main entry point for the chat view module.
    Per ORCH-006: Interactive agent command interface.
    Per GAP-UI-CHAT-002: Task execution viewing.
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
        build_task_execution_button()

    # Task execution viewer dialog (outside main card)
    build_task_execution_viewer()
