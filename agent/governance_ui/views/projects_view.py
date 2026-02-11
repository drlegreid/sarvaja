"""
Projects View for Governance Dashboard.

Per GOV-PROJECT-01-v1: Project hierarchy navigation.
Per RULE-012: Single Responsibility - only project navigation UI.
"""

from .projects import build_projects_list_view


def build_projects_view() -> None:
    """Build the complete Projects view."""
    build_projects_list_view()
