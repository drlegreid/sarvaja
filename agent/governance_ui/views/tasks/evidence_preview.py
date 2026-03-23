"""Task Evidence Preview — Rendered HTML Display.

Per SRVJ-FEAT-009: Task detail view renders evidence as HTML preview.
Follows session evidence pattern (views/sessions/evidence_preview.py).

Created: 2026-03-23
"""

from trame.widgets import vuetify3 as v3, html


def build_task_evidence_preview() -> None:
    """Build inline evidence preview with rendered HTML for tasks."""
    with v3.VCard(
        v_if="task_evidence_files && task_evidence_files.length > 0",
        classes="mt-4",
        variant="outlined",
        __properties=["data-testid"],
        **{"data-testid": "task-evidence-preview"},
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VIcon("mdi-file-document-check", classes="mr-2", size="small")
            html.Span("Evidence")
            v3.VSpacer()
            v3.VChip(
                v_text="task_evidence_files.length + ' file(s)'",
                size="x-small",
                color="success",
                variant="tonal",
            )

        with v3.VCardText():
            # Loading state
            v3.VProgressLinear(
                v_if="task_evidence_loading",
                indeterminate=True,
                color="primary",
            )
            # Rendered evidence files
            with html.Div(
                v_for="(ev, idx) in task_evidence_files",
                key="idx",
                v_if="!task_evidence_loading",
            ):
                # Source label
                html.P(
                    v_text="ev.source",
                    classes="text-caption text-medium-emphasis mb-1",
                    style="font-family: monospace;",
                )
                # Rendered HTML content
                html.Div(
                    v_html="ev.html",
                    classes="evidence-rendered pa-2 mb-3",
                    style=(
                        "max-height: 300px; overflow-y: auto; "
                        "font-size: 0.875rem; line-height: 1.5; "
                        "border: 1px solid rgba(128,128,128,0.2); "
                        "border-radius: 4px;"
                    ),
                )
