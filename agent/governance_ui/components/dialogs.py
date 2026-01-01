"""
Dialog components for Governance Dashboard.

Per RULE-012: Single Responsibility - only dialog UI patterns.
Per RULE-019: UI/UX Standards - consistent dialog patterns.
"""

from trame.widgets import vuetify3 as v3, html


def build_confirm_dialog(
    v_model: str,
    title: str,
    message: str,
    confirm_action: str,
    cancel_action: str = None,
    confirm_color: str = "error"
) -> None:
    """
    Build a confirmation dialog.

    Args:
        v_model: State variable controlling dialog visibility
        title: Dialog title
        message: Confirmation message
        confirm_action: Action to trigger on confirm
        cancel_action: Action to trigger on cancel (defaults to closing)
        confirm_color: Color for confirm button
    """
    with v3.VDialog(v_model=v_model, max_width="400"):
        with v3.VCard():
            v3.VCardTitle(title)
            with v3.VCardText():
                html.Span(message)
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Cancel",
                    variant="text",
                    click=cancel_action or f"{v_model} = false"
                )
                v3.VBtn(
                    "Confirm",
                    color=confirm_color,
                    click=confirm_action
                )


def build_error_dialog() -> None:
    """Build a global error dialog."""
    with v3.VDialog(v_model="has_error", max_width="500"):
        with v3.VCard():
            with v3.VCardTitle(classes="text-error"):
                v3.VIcon("mdi-alert-circle", classes="mr-2")
                html.Span("Error")
            with v3.VCardText():
                html.Span("{{ error_message }}")
            with v3.VCardActions():
                v3.VSpacer()
                v3.VBtn(
                    "Close",
                    color="primary",
                    click="has_error = false"
                )


def build_loading_overlay() -> None:
    """Build a loading overlay."""
    with v3.VOverlay(v_model="is_loading", persistent=True):
        v3.VProgressCircular(indeterminate=True, size="64")
