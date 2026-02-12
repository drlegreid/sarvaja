"""
Navigation component for Governance Dashboard.

Per RULE-012: Single Responsibility - only navigation UI.
Per RULE-019: UI/UX Standards - consistent navigation pattern.

NOTE: NAVIGATION_ITEMS imported from constants.py (single source of truth).
"""

from trame.widgets import vuetify3 as v3, html
from typing import List, Dict, Any

from agent.governance_ui.state.constants import NAVIGATION_ITEMS


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
