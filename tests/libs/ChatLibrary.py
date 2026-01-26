"""
Chat Library for Robot Framework (Facade)
Combines all chat test libraries.
Migrated from tests/test_chat.py
Per: RF-005 Robot Framework Migration, DOC-SIZE-01-v1
"""
import sys
from pathlib import Path

# Add libs directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ChatStateLibrary import ChatStateLibrary
from ChatMessageLibrary import ChatMessageLibrary
from ChatAPILibrary import ChatAPILibrary
from ChatIntegrationLibrary import ChatIntegrationLibrary


class ChatLibrary(
    ChatStateLibrary,
    ChatMessageLibrary,
    ChatAPILibrary,
    ChatIntegrationLibrary
):
    """
    Facade library combining all chat test keywords.

    Split libraries:
    - ChatStateLibrary: State constants, transforms, helpers (11 keywords)
    - ChatMessageLibrary: Message formatting, creation (5 keywords)
    - ChatAPILibrary: API models, command processing (11 keywords)
    - ChatIntegrationLibrary: Session management, integration (6 keywords)

    Total: 33 keywords
    """

    ROBOT_LIBRARY_SCOPE = 'SUITE'
