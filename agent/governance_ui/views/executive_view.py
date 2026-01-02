"""
Executive Report View for Governance Dashboard.

Per RULE-012: Single Responsibility - only executive report UI.
Per RULE-029: Executive Reporting Pattern.
Per GAP-FILE-001: Modularization of governance_dashboard.py.
Per GAP-UI-046: Reports are per-session, not quarterly/monthly.

Extracted from governance_dashboard.py lines 2366-2502.
"""

from trame.widgets import vuetify3 as v3, html


def build_session_selector() -> None:
    """Build session selector for executive reports (GAP-UI-046)."""
    with html.Div(classes="d-flex align-center", style="gap: 8px;"):
        v3.VSelect(
            v_model="executive_session_id",
            items=("sessions.map(s => ({title: s.session_id || s.id, value: s.session_id || s.id}))",),
            label="Select Session",
            variant="outlined",
            density="compact",
            hide_details=True,
            style="max-width: 300px;",
            __properties=["data-testid"],
            **{"data-testid": "executive-session-select"}
        )
        v3.VBtn(
            "Generate Report",
            prepend_icon="mdi-file-chart",
            color="primary",
            size="small",
            click="trigger('load_executive_report')",
            disabled=("!executive_session_id",),
            __properties=["data-testid"],
            **{"data-testid": "executive-generate-btn"}
        )


def build_executive_header() -> None:
    """Build executive report header with session selector (GAP-UI-046)."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-chart-box", classes="mr-2")
        html.Span("Executive Report")
        v3.VSpacer()
        # Session selector (replaces period selector per GAP-UI-046)
        build_session_selector()


def build_metrics_summary() -> None:
    """Build metrics summary cards."""
    with v3.VRow(classes="mb-4"):
        with v3.VCol(cols=3):
            with v3.VCard(variant="outlined", classes="text-center pa-2"):
                v3.VIcon("mdi-gavel", size="large", color="primary")
                html.Div(
                    "{{ executive_report.metrics_summary?.total_rules || 0 }}",
                    classes="text-h5 mt-1"
                )
                html.Div("Rules", classes="text-caption")
        with v3.VCol(cols=3):
            with v3.VCard(variant="outlined", classes="text-center pa-2"):
                v3.VIcon("mdi-robot", size="large", color="info")
                html.Div(
                    "{{ executive_report.metrics_summary?.total_agents || 0 }}",
                    classes="text-h5 mt-1"
                )
                html.Div("Agents", classes="text-caption")
        with v3.VCol(cols=3):
            with v3.VCard(variant="outlined", classes="text-center pa-2"):
                v3.VIcon("mdi-checkbox-marked", size="large", color="success")
                html.Div(
                    "{{ executive_report.metrics_summary?.tasks_completed || 0 }}",
                    classes="text-h5 mt-1"
                )
                html.Div("Tasks Done", classes="text-caption")
        with v3.VCol(cols=3):
            with v3.VCard(variant="outlined", classes="text-center pa-2"):
                v3.VIcon("mdi-percent", size="large", color="warning")
                html.Div(
                    "{{ (executive_report.metrics_summary?.compliance_rate || 0)"
                    ".toFixed(0) }}%",
                    classes="text-h5 mt-1"
                )
                html.Div("Compliance", classes="text-caption")


def build_report_sections() -> None:
    """Build report sections with dynamic icons."""
    v3.VDivider(classes="mb-4")
    with html.Div(
        v_for="(section, idx) in executive_report.sections",
        key=("idx",),
    ):
        with v3.VCard(
            variant="outlined",
            classes="mb-3",
            __properties=["data-testid"],
            **{"data-testid": "executive-section"}
        ):
            with v3.VCardTitle(
                density="compact",
                classes="d-flex align-center",
            ):
                v3.VIcon(
                    v_bind_icon=(
                        "section.title.includes('Summary') ? 'mdi-clipboard-text' : "
                        "section.title.includes('Compliance') ? 'mdi-check-decagram' : "
                        "section.title.includes('Risk') ? 'mdi-alert-circle' : "
                        "section.title.includes('Alignment') ? 'mdi-compass' : "
                        "section.title.includes('Resource') ? 'mdi-account-group' : "
                        "section.title.includes('Recommendation') ? 'mdi-lightbulb' : "
                        "section.title.includes('Objective') ? 'mdi-target' : "
                        "'mdi-file-document'",
                    ),
                    classes="mr-2",
                    size="small"
                )
                html.Span("{{ section.title }}")
                v3.VSpacer()
                v3.VChip(
                    v_if="section.status",
                    v_text="section.status",
                    v_bind_color=(
                        "section.status === 'success' ? 'success' : "
                        "section.status === 'warning' ? 'warning' : 'error'"
                    ),
                    size="small",
                    density="compact",
                )
            with v3.VCardText():
                html.P("{{ section.content }}", classes="mb-0")


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
                click="active_view = 'sessions'; selected_session = sessions.find(s => (s.session_id || s.id) === executive_session_id); show_session_detail = true"
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
                        v_for="(highlight, idx) in executive_report.session_evidence.highlights",
                        key="idx"
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon("mdi-check", color="success", size="small")
                        with v3.VListItemTitle():
                            html.Span("{{ highlight }}")


def build_executive_content() -> None:
    """Build the executive report content area."""
    with v3.VCardText():
        # Loading state
        with html.Div(v_if="executive_loading", classes="text-center py-8"):
            v3.VProgressCircular(indeterminate=True, color="primary")
            html.Div("Generating report...", classes="mt-2 text-grey")

        # Error state
        with v3.VAlert(
            v_if="executive_report && executive_report.error",
            type="error",
            density="compact",
        ):
            html.Span("{{ executive_report.error }}")

        # Report content
        with html.Div(
            v_if="executive_report && !executive_report.error && !executive_loading"
        ):
            # Status banner
            build_status_banner()

            # Session evidence summary (GAP-UI-046)
            build_session_evidence_section()

            # Metrics summary
            build_metrics_summary()

            # Report sections
            build_report_sections()

        # Empty state
        with html.Div(
            v_if="!executive_report && !executive_loading",
            classes="text-center py-8 text-grey"
        ):
            v3.VIcon("mdi-chart-box-outline", size="64", color="grey")
            html.Div(
                "Select a session and click 'Generate Report' to view executive summary",
                classes="mt-2"
            )


def build_executive_view() -> None:
    """
    Build the Executive Report view.

    This is the main entry point for the executive view module.
    Per RULE-029: Executive Reporting Pattern.
    Per GAP-UI-046: Reports are per-session with evidence summary.
    """
    with v3.VCard(
        v_if="active_view === 'executive'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "executive-report"}
    ):
        build_executive_header()
        build_executive_content()
