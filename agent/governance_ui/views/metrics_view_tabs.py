"""
Metrics View Search & Timeline Tabs.

Per DOC-SIZE-01-v1: Extracted from metrics_view.py (410 lines).
Search tab with content search + results, and timeline tab with daily cards.
"""

from trame.widgets import vuetify3 as v3, html


def build_search_tab() -> None:
    """Build the search tab content."""
    with html.Div(v_if="metrics_active_tab === 'search'"):
        with v3.VRow(classes="mt-2"):
            with v3.VCol(cols=12, md=8):
                v3.VTextField(
                    v_model="metrics_search_query",
                    label="Search session content...",
                    prepend_inner_icon="mdi-magnify",
                    variant="outlined",
                    density="compact",
                    clearable=True,
                    __properties=["data-testid"],
                    **{
                        "data-testid": "metrics-search-input",
                        "v-on:keydown.enter": "trigger('search_metrics')",
                    }
                )
            with v3.VCol(cols=12, md=4):
                v3.VBtn(
                    "Search",
                    prepend_icon="mdi-magnify",
                    color="primary",
                    block=True,
                    click="trigger('search_metrics')",
                    loading=("metrics_search_loading",),
                    __properties=["data-testid"],
                    **{"data-testid": "metrics-search-btn"}
                )

        # Results count
        v3.VAlert(
            v_if="metrics_search_results && metrics_search_results.length > 0",
            type="info",
            density="compact",
            classes="mb-2",
            v_text="'Found ' + metrics_search_total + ' matches'",
        )

        # Results list
        with v3.VList(
            v_if="metrics_search_results && metrics_search_results.length > 0",
            density="compact",
            __properties=["data-testid"],
            **{"data-testid": "metrics-search-results"}
        ):
            with v3.VListItem(
                v_for="(result, idx) in metrics_search_results",
                key="idx",
            ):
                with v3.VListItemTitle():
                    html.Span(
                        "{{ result.timestamp }}",
                        classes="text-caption text-grey mr-2"
                    )
                    v3.VChip(
                        v_if="result.session_id",
                        v_text="result.session_id",
                        size="x-small",
                        color="info",
                        classes="mr-1"
                    )
                    v3.VChip(
                        v_if="result.git_branch",
                        v_text="result.git_branch",
                        size="x-small",
                        color="secondary",
                    )
                with v3.VListItemSubtitle():
                    html.Span("{{ result.text_content }}")

        # Empty search state
        v3.VAlert(
            v_if="!metrics_search_loading && metrics_search_results && metrics_search_results.length === 0 && metrics_search_query",
            type="info",
            density="compact",
            text="No matches found. Try different search terms.",
        )


def build_timeline_tab() -> None:
    """Build the timeline tab content."""
    with html.Div(v_if="metrics_active_tab === 'timeline'"):
        v3.VBtn(
            "Load Timeline",
            prepend_icon="mdi-timeline-text",
            variant="outlined",
            size="small",
            classes="mt-2 mb-4",
            click="trigger('load_metrics_timeline')",
            loading=("metrics_timeline_loading",),
            __properties=["data-testid"],
            **{"data-testid": "metrics-timeline-btn"}
        )

        # Timeline cards
        with v3.VRow(
            v_if="metrics_timeline && metrics_timeline.length > 0",
            __properties=["data-testid"],
            **{"data-testid": "metrics-timeline"}
        ):
            with v3.VCol(
                v_for="day in metrics_timeline",
                key="day.date",
                cols=12,
                md=6,
                lg=4,
            ):
                with v3.VCard(variant="outlined"):
                    with v3.VCardTitle(classes="d-flex align-center"):
                        v3.VIcon("mdi-calendar", classes="mr-2", size="small")
                        html.Span("{{ day.date }}")
                        v3.VSpacer()
                        v3.VChip(
                            v_text="day.entry_count + ' entries'",
                            size="x-small",
                            color="info",
                        )
                    with v3.VCardText():
                        # Tools
                        with html.Div(
                            v_if="day.tools_used && day.tools_used.length > 0",
                            classes="mb-2"
                        ):
                            html.Span("Tools: ", classes="text-caption text-grey")
                            v3.VChip(
                                v_for="tool in day.tools_used",
                                key="tool",
                                v_text="tool",
                                size="x-small",
                                classes="mr-1 mb-1",
                                variant="outlined",
                            )
                        # Branches
                        with html.Div(
                            v_if="day.branches && day.branches.length > 0",
                            classes="mb-2"
                        ):
                            html.Span("Branches: ", classes="text-caption text-grey")
                            v3.VChip(
                                v_for="branch in day.branches",
                                key="branch",
                                v_text="branch",
                                size="x-small",
                                color="secondary",
                                classes="mr-1 mb-1",
                            )
                        # Snippets
                        with html.Div(v_if="day.snippets && day.snippets.length > 0"):
                            html.Div(
                                v_for="(snippet, i) in day.snippets",
                                key="i",
                                v_text="snippet",
                                classes="text-body-2 text-grey-darken-1 mb-1"
                            )
