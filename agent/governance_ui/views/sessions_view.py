"""
Sessions View for Governance Dashboard.

Per RULE-012: Single Responsibility - only session evidence UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per RULE-032: File size limit - modularized into sessions/ subpackage.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- sessions/list.py: List view (~60 lines)
- sessions/content.py: Metadata chips and info card (~75 lines)
- sessions/evidence.py: Evidence files and attach dialog (~95 lines)
- sessions/detail.py: Detail view (~70 lines)
- sessions/form.py: Create/edit form (~95 lines)
"""

from .sessions import (
    build_sessions_list_view,
    build_session_detail_view,
    build_session_form_view,
    build_evidence_attach_dialog,
)


def build_sessions_view() -> None:
    """
    Build the complete Sessions view including list, detail, and form.

    This is the main entry point for the sessions view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    Per P11.5: Session Evidence Attachments.
    Per GAP-UI-034: Session CRUD operations.
    """
    build_sessions_list_view()
    build_session_detail_view()
    build_session_form_view()
    build_evidence_attach_dialog()
