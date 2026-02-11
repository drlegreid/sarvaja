"""
Projects View Package.

Per GOV-PROJECT-01-v1: Project hierarchy navigation.
Per RULE-012: Single Responsibility - only project UI.
"""

from .list import build_projects_list_view

__all__ = [
    "build_projects_list_view",
]
