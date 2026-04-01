"""
RED Phase: Tests for holographic test evidence wiring across all test levels.
Per BUG-014 / TEST-HOLO-01-v1.

Validates that HolographicTestStore is auto-populated during:
- pytest runs (unit + integration)
- Robot Framework runs (e2e)
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional

from tests.evidence.holographic_store import (
    HolographicTestStore,
    get_global_store,
    reset_global_store,
)


# ---------------------------------------------------------------------------
# Helpers: mock pytest objects
# ---------------------------------------------------------------------------

@dataclass
class MockReport:
    """Minimal pytest report for testing plugin hooks."""
    nodeid: str = "tests/unit/test_example.py::test_something"
    when: str = "call"
    outcome: str = "passed"
    duration: float = 0.05
    fspath: str = "tests/unit/test_example.py"
    longrepr: Optional[str] = None

    @property
    def failed(self):
        return self.outcome == "failed"

    @property
    def passed(self):
        return self.outcome == "passed"

    @property
    def skipped(self):
        return self.outcome == "skipped"


class MockConfig:
    """Minimal pytest config for testing plugin hooks."""
    def __init__(self, **options):
        self._options = {
            "--bdd-evidence": False,
            "--evidence-dir": "evidence/tests",
            "--session-id": None,
            "--session-report": False,
            "--trace-capture": False,
            "--compressed-summary": False,
        }
        self._options.update(options)
        self._ini_lines = []

    def getoption(self, name, default=None):
        return self._options.get(name, default)

    def addinivalue_line(self, name, line):
        self._ini_lines.append((name, line))


# ---------------------------------------------------------------------------
# 1. Pytest plugin wiring tests
# ---------------------------------------------------------------------------

class TestPytestPluginHolographicWiring:
    """Verify pytest plugin auto-pushes to HolographicTestStore."""

    def setup_method(self):
        """Reset global store before each test."""
        reset_global_store()

    def test_configure_initializes_holographic_store(self):
        """pytest_configure must initialize the global holographic store."""
        from tests.evidence.pytest_plugin import pytest_configure, _holographic_store

        config = MockConfig()
        pytest_configure(config)

        # The store should be initialized
        store = get_global_store()
        assert store is not None
        assert store.count == 0

    def test_logreport_pushes_to_store_on_call(self):
        """pytest_runtest_logreport must push to holographic store on 'call' phase."""
        from tests.evidence import pytest_plugin
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        config = MockConfig()
        pytest_configure(config)
        reset_global_store()  # Ensure clean store

        # Re-configure to bind store
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/unit/test_auth.py::test_login",
            when="call",
            outcome="passed",
            duration=0.123,
            fspath="tests/unit/test_auth.py",
        )
        pytest_runtest_logreport(report)

        store = get_global_store()
        assert store.count == 1

    def test_logreport_captures_unit_category(self):
        """Unit test paths produce category='unit'."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/unit/test_foo.py::test_bar",
            fspath="tests/unit/test_foo.py",
        )
        pytest_runtest_logreport(report)

        store = get_global_store()
        result = store.query(zoom=2)
        assert result["tests"][0]["category"] == "unit"

    def test_logreport_captures_e2e_category(self):
        """E2E test paths produce category='e2e'."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/e2e/test_dashboard_e2e.py::test_nav",
            fspath="tests/e2e/test_dashboard_e2e.py",
        )
        pytest_runtest_logreport(report)

        store = get_global_store()
        result = store.query(zoom=2)
        assert result["tests"][0]["category"] == "e2e"

    def test_logreport_captures_integration_category(self):
        """Integration test paths produce category='integration'."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/integration/test_typedb.py::test_query",
            fspath="tests/integration/test_typedb.py",
        )
        pytest_runtest_logreport(report)

        store = get_global_store()
        result = store.query(zoom=2)
        assert result["tests"][0]["category"] == "integration"

    def test_logreport_captures_failure_details(self):
        """Failed tests include error message in holographic store."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/unit/test_auth.py::test_bad_login",
            when="call",
            outcome="failed",
            duration=0.05,
            fspath="tests/unit/test_auth.py",
            longrepr="AssertionError: expected 200 got 401",
        )
        pytest_runtest_logreport(report)

        store = get_global_store()
        result = store.query(zoom=1)
        assert result["stats"]["failed"] == 1
        assert len(result["failures"]) == 1

    def test_logreport_captures_skipped_from_setup(self):
        """Skipped tests (setup phase) are pushed to holographic store."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/integration/test_typedb.py::test_query",
            when="setup",
            outcome="skipped",
            duration=0.0,
            fspath="tests/integration/test_typedb.py",
            longrepr="Skipped: TypeDB not available",
        )
        pytest_runtest_logreport(report)

        store = get_global_store()
        assert store.count == 1
        result = store.query(zoom=0)
        assert result["total"] == 1

    def test_all_zoom_levels_populated_after_run(self):
        """After pushing events, all zoom levels (0-3) return data."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        # Push 3 test results
        for i, status in enumerate(["passed", "passed", "failed"]):
            report = MockReport(
                nodeid=f"tests/unit/test_x.py::test_{i}",
                outcome=status,
                fspath="tests/unit/test_x.py",
                longrepr="Error" if status == "failed" else None,
            )
            pytest_runtest_logreport(report)

        store = get_global_store()
        assert store.count == 3

        # All zoom levels must return data
        z0 = store.query(zoom=0)
        assert z0["total"] == 3

        z1 = store.query(zoom=1)
        assert z1["stats"]["total"] == 3
        assert z1["stats"]["passed"] == 2
        assert z1["stats"]["failed"] == 1

        z2 = store.query(zoom=2)
        assert z2["count"] == 3

        z3 = store.query(zoom=3)
        assert z3["count"] == 3

    def test_logreport_ignores_teardown_phase(self):
        """Teardown phase should not push to holographic store."""
        from tests.evidence.pytest_plugin import pytest_configure, pytest_runtest_logreport

        reset_global_store()
        config = MockConfig()
        pytest_configure(config)

        report = MockReport(when="teardown", outcome="passed")
        pytest_runtest_logreport(report)

        store = get_global_store()
        assert store.count == 0

    def test_session_finish_reads_from_holographic_store(self):
        """pytest_sessionfinish uses holographic store for compressed output."""
        from tests.evidence.pytest_plugin import (
            pytest_configure, pytest_runtest_logreport, pytest_sessionfinish,
        )

        reset_global_store()
        config = MockConfig(**{"--compressed-summary": True})
        pytest_configure(config)

        report = MockReport(
            nodeid="tests/unit/test_a.py::test_1",
            outcome="passed",
            duration=0.1,
        )
        pytest_runtest_logreport(report)

        # sessionfinish should not crash and should read from store
        mock_session = MagicMock()
        mock_session.exitstatus = 0
        pytest_sessionfinish(mock_session, 0)

        # Store data should still be there
        store = get_global_store()
        assert store.count == 1


# ---------------------------------------------------------------------------
# 2. Robot Framework listener tests
# ---------------------------------------------------------------------------

class TestRobotHolographicListener:
    """Verify Robot Framework listener pushes to HolographicTestStore."""

    def setup_method(self):
        reset_global_store()

    def test_listener_imports(self):
        """HolographicListener can be imported from evidence module."""
        from tests.evidence.robot_listener import HolographicListener
        listener = HolographicListener()
        assert listener is not None

    def test_listener_has_api_version(self):
        """Listener declares ROBOT_LISTENER_API_VERSION = 3."""
        from tests.evidence.robot_listener import HolographicListener
        assert HolographicListener.ROBOT_LISTENER_API_VERSION == 3

    def test_end_test_pushes_pass(self):
        """end_test pushes passing test to holographic store."""
        from tests.evidence.robot_listener import HolographicListener

        listener = HolographicListener()
        data = MagicMock()
        data.name = "Verify Task Creation"
        data.full_name = "TaskCrud.Verify Task Creation"
        data.tags = ["e2e", "crud"]

        result = MagicMock()
        result.status = "PASS"
        result.message = ""
        result.elapsed_time = MagicMock(total_seconds=MagicMock(return_value=2.5))

        listener.end_test(data, result)

        store = get_global_store()
        assert store.count == 1
        z2 = store.query(zoom=2)
        assert z2["tests"][0]["status"] == "passed"
        assert z2["tests"][0]["category"] == "e2e"

    def test_end_test_pushes_fail_with_error(self):
        """end_test pushes failing test with error message."""
        from tests.evidence.robot_listener import HolographicListener

        listener = HolographicListener()
        data = MagicMock()
        data.name = "Verify Login"
        data.full_name = "Auth.Verify Login"
        data.tags = ["e2e"]

        result = MagicMock()
        result.status = "FAIL"
        result.message = "Element not found: css=button.login"
        result.elapsed_time = MagicMock(total_seconds=MagicMock(return_value=5.0))

        listener.end_test(data, result)

        store = get_global_store()
        z1 = store.query(zoom=1)
        assert z1["stats"]["failed"] == 1
        assert "Element not found" in z1["failures"][0].get("error", "")

    def test_end_test_uses_tag_for_category(self):
        """Listener extracts category from Robot tags (unit/integration/e2e)."""
        from tests.evidence.robot_listener import HolographicListener

        listener = HolographicListener()

        # Test with integration tag
        data = MagicMock()
        data.name = "TypeDB Query"
        data.full_name = "Integration.TypeDB Query"
        data.tags = ["integration", "typedb"]

        result = MagicMock()
        result.status = "PASS"
        result.message = ""
        result.elapsed_time = MagicMock(total_seconds=MagicMock(return_value=1.0))

        listener.end_test(data, result)

        store = get_global_store()
        z2 = store.query(zoom=2)
        assert z2["tests"][0]["category"] == "integration"

    def test_close_outputs_summary(self, capsys):
        """close() prints holographic summary."""
        from tests.evidence.robot_listener import HolographicListener

        listener = HolographicListener()

        # Push some test data
        store = get_global_store()
        store.push_event("robot::test_1", "test_1", "passed", category="e2e")
        store.push_event("robot::test_2", "test_2", "failed", category="e2e",
                         error_message="Timeout")

        listener.close()

        captured = capsys.readouterr()
        assert "HOLOGRAPHIC" in captured.out or "2" in captured.out

    def test_multiple_tests_accumulate(self):
        """Multiple end_test calls accumulate in the store."""
        from tests.evidence.robot_listener import HolographicListener

        listener = HolographicListener()

        for i in range(5):
            data = MagicMock()
            data.name = f"Test {i}"
            data.full_name = f"Suite.Test {i}"
            data.tags = ["e2e"]

            result = MagicMock()
            result.status = "PASS" if i < 4 else "FAIL"
            result.message = "Error" if i == 4 else ""
            result.elapsed_time = MagicMock(total_seconds=MagicMock(return_value=1.0))

            listener.end_test(data, result)

        store = get_global_store()
        assert store.count == 5
        z0 = store.query(zoom=0)
        assert z0["passed"] == 4
        assert z0["failed"] == 1


# ---------------------------------------------------------------------------
# 3. Cross-level integration tests
# ---------------------------------------------------------------------------

class TestCrossLevelHolographic:
    """Verify holographic store works across mixed test levels."""

    def setup_method(self):
        reset_global_store()

    def test_mixed_categories_queryable(self):
        """Unit + integration + e2e results coexist and filter correctly."""
        store = get_global_store()
        store.push_event("unit::t1", "t1", "passed", category="unit")
        store.push_event("int::t2", "t2", "passed", category="integration")
        store.push_event("e2e::t3", "t3", "failed", category="e2e",
                         error_message="Timeout")

        # Filter by category
        unit = store.query(zoom=0, category="unit")
        assert unit["total"] == 1

        e2e = store.query(zoom=0, category="e2e")
        assert e2e["total"] == 1
        assert e2e["failed"] == 1

        # Unfiltered shows all
        all_results = store.query(zoom=0)
        assert all_results["total"] == 3

    def test_zoom_1_default_is_llm_optimized(self):
        """Zoom 1 (default) produces compact LLM-friendly output."""
        store = get_global_store()
        for i in range(20):
            store.push_event(
                f"tests/unit/test_x.py::test_{i}", f"test_{i}",
                "passed" if i < 18 else "failed",
                category="unit",
                error_message=f"AssertionError {i}" if i >= 18 else None,
            )

        z1 = store.query(zoom=1)
        # Compact summary should have stats and failures
        assert z1["stats"]["total"] == 20
        assert z1["stats"]["passed"] == 18
        assert z1["stats"]["failed"] == 2
        assert len(z1["failures"]) == 2
        # Compression ratio should exist
        assert "compression" in z1


# ---------------------------------------------------------------------------
# 4. HTML report auto-generation wiring tests
# ---------------------------------------------------------------------------

class TestHtmlReportWiring:
    """Verify HTML report auto-generation in pytest plugin and Robot listener."""

    def setup_method(self):
        reset_global_store()

    def test_robot_listener_close_generates_html(self):
        """Robot listener close() generates HTML to output_dir."""
        from tempfile import TemporaryDirectory
        from tests.evidence.robot_listener import HolographicListener

        with TemporaryDirectory() as tmpdir:
            listener = HolographicListener(output_dir=tmpdir)

            data = MagicMock()
            data.name = "Verify Task"
            data.full_name = "Suite.Verify Task"
            data.tags = ["e2e"]
            result = MagicMock()
            result.status = "PASS"
            result.message = ""
            result.elapsed_time = MagicMock(
                total_seconds=MagicMock(return_value=1.0))

            listener.end_test(data, result)
            listener.close()

            from pathlib import Path
            html_files = list(Path(tmpdir).glob("holographic-report-*.html"))
            assert len(html_files) >= 1
            content = html_files[0].read_text()
            assert "<html" in content.lower()
            assert "Verify Task" in content

    def test_pytest_sessionfinish_generates_html(self):
        """pytest_sessionfinish generates HTML when --holographic-html set."""
        from tempfile import TemporaryDirectory
        from tests.evidence.pytest_plugin import (
            pytest_configure, pytest_runtest_logreport, pytest_sessionfinish,
        )

        with TemporaryDirectory() as tmpdir:
            config = MockConfig(**{"--holographic-html": tmpdir})
            pytest_configure(config)

            report = MockReport(
                nodeid="tests/unit/test_a.py::test_1",
                outcome="passed",
                duration=0.05,
            )
            pytest_runtest_logreport(report)

            mock_session = MagicMock()
            pytest_sessionfinish(mock_session, 0)

            from pathlib import Path
            html_files = list(Path(tmpdir).glob("holographic-report-*.html"))
            assert len(html_files) >= 1
