"""
Sessions View Subpackage.

Per RULE-012: DSP Hygiene - modular code structure.
Per RULE-032: File size limit (<300 lines per file).

This package splits the sessions_view.py (376 lines) into focused modules:
- list.py: Sessions list view (~60 lines)
- content.py: Metadata chips and info card (~75 lines)
- evidence.py: Evidence files and attach dialog (~95 lines)
- detail.py: Session detail view (~70 lines)
- form.py: Create/edit form (~95 lines)
"""

from .list import build_sessions_list_view
from .detail import build_session_detail_view
from .form import build_session_form_view
from .evidence import build_evidence_attach_dialog
from .tasks import build_completed_tasks_card
from .tool_calls import build_tool_calls_card

__all__ = [
    "build_sessions_list_view",
    "build_session_detail_view",
    "build_session_form_view",
    "build_evidence_attach_dialog",
    "build_completed_tasks_card",
    "build_tool_calls_card",
]
