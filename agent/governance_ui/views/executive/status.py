"""
Executive Status and Evidence Components.

Per RULE-012: Single Responsibility - only status banner and evidence UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-046: Reports are per-session with evidence summary.
"""

from trame.widgets import vuetify3 as v3, html


def build_status_banner() -> None:
    """Build status banner at top of report (GAP-UI-046: per-session)."""
    with v3.VAlert(
        v_bind_type=(
            "executive_report.overall_status === 'healthy' ? 'success' : "
            "executive_report.overall_status === 'warning' ? 'warning' : 'error'",
        ),
        density="compact",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "executive-status-banner"}
    ):
        with html.Div(classes="d-flex align-center"):
            v3.VIcon(
                v_bind_icon=(
                    "executive_report.overall_status === 'healthy' ? 'mdi-check-circle' : "
                    "executive_report.overall_status === 'warning' ? 'mdi-alert' : "
                    "'mdi-alert-circle'",
                ),
                classes="mr-2"
            )
            # Session ID and date (GAP-UI-046)
            html.Span(
                "Session: {{ executive_report.session_id || executive_session_id }}",
                classes="font-weight-bold"
            )
            v3.VChip(
                v_if="executive_report.session_date",
                v_text="executive_report.session_date",
                size="small",
                prepend_icon="mdi-calendar",
                classes="ml-2"
            )
            v3.VSpacer()
            html.Span(
                "Generated: {{ executive_report.generated_at }}",
                classes="text-caption"
            )


def build_session_evidence_section() -> None:
    """Build session evidence summary section (GAP-UI-046)."""
    with v3.VCard(
        v_if="executive_report.session_evidence",
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "session-evidence-section"}
    ):
        with v3.VCardTitle(classes="d-flex align-center", density="compact"):
            v3.VIcon("mdi-file-document-multiple", classes="mr-2", size="small")
            html.Span("Session Evidence")
            v3.VSpacer()
            v3.VBtn(
                "View Full Session",
                variant="text",
                size="small",
                prepend_icon="mdi-open-in-new",
                click=(
                    "active_view = 'sessions'; "
                    "selected_session = sessions.find("
                    "s => (s.session_id || s.id) === executive_session_id); "
                    "show_session_detail = true"
                )
            )
        with v3.VCardText():
            # Evidence stats
            with v3.VRow(dense=True):
                with v3.VCol(cols=3):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ executive_report.session_evidence.decisions_count || 0 }}",
                            classes="text-h6"
                        )
                        html.Div("Decisions", classes="text-caption text-grey")
                with v3.VCol(cols=3):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ executive_report.session_evidence.tasks_count || 0 }}",
                            classes="text-h6"
                        )
                        html.Div("Tasks", classes="text-caption text-grey")
                with v3.VCol(cols=3):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ executive_report.session_evidence.gaps_resolved || 0 }}",
                            classes="text-h6"
                        )
                        html.Div("Gaps Resolved", classes="text-caption text-grey")
                with v3.VCol(cols=3):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ executive_report.session_evidence.artifacts_count || 0 }}",
                            classes="text-h6"
                        )
                        html.Div("Artifacts", classes="text-caption text-grey")

            # Key highlights
            with html.Div(
                v_if="executive_report.session_evidence.highlights?.length > 0",
                classes="mt-3"
            ):
                html.Div("Key Highlights", classes="text-subtitle-2 mb-2")
                with v3.VList(density="compact"):
                    with v3.VListItem(
                        v_for=(
                            "(highlight, idx) in "
                            "executive_report.session_evidence.highlights"
                        ),
                        key="idx"
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon("mdi-check", color="success", size="small")
                        with v3.VListItemTitle():
                            html.Span("{{ highlight }}")
