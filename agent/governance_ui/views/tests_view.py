"""
Test Runner Dashboard View.

Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests.
Per RULE-012: Single Responsibility - only test runner UI.

Provides UI for running and viewing test results:
- Test categories (unit, governance, UI, kanren, api, e2e)
- Test run history
- Real-time test output
"""

from trame.widgets import vuetify3 as v3, html


def build_tests_header() -> None:
    """Build test runner header."""
    with v3.VCardTitle(classes="d-flex align-center"):
        v3.VIcon("mdi-test-tube", classes="mr-2")
        html.Span("Test Runner")
        v3.VSpacer()
        v3.VBtn(
            "Refresh",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            click="trigger('load_test_results')",
            loading=("tests_loading",),
            __properties=["data-testid"],
            **{"data-testid": "tests-refresh-btn"}
        )


def build_test_category_card(
    category_id: str,
    title: str,
    icon: str,
    description: str
) -> None:
    """Build a test category card with run button."""
    with v3.VCol(cols=12, md=6, lg=4):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": f"tests-card-{category_id}"}
        ):
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon(icon=icon, classes="mr-2", color="primary")
                html.Span(title)
            with v3.VCardText():
                html.Div(description, classes="text-body-2 text-grey")
            with v3.VCardActions():
                v3.VBtn(
                    "Run Tests",
                    prepend_icon="mdi-play",
                    variant="tonal",
                    color="primary",
                    size="small",
                    click=f"trigger('run_tests', '{category_id}')",
                    loading=("tests_running",),
                    __properties=["data-testid"],
                    **{"data-testid": f"tests-run-{category_id}"}
                )


def build_regression_card() -> None:
    """Build the full regression card (default run)."""
    with v3.VCol(cols=12):
        with v3.VCard(
            variant="elevated",
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "tests-card-regression"}
        ):
            with v3.VCardTitle(classes="d-flex align-center"):
                v3.VIcon(icon="mdi-shield-check", classes="mr-2")
                html.Span("Full Regression (Default)")
                v3.VSpacer()
                v3.VChip(
                    "3 Phases",
                    size="small",
                    variant="outlined",
                    color="white",
                )
            with v3.VCardText():
                html.Div(
                    "Static unit tests + Heuristic data integrity + "
                    "Dynamic Playwright UI checks (chat, all screens)",
                    classes="text-body-2"
                )
                with v3.VRow(dense=True, classes="mt-2"):
                    with v3.VCol(cols=4):
                        with html.Div(classes="d-flex align-center"):
                            v3.VIcon("mdi-code-braces", size="small", classes="mr-1")
                            html.Span("Phase 1: Static", classes="text-caption")
                    with v3.VCol(cols=4):
                        with html.Div(classes="d-flex align-center"):
                            v3.VIcon("mdi-database-check", size="small", classes="mr-1")
                            html.Span("Phase 2: Heuristic", classes="text-caption")
                    with v3.VCol(cols=4):
                        with html.Div(classes="d-flex align-center"):
                            v3.VIcon("mdi-monitor-eye", size="small", classes="mr-1")
                            html.Span("Phase 3: Playwright", classes="text-caption")
            with v3.VCardActions():
                v3.VBtn(
                    "Run Full Regression",
                    prepend_icon="mdi-play-circle",
                    variant="elevated",
                    color="white",
                    size="small",
                    click="trigger('run_regression')",
                    loading=("tests_running",),
                    __properties=["data-testid"],
                    **{"data-testid": "tests-run-regression"}
                )
                v3.VBtn(
                    "Static Only",
                    prepend_icon="mdi-play-outline",
                    variant="text",
                    color="white",
                    size="small",
                    click="trigger('run_regression_static')",
                    loading=("tests_running",),
                )


def build_regression_phases_panel() -> None:
    """Build phase breakdown for regression runs."""
    with v3.VRow(
        classes="mt-2",
        v_if="tests_current_run && tests_current_run.phases",
    ):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "regression-phases-panel"},
            ):
                v3.VCardTitle("Regression Phases")
                with v3.VCardText():
                    with v3.VTable(density="compact"):
                        with html.Thead():
                            with html.Tr():
                                html.Th("Phase")
                                html.Th("Name")
                                html.Th("Verdict")
                                html.Th("Passed")
                                html.Th("Failed")
                                html.Th("Duration")
                        with html.Tbody():
                            with html.Tr(
                                v_for="(phase, idx) in tests_current_run.phases",
                                key="idx",
                            ):
                                html.Td("{{ phase.phase }}")
                                html.Td("{{ phase.name }}")
                                html.Td(children=[
                                    v3.VChip(
                                        v_text="phase.verdict",
                                        size="x-small",
                                        color=(
                                            "phase.verdict === 'PASS' ? 'success' : "
                                            "phase.verdict === 'ERROR' ? 'warning' : 'error'"
                                        ),
                                    )
                                ])
                                html.Td("{{ phase.passed || 0 }}")
                                html.Td("{{ phase.failed || 0 }}")
                                html.Td(
                                    "{{ (phase.duration_seconds || 0).toFixed(1) }}s"
                                )


