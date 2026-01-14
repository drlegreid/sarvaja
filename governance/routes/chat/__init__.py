"""
Chat Routes Package.

Per GAP-FILE-023: Split from monolithic routes/chat.py (421 lines)
Per DOC-SIZE-01-v1: Files under 400 lines

Maintains backward compatibility by re-exporting all public symbols.

Modules:
    - commands: Chat command processing
    - endpoints: FastAPI routes

Created: 2026-01-14
"""

# Re-export router for backward compatibility
from .endpoints import router

# Re-export command processor for backward compatibility
from .commands import process_chat_command

# Expose as _process_chat_command for backward compat with existing imports
_process_chat_command = process_chat_command

__all__ = ["router", "process_chat_command", "_process_chat_command"]
