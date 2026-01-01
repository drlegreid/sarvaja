"""
Card components for Governance Dashboard.

Per RULE-012: Single Responsibility - only card UI patterns.
Per RULE-019: UI/UX Standards - consistent card patterns.
"""

from trame.widgets import vuetify3 as v3, html


def build_entity_card(
    title: str,
    subtitle: str = None,
    icon: str = None,
    actions: list = None
) -> None:
    """
    Build a standard entity card.

    Args:
        title: Card title
        subtitle: Optional subtitle
        icon: Optional icon name
        actions: List of action dicts with {label, click, color}
    """
    with v3.VCard(classes="mb-4"):
        with v3.VCardTitle(classes="d-flex align-center"):
            if icon:
                v3.VIcon(icon, classes="mr-2")
            html.Span(title)
            if actions:
                v3.VSpacer()
                for action in actions:
                    v3.VBtn(
                        action.get("label", ""),
                        color=action.get("color", "primary"),
                        click=action.get("click", ""),
                        variant="text"
                    )
        if subtitle:
            v3.VCardSubtitle(subtitle)


def build_stat_card(
    icon: str,
    value: str,
    label: str,
    color: str = "primary"
) -> None:
    """
    Build a statistics card.

    Args:
        icon: Icon name
        value: Main statistic value
        label: Label for the statistic
        color: Icon color
    """
    with v3.VCard(variant="outlined"):
        with v3.VCardText(classes="text-center"):
            v3.VIcon(icon, size="32", color=color)
            html.Div(value, classes="text-h4 my-2")
            html.Div(label, classes="text-caption text-grey")


def build_detail_field(label: str, value: str) -> None:
    """
    Build a detail field display.

    Args:
        label: Field label
        value: Field value (can include {{ }} for reactive binding)
    """
    html.Div(label, classes="text-caption text-grey")
    html.Div(value, classes="text-body-1 mb-3")