def build_categories_grid() -> None:
    """Build the test categories grid."""
    # Full regression as primary action
    with v3.VRow(classes="mb-2"):
        build_regression_card()

    # Individual category cards
    with v3.VRow():
        build_test_category_card(
            "unit", "Unit Tests", "mdi-checkbox-marked-circle",
            "Fast unit tests for individual components"
        )
        build_test_category_card(
            "governance", "Governance", "mdi-gavel",
            "TypeDB governance rules and queries"
        )
        build_test_category_card(
            "ui", "UI Tests", "mdi-monitor",
            "Dashboard UI component tests"
        )
        build_test_category_card(
            "kanren", "Kanren", "mdi-graph",
            "Constraint engine validation tests"
        )
        build_test_category_card(
            "api", "API Tests", "mdi-api",
            "REST API endpoint tests"
        )
        build_test_category_card(
            "e2e", "E2E Health", "mdi-check-decagram",
            "Platform health E2E verification"
        )


def build_current_run_panel() -> None:
    """Build current test run panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                v_if="tests_current_run",
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "tests-current-run"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    v3.VProgressCircular(
                        v_if="tests_current_run.status === 'running'",
                        indeterminate=True,
                        size=20,
                        width=2,
                        classes="mr-2"
                    )
                    v3.VIcon(
                        v_if="tests_current_run.status !== 'running'",
                        icon=(
                            "tests_current_run.status === 'completed' ? "
                            "'mdi-check-circle' : 'mdi-alert-circle'"
                        ),
                        color=(
                            "tests_current_run.status === 'completed' ? "
                            "'success' : 'error'"
                        ),
                        classes="mr-2"
                    )
                    html.Span("Test Run: {{ tests_current_run.run_id }}")
                    v3.VSpacer()
                    v3.VChip(
                        v_text="tests_current_run.status",
                        color=(
                            "tests_current_run.status === 'completed' ? 'success' : "
                            "tests_current_run.status === 'running' ? 'info' : 'error'"
                        ),
                        size="small"
                    )
                with v3.VCardText():
                    # Summary stats - Per UI-RESP-01-v1: Responsive
                    with v3.VRow(dense=True, v_if="tests_current_run.total > 0"):
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Total", classes="text-caption text-grey")
                            html.Div(
                                "{{ tests_current_run.total }}",
                                classes="text-h5 font-weight-bold"
                            )
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Passed", classes="text-caption text-success")
                            html.Div(
                                "{{ tests_current_run.passed }}",
                                classes="text-h5 font-weight-bold text-success"
                            )
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Failed", classes="text-caption text-error")
                            html.Div(
                                "{{ tests_current_run.failed }}",
                                classes="text-h5 font-weight-bold text-error"
                            )
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Duration", classes="text-caption text-grey")
                            html.Div(
                                "{{ (tests_current_run.duration_seconds || 0).toFixed(1) }}s",
                                classes="text-h5 font-weight-bold"
                            )
                    # Evidence file link (UI-AUDIT-010)
                    with v3.VAlert(
                        v_if="tests_current_run.evidence_file",
                        type="success",
                        variant="tonal",
                        density="compact",
                        classes="mt-3"
                    ):
                        with html.Div(classes="d-flex align-center"):
                            v3.VIcon("mdi-file-document-check", classes="mr-2")
                            html.Span("Evidence file generated: ")
                            html.Code(
                                "{{ tests_current_run.evidence_file.split('/').pop() }}",
                                classes="ml-1"
                            )
                    # Output
                    html.Pre(
                        v_if="tests_current_run.output",
                        v_text="tests_current_run.output",
                        classes="bg-grey-darken-4 pa-3 rounded text-caption overflow-auto",
                        style="max-height: 300px; white-space: pre-wrap;"
                    )


def build_recent_runs_panel() -> None:
    """Build recent test runs panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "tests-recent-runs"}
            ):
                v3.VCardTitle("Recent Test Runs")
                with v3.VCardText():
                    with v3.VList(
                        v_if="tests_recent_runs && tests_recent_runs.length > 0",
                        dense=True
                    ):
                        with v3.VListItem(
                            v_for="run in tests_recent_runs",
                            key="run.run_id",
                            click="trigger('view_test_run', run.run_id)"
                        ):
                            with html.Template(v_slot_prepend=True):
                                v3.VIcon(
                                    icon=(
                                        "run.status === 'completed' ? "
                                        "'mdi-check-circle' : 'mdi-alert-circle'"
                                    ),
                                    color=(
                                        "run.status === 'completed' ? 'success' : 'error'"
                                    ),
                                    size="small"
                                )
                            v3.VListItemTitle("{{ run.run_id }}")
                            v3.VListItemSubtitle(
                                "{{ run.passed || 0 }} passed, "
                                "{{ run.failed || 0 }} failed"
                            )
                            with html.Template(v_slot_append=True):
                                v3.VChip(
                                    v_text="run.status",
                                    size="x-small",
                                    color=(
                                        "run.status === 'completed' ? 'success' : 'error'"
                                    )
                                )
                    v3.VAlert(
                        v_if="!tests_recent_runs || tests_recent_runs.length === 0",
                        text="No test runs yet. Select a category above to run tests.",
                        type="info",
                        variant="tonal",
                        density="compact"
                    )


