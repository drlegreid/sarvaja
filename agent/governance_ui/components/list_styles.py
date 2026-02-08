"""
List Styles Component for Trame.

Per UI-LIST-01: Consistent list styling across dashboard views.
- Alternating row colors (zebra striping)
- Full-height containers
- Consistent padding and spacing

Created: 2026-02-08
"""

from trame.widgets import html


def inject_list_styles() -> None:
    """
    Inject custom CSS for list styling.

    Features:
    - Alternating row colors for VDataTable (light grey/white)
    - Full-height list containers
    - Consistent row hover states

    Call this once in the layout after VAppLayout starts.
    """
    html.Style(
        """
        /* UI-LIST-01: Alternating row colors for VDataTable */
        .v-data-table tbody tr:nth-child(even) {
            background-color: rgba(0, 0, 0, 0.02) !important;
        }

        .v-theme--dark .v-data-table tbody tr:nth-child(even) {
            background-color: rgba(255, 255, 255, 0.03) !important;
        }

        /* Hover state */
        .v-data-table tbody tr:hover {
            background-color: rgba(var(--v-theme-primary), 0.08) !important;
        }

        /* UI-LIST-01: Full-height list containers */
        [data-testid="rules-list"],
        [data-testid="tasks-list"],
        [data-testid="sessions-list"] {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 120px);
            max-height: calc(100vh - 120px);
        }

        /* Make card text scrollable while keeping header fixed */
        [data-testid="rules-list"] > .v-card-text,
        [data-testid="tasks-list"] > .v-card-text,
        [data-testid="sessions-list"] > .v-card-text {
            flex: 1;
            overflow-y: auto;
            min-height: 0;
        }

        /* Keep card title and toolbar fixed */
        [data-testid="rules-list"] > .v-card-title,
        [data-testid="tasks-list"] > .v-card-title,
        [data-testid="sessions-list"] > .v-card-title,
        [data-testid="rules-list"] > .v-toolbar,
        [data-testid="tasks-list"] > .v-toolbar,
        [data-testid="sessions-list"] > .v-toolbar {
            flex-shrink: 0;
        }

        /* Keep pagination footer fixed at bottom */
        [data-testid="rules-list"] > .v-card-actions,
        [data-testid="tasks-list"] > .v-card-actions,
        [data-testid="sessions-list"] > .v-card-actions,
        [data-testid="tasks-pagination"],
        [data-testid="sessions-pagination"] {
            flex-shrink: 0;
            border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
        }

        /* VList alternating colors (for non-table lists) */
        .v-list-item:nth-child(even) {
            background-color: rgba(0, 0, 0, 0.01);
        }

        .v-theme--dark .v-list-item:nth-child(even) {
            background-color: rgba(255, 255, 255, 0.02);
        }

        /* Consistent row padding */
        .v-data-table tbody tr td {
            padding-top: 8px !important;
            padding-bottom: 8px !important;
        }
        """
    )


__all__ = ["inject_list_styles"]
