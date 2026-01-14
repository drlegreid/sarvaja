"""
Context Preloader Package.

Per GAP-FILE-022: Split from monolithic context_preloader.py (428 lines)
Per DOC-SIZE-01-v1: Files under 400 lines

Maintains backward compatibility by re-exporting all public symbols.

Modules:
    - models: Data classes (Decision, TechnologyChoice, ContextSummary)
    - preloader: ContextPreloader class and factory functions

Created: 2026-01-14
"""

# Re-export models for backward compatibility
from .models import Decision, TechnologyChoice, ContextSummary

# Re-export preloader for backward compatibility
from .preloader import (
    ContextPreloader,
    get_context_preloader,
    preload_session_context,
    get_agent_context_prompt,
)

__all__ = [
    # Models
    "Decision",
    "TechnologyChoice",
    "ContextSummary",
    # Preloader
    "ContextPreloader",
    "get_context_preloader",
    "preload_session_context",
    "get_agent_context_prompt",
]