def build_robot_reports_panel() -> None:
    """Build Robot Framework reports panel."""
    with v3.VRow(classes="mt-4"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "robot-reports-panel"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    v3.VIcon("mdi-robot", classes="mr-2", color="primary")
                    html.Span("Robot Framework Reports")
                    v3.VSpacer()
                    v3.VBtn(
                        "Load Summary",
                        prepend_icon="mdi-refresh",
                        variant="outlined",
                        size="small",
                        click="trigger('load_robot_summary')",
                        __properties=["data-testid"],
                        **{"data-testid": "robot-refresh-btn"}
                    )
                with v3.VCardText():
                    # Summary stats
                    with v3.VRow(
                        dense=True,
                        v_if="robot_summary && robot_summary.available"
                    ):
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Total", classes="text-caption text-grey")
                            html.Div(
                                "{{ robot_summary.total }}",
                                classes="text-h5 font-weight-bold"
                            )
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Passed", classes="text-caption text-success")
                            html.Div(
                                "{{ robot_summary.passed }}",
                                classes="text-h5 font-weight-bold text-success"
                            )
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Failed", classes="text-caption text-error")
                            html.Div(
                                "{{ robot_summary.failed }}",
                                classes="text-h5 font-weight-bold text-error"
                            )
                        with v3.VCol(cols=6, sm=3):
                            html.Div("Generated", classes="text-caption text-grey")
                            html.Div(
                                "{{ (robot_summary.generated || '').substring(0, 19) }}",
                                classes="text-body-2 font-weight-medium"
                            )
                    # Report links
                    with html.Div(
                        v_if="robot_summary && robot_summary.available",
                        classes="mt-3 d-flex ga-2"
                    ):
                        v3.VBtn(
                            "View Report",
                            v_if="robot_summary.report_exists",
                            prepend_icon="mdi-file-chart",
                            variant="tonal",
                            color="primary",
                            href="/api/tests/robot/report?file=report.html",
                            target="_blank",
                            __properties=["data-testid"],
                            **{"data-testid": "robot-view-report"}
                        )
                        v3.VBtn(
                            "View Log",
                            v_if="robot_summary.log_exists",
                            prepend_icon="mdi-file-document",
                            variant="tonal",
                            color="secondary",
                            href="/api/tests/robot/report?file=log.html",
                            target="_blank",
                            __properties=["data-testid"],
                            **{"data-testid": "robot-view-log"}
                        )
                    # Not available
                    v3.VAlert(
                        v_if="robot_summary && !robot_summary.available",
                        type="info",
                        variant="tonal",
                        density="compact",
                        text=("robot_summary.message || 'No Robot Framework reports found.'",)
                    )
                    v3.VAlert(
                        v_if="!robot_summary",
                        type="info",
                        variant="tonal",
                        density="compact",
                        text="Click 'Load Summary' to check for Robot Framework reports."
                    )


def build_tests_view() -> None:
    """
    Build the Test Runner Dashboard view.

    Main entry point for the tests view module.
    Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests.
    """
    with v3.VCard(
        v_if="active_view === 'tests'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "tests-dashboard"}
    ):
        build_tests_header()

        with v3.VCardText():
            # Test categories grid
            build_categories_grid()

            # Robot Framework reports
            build_robot_reports_panel()

            # Current test run
            build_current_run_panel()

            # Regression phases breakdown
            build_regression_phases_panel()

            # Recent runs
            build_recent_runs_panel()
