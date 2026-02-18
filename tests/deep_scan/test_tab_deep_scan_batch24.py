"""
Unit tests for Tab Deep Scan Batch 24 — Silent JSON parse + infra error handling.

Covers: BUG-UI-SILENT-JSON-001 (JSON parse error traces in metrics/data_loaders/infra).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── BUG-UI-SILENT-JSON-001: metrics.py JSON parse traces ───────────────


class TestMetricsJsonParseTraces:
    """All 3 metrics functions must trace JSON parse failures."""

    def test_load_metrics_data_traces_json_error(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        # Find the load_metrics_data function
        start = source.index("def load_metrics_data(")
        end = source.index("\n    @ctrl.trigger", start + 1)
        fn_src = source[start:end]
        assert "add_error_trace" in fn_src
        assert "Metrics JSON parse failed" in fn_src

    def test_search_metrics_traces_json_error(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        start = source.index("def search_metrics(")
        end = source.index("\n    @ctrl.trigger", start + 1)
        fn_src = source[start:end]
        assert "add_error_trace" in fn_src
        assert "Search metrics JSON parse failed" in fn_src

    def test_load_metrics_timeline_traces_json_error(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        start = source.index("def load_metrics_timeline(")
        end = source.index("\n    return", start + 1)
        fn_src = source[start:end]
        assert "add_error_trace" in fn_src
        assert "Timeline JSON parse failed" in fn_src

    def test_no_bare_except_pass_in_json_blocks(self):
        """No except Exception: pass in JSON parse blocks."""
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        # Find all response.json() blocks and ensure none have bare pass
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if "response_body = response.json()" in line:
                # Look at the except block within next 5 lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "except Exception" in lines[j]:
                        # Next line should NOT be bare pass
                        if j + 1 < len(lines):
                            assert lines[j + 1].strip() != "pass", \
                                f"Line {j+2}: bare pass after JSON parse except"

    def test_load_metrics_data_null_guard_on_200(self):
        """metrics_data should NOT be set to None/null on JSON parse failure."""
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        start = source.index("def load_metrics_data(")
        end = source.index("\n    @ctrl.trigger", start + 1)
        fn_src = source[start:end]
        # Must check response_body is not None before using
        assert "response_body is not None" in fn_src


# ── BUG-UI-SILENT-JSON-001: data_loaders.py JSON parse traces ──────────


class TestDataLoadersJsonParseTraces:
    """load_trust_data must trace JSON parse failures."""

    def test_load_trust_data_traces_json_error(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_trust_data(")
        end = source.index("\n    def load_monitor_data", start + 1)
        fn_src = source[start:end]
        assert "add_error_trace" in fn_src
        assert "Agents JSON parse failed" in fn_src

    def test_no_bare_except_pass_in_trust_json(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_trust_data(")
        end = source.index("\n    def load_monitor_data", start + 1)
        fn_src = source[start:end]
        lines = fn_src.splitlines()
        for i, line in enumerate(lines):
            if "response_body = response.json()" in line:
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "except Exception" in lines[j]:
                        if j + 1 < len(lines):
                            assert lines[j + 1].strip() != "pass"

    def test_null_guard_on_agents_response(self):
        """response_body must be checked for None before use."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_trust_data(")
        end = source.index("\n    def load_monitor_data", start + 1)
        fn_src = source[start:end]
        assert "response_body is not None" in fn_src


# ── BUG-UI-SILENT-JSON-001: infra_loaders.py healthcheck trace ─────────


class TestInfraLoadersHealthcheckTrace:
    """Healthcheck state file parse failure must be traced."""

    def test_healthcheck_parse_traces_error(self):
        from agent.governance_ui.controllers import infra_loaders
        source = inspect.getsource(infra_loaders)
        assert "Healthcheck state parse failed" in source

    def test_imports_add_error_trace(self):
        from agent.governance_ui.controllers import infra_loaders
        source = inspect.getsource(infra_loaders)
        assert "from agent.governance_ui.trace_bar.transforms import add_error_trace" in source

    def test_no_bare_except_pass_for_healthcheck(self):
        """The healthcheck state file block should not have bare pass."""
        from agent.governance_ui.controllers import infra_loaders
        source = inspect.getsource(infra_loaders)
        start = source.index("# Load stats from healthcheck state")
        end = source.index("# Get memory usage", start + 1)
        block = source[start:end]
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if "except Exception" in line:
                if i + 1 < len(lines):
                    assert lines[i + 1].strip() != "pass", \
                        "Healthcheck except block should not be bare pass"


# ── Metrics behavioral tests ──────────────────────────────────────────


class TestMetricsBehavior:
    """Verify metrics controllers handle JSON failures gracefully."""

    def _make_state(self, **attrs):
        s = MagicMock()
        for k, v in attrs.items():
            setattr(s, k, v)
        return s

    def _make_ctrl(self):
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = trigger_decorator
        ctrl._triggers = triggers
        return ctrl

    @patch("agent.governance_ui.controllers.metrics.add_error_trace")
    @patch("agent.governance_ui.controllers.metrics.add_api_trace")
    @patch("httpx.Client")
    def test_load_metrics_json_failure_sets_error(self, MockClient, mock_api_trace, mock_err_trace):
        """When JSON parse fails on 200, metrics_data is None and error traced."""
        mc = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("Invalid JSON")
        mc.get.return_value = resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state = self._make_state(metrics_days_filter=5)
        ctrl = self._make_ctrl()
        from agent.governance_ui.controllers.metrics import register_metrics_controllers
        register_metrics_controllers(state, ctrl, "http://localhost:8082")

        result = ctrl._triggers["load_metrics_data"]
        result()

        # Should have called add_error_trace for JSON parse failure
        mock_err_trace.assert_called()
        assert state.metrics_data is None
        assert state.metrics_loading is False

    @patch("agent.governance_ui.controllers.metrics.add_error_trace")
    @patch("agent.governance_ui.controllers.metrics.add_api_trace")
    @patch("httpx.Client")
    def test_search_metrics_json_failure_returns_empty(self, MockClient, mock_api_trace, mock_err_trace):
        """When JSON parse fails on search, results are empty and error traced."""
        mc = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("Invalid JSON")
        mc.get.return_value = resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state = self._make_state(metrics_search_query="test")
        ctrl = self._make_ctrl()
        from agent.governance_ui.controllers.metrics import register_metrics_controllers
        register_metrics_controllers(state, ctrl, "http://localhost:8082")

        ctrl._triggers["search_metrics"]()

        mock_err_trace.assert_called()
        assert state.metrics_search_results == []
        assert state.metrics_search_total == 0
        assert state.metrics_search_loading is False


# ── Cross-file consistency checks ─────────────────────────────────────


class TestJsonParseConsistency:
    """All files using response.json() in try/except must trace errors."""

    def test_metrics_has_bugfix_marker(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        assert source.count("BUG-UI-SILENT-JSON-001") >= 3

    def test_data_loaders_has_bugfix_marker(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        assert "BUG-UI-SILENT-JSON-001" in source

    def test_infra_loaders_has_bugfix_marker(self):
        from agent.governance_ui.controllers import infra_loaders
        source = inspect.getsource(infra_loaders)
        assert "BUG-UI-SILENT-JSON-001" in source
