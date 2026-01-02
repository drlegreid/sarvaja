"""
Decisions View for Governance Dashboard.

Per RULE-012: Single Responsibility - only decisions list/detail UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per RULE-032: File size limit - modularized into decisions/ subpackage.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- decisions/list.py: List view (~60 lines)
- decisions/content.py: Content preview and info cards (~140 lines)
- decisions/detail.py: Detail view (~80 lines)
- decisions/form.py: Create/edit form (~100 lines)
"""

from .decisions import (
    build_decisions_list_view,
    build_decision_detail_view,
    build_decision_form_view,
)


def build_decisions_view() -> None:
    """
    Build the complete Decisions view including list, detail, and form.

    This is the main entry point for the decisions view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    Per GAP-UI-033: Decision CRUD operations.
    """
    build_decisions_list_view()
    build_decision_detail_view()
    build_decision_form_view()
