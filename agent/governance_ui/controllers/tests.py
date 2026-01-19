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
            add_error_trace(state, f"Load tests failed: {str(e)}", "/api/tests/results")
            state.tests_recent_runs = []
        finally:
            state.tests_loading = False

    @ctrl.trigger("load_test_results")
    def on_load_test_results():
        """Trigger to reload test results."""
        load_tests_data()

    def poll_for_results(run_id: str):
        """Background polling for test results."""
        max_polls = 30  # Max 1 minute of polling
        for _ in range(max_polls):
            time.sleep(2)
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{api_base_url}/api/tests/results/{run_id}")
                    if response.status_code == 200:
                        data = response.json()
                        state.tests_current_run = data
                        state.dirty("tests_current_run")
                        if data.get("status") != "running":
                            load_tests_data()
                            state.tests_running = False
                            state.dirty("tests_running")
                            return
            except Exception:
                pass
        state.tests_running = False
        state.dirty("tests_running")

    @ctrl.trigger("run_tests")
    def on_run_tests(category: str = None):
        """Run tests for a category."""
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
        except Exception as e:
            add_error_trace(state, f"Run tests failed: {str(e)}", "/api/tests/run")
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
            add_error_trace(state, f"View run failed: {str(e)}", f"/api/tests/results/{run_id}")

    return {
        "load_tests_data": load_tests_data,
    }
