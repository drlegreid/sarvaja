"""
Unit tests for SFDC Fallback Workflow Runner.

Per DOC-SIZE-01-v1: Tests for extracted graph_fallback.py.
Tests: run_fallback_workflow with various state transitions.
"""

import pytest
from unittest.mock import MagicMock

from governance.sfdc.langgraph.graph_fallback import run_fallback_workflow


def _make_graph(nodes):
    """Create a mock graph with named nodes."""
    g = MagicMock()
    g.nodes = nodes
    return g


class TestRunFallbackWorkflow:
    """Tests for run_fallback_workflow()."""

    def test_empty_graph(self):
        g = _make_graph({})
        result = run_fallback_workflow(g, {})
        assert isinstance(result, dict)

    def test_linear_sequence(self):
        executed = []

        def make_node(name):
            def fn(state):
                executed.append(name)
                return {}
            return fn

        g = _make_graph({
            "start": make_node("start"),
            "complete": make_node("complete"),
        })
        result = run_fallback_workflow(g, {})
        assert "start" in executed
        assert "complete" in executed

    def test_failed_status_triggers_abort(self):
        executed = []

        def start_fail(state):
            executed.append("start")
            return {"status": "failed"}

        def abort_fn(state):
            executed.append("abort")
            return {}

        def complete_fn(state):
            executed.append("complete")
            return {}

        g = _make_graph({
            "start": start_fail,
            "abort": abort_fn,
            "complete": complete_fn,
        })
        result = run_fallback_workflow(g, {})
        assert "abort" in executed
        assert result.get("status") == "failed"

    def test_skip_monitor(self):
        executed = []

        def make_node(name):
            def fn(state):
                executed.append(name)
                return {}
            return fn

        g = _make_graph({
            "start": make_node("start"),
            "monitor": make_node("monitor"),
            "complete": make_node("complete"),
        })
        result = run_fallback_workflow(g, {"should_skip_monitor": True})
        assert "monitor" not in executed

    def test_breaking_changes_skip_to_report(self):
        executed = []

        def make_node(name):
            def fn(state):
                executed.append(name)
                return {}
            return fn

        g = _make_graph({
            "start": make_node("start"),
            "discover": make_node("discover"),
            "develop": make_node("develop"),
            "skip_to_report": make_node("skip_to_report"),
            "report": make_node("report"),
            "complete": make_node("complete"),
        })
        result = run_fallback_workflow(g, {"has_breaking_changes": True})
        assert "skip_to_report" in executed
        assert "develop" not in executed

    def test_node_exception_sets_failed(self):
        def bad_node(state):
            raise RuntimeError("boom")

        g = _make_graph({"start": bad_node})
        result = run_fallback_workflow(g, {})
        assert result["status"] == "failed"
        assert "boom" in result["error_message"]

    def test_deployment_failure_triggers_rollback(self):
        executed = []

        def deploy_fail(state):
            executed.append("deploy")
            return {"deployment_status": "Failed"}

        def rollback(state):
            executed.append("rollback")
            return {}

        def report(state):
            executed.append("report")
            return {}

        g = _make_graph({
            "start": lambda s: (executed.append("start"), {})[1],
            "deploy": deploy_fail,
            "rollback": rollback,
            "report": report,
            "complete": lambda s: (executed.append("complete"), {})[1],
        })
        result = run_fallback_workflow(g, {})
        assert "rollback" in executed
        assert "report" in executed

    def test_validation_failure_triggers_rollback(self):
        executed = []

        g = _make_graph({
            "start": lambda s: (executed.append("start"), {})[1],
            "validate": lambda s: (executed.append("validate"), {"validation_passed": False})[1],
            "rollback": lambda s: (executed.append("rollback"), {})[1],
            "report": lambda s: (executed.append("report"), {})[1],
            "complete": lambda s: (executed.append("complete"), {})[1],
        })
        result = run_fallback_workflow(g, {})
        assert "rollback" in executed

    def test_test_failure_retries(self):
        call_count = [0]

        def test_node(state):
            call_count[0] += 1
            if call_count[0] < 3:
                return {"coverage_met": False}
            return {"coverage_met": True}

        g = _make_graph({
            "start": lambda s: {},
            "develop": lambda s: {},
            "test": test_node,
            "complete": lambda s: {},
        })
        result = run_fallback_workflow(g, {})
        assert call_count[0] == 3

    def test_does_not_modify_original_state(self):
        g = _make_graph({
            "start": lambda s: {"new_key": "new_value"},
        })
        original = {"key": "value"}
        result = run_fallback_workflow(g, original)
        assert "new_key" not in original
