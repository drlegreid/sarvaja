"""
Test Runner Dashboard View.

Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests.
Per RULE-012: Single Responsibility - only test runner UI.
Per DOC-SIZE-01-v1: Result panels in tests_view_panels.py.

Provides UI for running and viewing test results:
- Test categories (unit, governance, UI, kanren, api, e2e)
- Test run history
- Real-time test output
"""

from trame.widgets import vuetify3 as v3, html

from .tests_view_panels import (  # noqa: F401 — re-export
    build_current_run_panel,
    build_recent_runs_panel,
    build_robot_reports_panel,
)


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
            **{"data-testid": "tests-refresh-btn"},
        )


def build_test_category_card(
    category_id: str,
    title: str,
    icon: str,
    description: str,
) -> None:
    """Build a test category card with run button."""
    with v3.VCol(cols=12, md=6, lg=4):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": f"tests-card-{category_id}"},
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
                    **{"data-testid": f"tests-run-{category_id}"},
                )


def build_regression_card() -> None:
    """Build the full regression card (default run)."""
    with v3.VCol(cols=12):
        with v3.VCard(
            variant="elevated",
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "tests-card-regression"},
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
                    classes="text-body-2",
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
                    **{"data-testid": "tests-run-regression"},
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
    with v3.VRow(classes="mb-2"):
        build_regression_card()

    with v3.VRow():
        build_test_category_card(
            "unit", "Unit Tests", "mdi-checkbox-marked-circle",
            "Fast unit tests for individual components",
        )
        build_test_category_card(
            "governance", "Governance", "mdi-gavel",
            "TypeDB governance rules and queries",
        )
        build_test_category_card(
            "ui", "UI Tests", "mdi-monitor",
            "Dashboard UI component tests",
        )
        build_test_category_card(
            "kanren", "Kanren", "mdi-graph",
            "Constraint engine validation tests",
        )
        build_test_category_card(
            "api", "API Tests", "mdi-api",
            "REST API endpoint tests",
        )
        build_test_category_card(
            "e2e", "E2E Health", "mdi-check-decagram",
            "Platform health E2E verification",
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
        **{"data-testid": "tests-dashboard"},
    ):
        build_tests_header()

        with v3.VCardText():
            build_categories_grid()
            build_robot_reports_panel()
            build_current_run_panel()
            build_regression_phases_panel()
            build_recent_runs_panel()
