"""
Resolution Section Component — Task Detail View.

Per EPIC-TASK-QUALITY-V3 Phase 17: Issue Resolution Evidence Trail.
Shows resolution_notes as markdown-rendered content below the execution log.
Only visible when resolution_notes is non-empty.
"""

from trame.widgets import vuetify3 as v3, html


def build_task_resolution_section() -> None:
    """Build the resolution notes section for task detail view.

    Displays resolution_notes as pre-formatted markdown content
    in a collapsible expansion panel. Only visible when the field
    is non-empty and not in edit mode.
    """
    with html.Div(
        v_if=(
            "!edit_task_mode && selected_task.resolution_notes"
        ),
        classes="mt-4",
        __properties=["data-testid"],
        **{"data-testid": "task-resolution-section"},
    ):
        with v3.VExpansionPanels(model_value=0):
            with v3.VExpansionPanel():
                with v3.VExpansionPanelTitle():
                    v3.VIcon(
                        "mdi-file-document-check-outline",
                        size="small",
                        color="success",
                        classes="mr-2",
                    )
                    html.Span(
                        "Resolution",
                        classes="text-subtitle-1 font-weight-bold",
                    )
                with v3.VExpansionPanelText():
                    html.Pre(
                        "{{ selected_task.resolution_notes }}",
                        style=(
                            "white-space: pre-wrap; "
                            "font-family: monospace; "
                            "font-size: 0.85rem; "
                            "padding: 12px; "
                            "border-radius: 4px; "
                            "max-height: 400px; "
                            "overflow-y: auto;"
                        ),
                        classes="bg-surface-variant",
                        __properties=["data-testid"],
                        **{"data-testid": "task-resolution-content"},
                    )
