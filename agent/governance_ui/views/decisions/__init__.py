"""
Decisions View Subpackage.

Per RULE-012: DSP Hygiene - modular code structure.
Per RULE-032: File size limit (<300 lines per file).

This package splits the decisions_view.py (380 lines) into focused modules:
- list.py: Decisions list view (~60 lines)
- content.py: Content preview and info cards (~140 lines)
- detail.py: Decision detail view (~80 lines)
- form.py: Create/edit form (~100 lines)
"""

from .list import build_decisions_list_view
from .detail import build_decision_detail_view
from .form import build_decision_form_view

__all__ = [
    "build_decisions_list_view",
    "build_decision_detail_view",
    "build_decision_form_view",
]
