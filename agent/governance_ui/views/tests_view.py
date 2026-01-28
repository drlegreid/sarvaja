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


def build_categories_grid() -> None:
    """Build the test categories grid."""
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

            # Current test run
            build_current_run_panel()

            # Recent runs
            build_recent_runs_panel()
