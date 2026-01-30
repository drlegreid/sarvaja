"""
Search View for Governance Dashboard.

Per RULE-012: Single Responsibility - only evidence search UI.
Per GAP-FILE-001: Modularization of governance_dashboard.py.
Per GAP-UI-009: Search functionality implementation.

Extracted from governance_dashboard.py lines 3011-3028.
Updated: 2026-01-02 (GAP-UI-009)
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

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "search-loading"}
        )

        with v3.VCardText():
            # Search input with button - Per UI-RESP-01-v1: Responsive
            with v3.VRow(classes="align-center"):
                with v3.VCol(cols=12, sm=9, md=10):
                    v3.VTextField(
                        v_model="search_query",
                        label="Search evidence...",
                        prepend_icon="mdi-magnify",
                        variant="outlined",
                        density="compact",
                        clearable=True,
                        __properties=["data-testid"],
                        **{"data-testid": "search-input"}
                    )
                with v3.VCol(cols=12, sm=3, md=2):
                    v3.VBtn(
                        "Search",
                        color="primary",
                        click="trigger('perform_search')",
                        disabled=("!search_query",),
                        __properties=["data-testid"],
                        **{"data-testid": "search-btn"}
                    )

            # Empty state - no query
            html.Div(
                v_if="!search_query && (!search_results || search_results.length === 0)",
                classes="text-grey text-center py-4"
            ).add_child(
                html.Span("Enter a search query to find evidence")
            )

            # No results state
            html.Div(
                v_if="search_query && search_results && search_results.length === 0",
                classes="text-grey text-center py-4",
                __properties=["data-testid"],
                **{"data-testid": "search-no-results"}
            ).add_child(
                html.Span("No results found for '{{ search_query }}'")
            )

            # Results count
            html.Div(
                v_if="search_results && search_results.length > 0",
                classes="mb-2 text-grey",
                __properties=["data-testid"],
                **{"data-testid": "search-results-count"}
            ).add_child(
                html.Span("{{ search_results.length }} results found")
            )

            # Results grid (PLAN-UI-OVERHAUL-001 Task 1.4: Evidence Grid)
            v3.VDataTable(
                v_if="search_results && search_results.length > 0",
                items=("search_results",),
                headers=[
                    {"title": "Source", "key": "source", "sortable": True},
                    {"title": "Type", "key": "source_type", "width": "120px", "sortable": True},
                    {"title": "Score", "key": "score", "width": "100px", "sortable": True},
                    {"title": "Content", "key": "content", "sortable": False},
                ],
                item_value="source",
                density="compact",
                items_per_page=20,
                hover=True,
                __properties=["data-testid"],
                **{"data-testid": "search-results-table"}
            )
