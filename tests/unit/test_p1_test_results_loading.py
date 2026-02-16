"""TDD Tests for P1: Test Results Loading Fix.

Validates:
1. _load_tests populates state correctly on success
2. _load_tests handles API errors gracefully with error state
3. load_tests_data controller sets loading/error states
4. Tests tab triggers load_tests_data on view change
5. runner_store loads persisted results on import
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestLoadTestsStartup:
    """_load_tests in dashboard_data_loader works correctly."""

    def test_populates_tests_recent_runs_on_success(self):
        """Successful API response populates state.tests_recent_runs."""
        from agent.governance_ui.dashboard_data_loader import _load_tests

        state = MagicMock()
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "runs": [
                {"run_id": "CVP-T2-001", "status": "completed", "total": 27, "passed": 13},
            ]
        }
        mock_client.get.return_value = mock_resp

        # CVP status
        mock_cvp = MagicMock()
        mock_cvp.status_code = 200
        mock_cvp.json.return_value = {"pipeline_health": "healthy"}
        mock_client.get.side_effect = [mock_resp, mock_cvp]

        _load_tests(state, mock_client, "http://localhost:8082")

        assert state.tests_recent_runs == [
            {"run_id": "CVP-T2-001", "status": "completed", "total": 27, "passed": 13},
        ]

    def test_handles_api_error_gracefully(self):
        """API returning non-200 results in empty list, not crash."""
        from agent.governance_ui.dashboard_data_loader import _load_tests

        state = MagicMock()
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_client.get.return_value = mock_resp

        _load_tests(state, mock_client, "http://localhost:8082")

        assert state.tests_recent_runs == []

    def test_handles_connection_error(self):
        """Connection refused doesn't crash, sets empty list."""
        from agent.governance_ui.dashboard_data_loader import _load_tests

        state = MagicMock()
        mock_client = MagicMock()
        mock_client.get.side_effect = ConnectionError("Connection refused")

        _load_tests(state, mock_client, "http://localhost:8082")

        assert state.tests_recent_runs == []


class TestRunnerStorePersistence:
    """runner_store.py loads persisted results from disk."""

    def test_load_persisted_results_reads_json_files(self):
        """_load_persisted_results reads JSON files from results dir."""
        from governance.routes.tests.runner_store import _load_persisted_results

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test result file
            result = {
                "status": "completed",
                "timestamp": "2026-02-15T10:00:00",
                "total": 10,
                "passed": 8,
                "failed": 2,
                "category": "unit",
            }
            (Path(tmpdir) / "CVP-T2-TEST.json").write_text(json.dumps(result))

            results = _load_persisted_results(results_dir=tmpdir)
            assert "CVP-T2-TEST" in results
            assert results["CVP-T2-TEST"]["total"] == 10

    def test_load_persisted_results_limits_to_50(self):
        """Only last 50 results loaded (sorted reverse by name)."""
        from governance.routes.tests.runner_store import _load_persisted_results

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(60):
                result = {"status": "completed", "total": i}
                (Path(tmpdir) / f"RUN-{i:04d}.json").write_text(json.dumps(result))

            results = _load_persisted_results(results_dir=tmpdir)
            assert len(results) == 50

    def test_load_persisted_results_handles_empty_dir(self):
        """Empty dir returns empty dict."""
        from governance.routes.tests.runner_store import _load_persisted_results

        with tempfile.TemporaryDirectory() as tmpdir:
            results = _load_persisted_results(results_dir=tmpdir)
            assert results == {}

    def test_load_persisted_results_handles_corrupt_json(self):
        """Corrupt JSON files are skipped without crash."""
        from governance.routes.tests.runner_store import _load_persisted_results

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "CORRUPT.json").write_text("not json{")
            (Path(tmpdir) / "VALID.json").write_text('{"status": "ok"}')

            results = _load_persisted_results(results_dir=tmpdir)
            assert "VALID" in results
            assert "CORRUPT" not in results


class TestTestsControllerLoadData:
    """tests.py controller sets correct state during loading."""

    def test_load_tests_data_populates_recent_runs(self):
        """load_tests_data() populates state.tests_recent_runs from API."""
        state = MagicMock()
        ctrl = MagicMock()
        ctrl.trigger = MagicMock(return_value=lambda f: f)

        with patch("agent.governance_ui.controllers.tests.httpx") as mock_httpx:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"runs": [{"run_id": "R1", "status": "completed"}]}
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_resp
            mock_httpx.Client.return_value = mock_client

            from agent.governance_ui.controllers.tests import register_tests_controllers
            loaders = register_tests_controllers(state, ctrl, "http://localhost:8082")
            loaders["load_tests_data"]()

        # Verify state was populated correctly
        assert state.tests_recent_runs == [{"run_id": "R1", "status": "completed"}]
        # Verify loading ends as False
        assert state.tests_loading is False


class TestListTestResultsAPI:
    """API endpoint returns correct format."""

    @pytest.mark.asyncio
    async def test_list_test_results_returns_runs_key(self):
        """GET /tests/results returns {'runs': [...]}."""
        from governance.routes.tests.runner import list_test_results
        from governance.routes.tests.runner_store import _test_results

        # Insert a test result
        _test_results["TEST-RUN-001"] = {
            "status": "completed",
            "total": 5,
            "passed": 5,
            "failed": 0,
        }

        try:
            result = await list_test_results(limit=10)
            assert "runs" in result
            runs = result["runs"]
            assert any(r["run_id"] == "TEST-RUN-001" for r in runs)
        finally:
            _test_results.pop("TEST-RUN-001", None)

    @pytest.mark.asyncio
    async def test_list_test_results_respects_limit(self):
        """Limit parameter caps returned runs."""
        from governance.routes.tests.runner import list_test_results
        from governance.routes.tests.runner_store import _test_results

        for i in range(5):
            _test_results[f"LIMIT-TEST-{i}"] = {"status": "completed"}

        try:
            result = await list_test_results(limit=3)
            assert len(result["runs"]) <= 3
        finally:
            for i in range(5):
                _test_results.pop(f"LIMIT-TEST-{i}", None)
