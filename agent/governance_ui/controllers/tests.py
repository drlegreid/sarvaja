"""
Test Runner Controllers (WORKFLOW-SHELL-01-v1)
===============================================
Controller functions for running and viewing tests.

Per RULE-012: DSP Semantic Code Structure
Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests

Created: 2026-01-17
"""

import time
import httpx
import threading
from typing import Any

from agent.governance_ui.trace_bar.transforms import (
    add_api_trace,
    add_error_trace,
)


def register_tests_controllers(
    state: Any,
    ctrl: Any,
    api_base_url: str
) -> dict:
    """
    Register test runner controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls

    Returns:
        Dict with load_tests_data function for view change handler
    """

    def load_tests_data():
        """Load recent test runs from REST API."""
        state.tests_loading = True
        try:
            with httpx.Client(timeout=10.0) as client:
                start = time.time()
                response = client.get(f"{api_base_url}/api/tests/results?limit=10")
                duration_ms = int((time.time() - start) * 1000)

                # Capture response body for trace
                response_body = None
                try:
                    response_body = response.json()
                except Exception:
                    pass

                add_api_trace(
                    state, "/api/tests/results", "GET", response.status_code, duration_ms,
                    response_body=response_body
                )
                if response.status_code == 200:
                    data = response_body or {}
                    state.tests_recent_runs = data.get("runs", [])
                else:
                    state.tests_recent_runs = []
        except Exception as e:
            # BUG-453-TST-001: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Load tests failed: {type(e).__name__}", "/api/tests/results")
            state.tests_recent_runs = []
        finally:
            state.tests_loading = False

    @ctrl.trigger("load_test_results")
    def on_load_test_results():
        """Trigger to reload test results."""
        load_tests_data()

    def poll_for_results(run_id: str):
        """Background polling for test results."""
        max_polls = 150  # Up to 5 minutes to match runner timeout (300s)
        consecutive_errors = 0
        for _ in range(max_polls):
            time.sleep(2)
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{api_base_url}/api/tests/results/{run_id}")
                    if response.status_code == 200:
                        data = response.json()
                        state.tests_current_run = data
                        state.dirty("tests_current_run")
                        consecutive_errors = 0
                        if data.get("status") != "running":
                            load_tests_data()
                            state.tests_running = False
                            state.dirty("tests_running")
                            return
            except Exception as e:
                # BUG-UI-TESTS-POLL-001: Log errors, stop after 5 consecutive
                consecutive_errors += 1
                if consecutive_errors >= 5:
                    # BUG-453-TST-002: Don't leak exception internals via add_error_trace → Trame WebSocket
                    add_error_trace(state, f"Poll stopped after 5 errors: {type(e).__name__}", f"/api/tests/results/{run_id}")
                    break
        state.tests_running = False
        state.dirty("tests_running")

    @ctrl.trigger("run_tests")
    def on_run_tests(category: str = None):
        """Run tests for a category."""
        # BUG-239-TESTS-002: Guard against double-submit while tests running
        if state.tests_running:
            return
        state.tests_running = True
        try:
            with httpx.Client(timeout=30.0) as client:
                start = time.time()
                url = f"{api_base_url}/api/tests/run"
                endpoint = "/api/tests/run"
                if category:
                    url += f"?category={category}"
                    endpoint += f"?category={category}"
                response = client.post(url)
                duration_ms = int((time.time() - start) * 1000)

                # Capture response body for trace
                response_body = None
                try:
                    response_body = response.json()
                except Exception:
                    pass

                add_api_trace(
                    state, endpoint, "POST", response.status_code, duration_ms,
                    request_body={"category": category} if category else None,
                    response_body=response_body
                )

                if response.status_code == 200:
                    data = response_body or {}
                    run_id = data.get("run_id")
                    # BUG-187-003: Guard against None run_id before spawning poll thread
                    if not run_id:
                        state.tests_running = False
                        state.has_error = True
                        state.error_message = "Test run started but no run_id returned"
                        return
                    state.tests_current_run = {
                        "run_id": run_id,
                        "status": "running",
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                    }
                    # Start background polling
                    thread = threading.Thread(
                        target=poll_for_results,
                        args=(run_id,),
                        daemon=True
                    )
                    thread.start()
                else:
                    # BUG-UI-TESTS-001: No thread started — reset spinner
                    state.tests_running = False
        except Exception as e:
            # BUG-453-TST-003: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"Run tests failed: {type(e).__name__}", "/api/tests/run")
            state.tests_running = False

    @ctrl.trigger("view_test_run")
    def on_view_test_run(run_id: str):
        """View a specific test run."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tests/results/{run_id}")
                if response.status_code == 200:
                    state.tests_current_run = response.json()
        except Exception as e:
            # BUG-453-TST-004: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(state, f"View run failed: {type(e).__name__}", f"/api/tests/results/{run_id}")

    def _start_regression(skip_dynamic: bool = False):
        """Shared regression launcher."""
        state.tests_running = True
        try:
            with httpx.Client(timeout=30.0) as client:
                start = time.time()
                url = f"{api_base_url}/api/tests/regression/run"
                if skip_dynamic:
                    url += "?skip_dynamic=true"
                response = client.post(url)
                duration_ms = int((time.time() - start) * 1000)

                response_body = None
                try:
                    response_body = response.json()
                except Exception:
                    pass

                add_api_trace(
                    state, "/api/tests/regression/run", "POST",
                    response.status_code, duration_ms,
                    response_body=response_body,
                )

                if response.status_code == 200:
                    data = response_body or {}
                    run_id = data.get("run_id")
                    # BUG-222-REGR-001: Guard against None run_id before polling
                    if not run_id:
                        state.tests_running = False
                        state.has_error = True
                        state.error_message = "Regression started but no run_id returned"
                        return
                    state.tests_current_run = {
                        "run_id": run_id,
                        "status": "running",
                        "category": "regression",
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                    }
                    # Poll with longer timeout for regression
                    thread = threading.Thread(
                        target=poll_for_regression,
                        args=(run_id,),
                        daemon=True,
                    )
                    thread.start()
                else:
                    # BUG-UI-TESTS-001: No thread started — reset spinner
                    state.tests_running = False
        except Exception as e:
            # BUG-453-TST-005: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(
                state, f"Regression failed: {type(e).__name__}",
                "/api/tests/regression/run",
            )
            state.tests_running = False

    def poll_for_regression(run_id: str):
        """Background polling for regression results (longer timeout)."""
        max_polls = 90  # Up to 3 minutes
        consecutive_errors = 0
        for _ in range(max_polls):
            time.sleep(2)
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        f"{api_base_url}/api/tests/results/{run_id}"
                    )
                    if response.status_code == 200:
                        data = response.json()
                        state.tests_current_run = data
                        state.dirty("tests_current_run")
                        consecutive_errors = 0
                        if data.get("status") != "running":
                            load_tests_data()
                            state.tests_running = False
                            state.dirty("tests_running")
                            return
            except Exception as e:
                # BUG-UI-TESTS-POLL-001: Log errors, stop after 5 consecutive
                consecutive_errors += 1
                if consecutive_errors >= 5:
                    # BUG-453-TST-006: Don't leak exception internals via add_error_trace → Trame WebSocket
                    add_error_trace(state, f"Regression poll stopped: {type(e).__name__}", f"/api/tests/results/{run_id}")
                    break
        state.tests_running = False
        state.dirty("tests_running")

    @ctrl.trigger("run_regression")
    def on_run_regression():
        """Run full regression (static + heuristic + dynamic)."""
        _start_regression(skip_dynamic=False)

    @ctrl.trigger("run_regression_static")
    def on_run_regression_static():
        """Run regression with only static + heuristic (skip Playwright)."""
        _start_regression(skip_dynamic=True)

    @ctrl.trigger("load_robot_summary")
    def on_load_robot_summary():
        """Load Robot Framework report summary."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{api_base_url}/api/tests/robot/summary")
                if response.status_code == 200:
                    state.robot_summary = response.json()
        except Exception as e:
            # BUG-453-TST-007: Don't leak exception internals via add_error_trace → Trame WebSocket
            add_error_trace(
                state, f"Load robot summary failed: {type(e).__name__}",
                "/api/tests/robot/summary",
            )
            # BUG-453-TST-008: Don't leak exception message via Trame state to browser
            state.robot_summary = {"available": False, "message": type(e).__name__}

    return {
        "load_tests_data": load_tests_data,
    }
