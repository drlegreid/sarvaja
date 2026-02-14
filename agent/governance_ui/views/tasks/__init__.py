"""
Tasks View Subpackage.

Per RULE-012: DSP Hygiene - modular code structure.
Per RULE-032: File size limit (<300 lines per file).

This package splits the tasks_view.py (514 lines) into focused modules:
- list.py: Tasks list view (~80 lines)
- forms.py: Edit form and content preview (~140 lines)
- execution.py: Execution log timeline (~125 lines)
- detail.py: Task detail view (~165 lines)
"""

from .list import build_tasks_list_view
from .detail import build_task_detail_view
from .forms import build_task_create_dialog
from .attach_dialog import build_attach_document_dialog

__all__ = [
    "build_tasks_list_view",
    "build_task_detail_view",
    "build_task_create_dialog",
    "build_attach_document_dialog",
]
