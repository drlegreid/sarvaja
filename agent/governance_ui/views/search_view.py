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
            # Search input with button
            with v3.VRow(classes="align-center"):
                with v3.VCol(cols=10):
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
                with v3.VCol(cols=2):
                    v3.VBtn(
                        "Search",
                        color="primary",
                        click="trigger('perform_search')",
                        disabled="!search_query",
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

            # Results list
            with v3.VList(
                v_if="search_results && search_results.length > 0",
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "search-results"}
            ):
                with v3.VListItem(
                    v_for="result in search_results",
                    key=("result.source",),
                    __properties=["data-testid"],
                    **{"data-testid": "search-result-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        v3.VIcon(
                            icon=(
                                "result.source_type === 'rule' ? 'mdi-gavel' : "
                                "result.source_type === 'session' ? 'mdi-clock-outline' : "
                                "result.source_type === 'decision' ? 'mdi-scale-balance' : "
                                "'mdi-file-document-outline'"
                            ),
                            color=(
                                "result.source_type === 'rule' ? 'primary' : "
                                "result.source_type === 'session' ? 'info' : "
                                "result.source_type === 'decision' ? 'warning' : 'grey'"
                            )
                        )
                    with v3.VListItemTitle():
                        html.Span("{{ result.source }}")
                    with v3.VListItemSubtitle():
                        # Source type badge
                        v3.VChip(
                            v_text="result.source_type",
                            size="x-small",
                            color="secondary",
                            variant="tonal",
                            classes="mr-2"
                        )
                        # Relevance score
                        v3.VChip(
                            v_text="'Score: ' + (result.score || 0)",
                            size="x-small",
                            color="info",
                            variant="tonal"
                        )
                    # Content preview
                    with html.Div(classes="text-caption text-grey mt-1"):
                        html.Span(
                            "{{ result.content ? result.content.substring(0, 150) + '...' : 'No preview available' }}"
                        )
