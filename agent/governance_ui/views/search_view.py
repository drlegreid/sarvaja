"""
Search View for Governance Dashboard.

Per RULE-012: Single Responsibility - only evidence search UI.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 3011-3028.
"""

from trame.widgets import vuetify3 as v3, html


def build_search_view() -> None:
    """
    Build the Evidence Search view.

    This is the main entry point for the search view module.
    Provides semantic search across all evidence artifacts.
    """
    with v3.VCard(
        v_if="active_view === 'search'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "search-view"}
    ):
        v3.VCardTitle("Evidence Search")
        with v3.VCardText():
            v3.VTextField(
                v_model="search_query",
                label="Search evidence...",
                prepend_icon="mdi-magnify",
                variant="outlined",
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "search-input"}
            )
            # TODO: Results list to be populated on search
            html.Div(
                "Enter a search query to find evidence",
                v_if="!search_query",
                classes="text-grey text-center py-4"
            )
