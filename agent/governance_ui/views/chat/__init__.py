"""
Chat View Subpackage.

Per RULE-012: DSP Hygiene - modular code structure.
Per RULE-032: File size limit (<300 lines per file).

This package splits the chat_view.py (360 lines) into focused modules:
- header.py: Chat header and welcome (~45 lines)
- messages.py: Message components and area (~100 lines)
- input.py: Input area and quick commands (~85 lines)
- execution.py: Task execution button and viewer (~140 lines)
"""

from .header import build_chat_header
from .messages import build_chat_messages
from .input import build_chat_input, build_quick_commands
from .execution import build_task_execution_button, build_task_execution_viewer

__all__ = [
    "build_chat_header",
    "build_chat_messages",
    "build_chat_input",
    "build_quick_commands",
    "build_task_execution_button",
    "build_task_execution_viewer",
]
