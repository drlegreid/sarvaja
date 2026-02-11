"""
Navigation component for Governance Dashboard.

Per RULE-012: Single Responsibility - only navigation UI.
Per RULE-019: UI/UX Standards - consistent navigation pattern.
"""

from trame.widgets import vuetify3 as v3, html
from typing import List, Dict, Any


NAVIGATION_ITEMS = [
    {"icon": "mdi-chat", "title": "Chat", "value": "chat"},
    {"icon": "mdi-gavel", "title": "Rules", "value": "rules"},
    {"icon": "mdi-robot", "title": "Agents", "value": "agents"},
    {"icon": "mdi-checkbox-marked", "title": "Tasks", "value": "tasks"},
    # Backlog merged into Tasks (UI-AUDIT-2026-01-19)
    {"icon": "mdi-calendar", "title": "Sessions", "value": "sessions"},
    {"icon": "mdi-chart-bar", "title": "Executive", "value": "executive"},
    {"icon": "mdi-file-document-edit", "title": "Decisions", "value": "decisions"},
    {"icon": "mdi-graph", "title": "Impact", "value": "impact"},
    {"icon": "mdi-shield-account", "title": "Trust", "value": "trust"},
    {"icon": "mdi-monitor-dashboard", "title": "Monitor", "value": "monitor"},
    {"icon": "mdi-check-decagram", "title": "Workflow", "value": "workflow"},
    {"icon": "mdi-server", "title": "Infrastructure", "value": "infra"},
    {"icon": "mdi-test-tube", "title": "Tests", "value": "tests"},  # WORKFLOW-SHELL-01-v1
    {"icon": "mdi-folder-multiple", "title": "Projects", "value": "projects"},  # GOV-PROJECT-01-v1
    # Evidence Search removed - now integrated into Sessions tab (2026-02-08)
]


def build_navigation() -> None:
    """Build the navigation drawer."""
    with v3.VNavigationDrawer(rail=True, permanent=True):
        with v3.VList(nav=True):
            for item in NAVIGATION_ITEMS:
                with v3.VListItem(
                    v_bind_active="active_view === '" + item["value"] + "'",
                    click=f"active_view = '{item['value']}'",
                    __properties=["data-testid"],
                    **{"data-testid": f"nav-{item['value']}"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon(item["icon"])
                    v3.VListItemTitle(item["title"])


def get_navigation_items() -> List[Dict[str, Any]]:
    """Get the list of navigation items for state initialization."""
    return NAVIGATION_ITEMS.copy()
