"""
Shared Dialogs for Governance Dashboard.

Per RULE-012: Single Responsibility - shared dialog components.
Per GAP-UI-038: Document reference viewer (fullscreen modal).

Created: 2026-01-02
"""

from trame.widgets import vuetify3 as v3, html


def build_file_viewer_dialog() -> None:
    """
    Build fullscreen file/document viewer dialog (GAP-UI-038).

    Displays file content in a fullscreen modal with:
    - Path display in header
    - Loading/error states
    - Markdown/code highlighting (when available)
    - Close button
    """
    with v3.VDialog(
        v_model="show_file_viewer",
        fullscreen=True,
        __properties=["data-testid"],
        **{"data-testid": "file-viewer-dialog"}
    ):
        with v3.VCard(classes="fill-height d-flex flex-column"):
            # Header with file path and close button
            with v3.VToolbar(color="primary", density="compact"):
                v3.VBtn(
                    icon="mdi-close",
                    variant="text",
                    click="show_file_viewer = false",
                    __properties=["data-testid"],
                    **{"data-testid": "file-viewer-close-btn"}
                )
                v3.VToolbarTitle(
                    "{{ file_viewer_path }}",
                    __properties=["data-testid"],
                    **{"data-testid": "file-viewer-path"}
                )
                v3.VSpacer()
                # Copy path button
                v3.VBtn(
                    icon="mdi-content-copy",
                    variant="text",
                    click="navigator.clipboard.writeText(file_viewer_path)"
                )

            # Content area
            with v3.VCardText(
                classes="flex-grow-1 overflow-y-auto pa-0",
                style="background: #1e1e1e;"
            ):
                # Loading state
                with html.Div(
                    v_if="file_viewer_loading",
                    classes="d-flex justify-center align-center fill-height"
                ):
                    v3.VProgressCircular(
                        indeterminate=True,
                        size=64,
                        color="primary"
                    )

                # Error state
                with v3.VAlert(
                    v_if="file_viewer_error && !file_viewer_loading",
                    type_="error",
                    variant="tonal",
                    classes="ma-4"
                ):
                    html.Span("{{ file_viewer_error }}")

                # File content
                html.Pre(
                    v_if="file_viewer_content && !file_viewer_loading && !file_viewer_error",
                    v_text="file_viewer_content",
                    style="white-space: pre-wrap; font-family: 'Consolas', "
                          "'Monaco', 'Courier New', monospace; font-size: 14px; "
                          "line-height: 1.5; margin: 0; padding: 16px; "
                          "color: #d4d4d4; background: #1e1e1e; min-height: 100%;",
                    __properties=["data-testid"],
                    **{"data-testid": "file-viewer-content"}
                )

                # Empty content
                with v3.VAlert(
                    v_if=(
                        "!file_viewer_content && !file_viewer_loading && "
                        "!file_viewer_error"
                    ),
                    type_="info",
                    variant="tonal",
                    classes="ma-4"
                ):
                    html.Span("No content available")


def build_confirm_dialog() -> None:
    """Build generic confirmation dialog."""
    with v3.VDialog(
        v_model="show_confirm",
        max_width="400px",
        __properties=["data-testid"],
        **{"data-testid": "confirm-dialog"}
    ):
        with v3.VCard():
            v3.VCardTitle("Confirm Action")
            v3.VCardText("{{ confirm_message }}")
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click="show_confirm = false",
                    __properties=["data-testid"],
                    **{"data-testid": "confirm-cancel-btn"}
                )
                v3.VBtn(
                    "Confirm",
                    color="primary",
                    click="confirm_action && confirm_action(); show_confirm = false",
                    __properties=["data-testid"],
                    **{"data-testid": "confirm-ok-btn"}
                )


def build_all_dialogs() -> None:
    """Build all shared dialogs. Call this once in main dashboard."""
    build_file_viewer_dialog()
    build_confirm_dialog()
