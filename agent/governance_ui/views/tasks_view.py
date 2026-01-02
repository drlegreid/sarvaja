"""
Tasks View for Governance Dashboard.

Per RULE-012: Single Responsibility - only tasks list/detail UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per RULE-032: File size limit - modularized into tasks/ subpackage.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- tasks/list.py: List view (~80 lines)
- tasks/forms.py: Edit form and content preview (~140 lines)
- tasks/execution.py: Execution log timeline (~125 lines)
- tasks/detail.py: Detail view (~165 lines)
"""

from .tasks import build_tasks_list_view, build_task_detail_view


def build_tasks_view() -> None:
    """
    Build the complete Tasks view including list and detail.

    This is the main entry point for the tasks view module.
    Per RULE-019: UI/UX Standards - consistent view patterns.
    """
    build_tasks_list_view()
    build_task_detail_view()
