"""
Pytest Configuration for Audit Trail Integration

Provides Given/When/Then structured audit trails for all test execution.
Per EPIC-006: Test certification with audit trails.

Usage:
    pytest tests/ -v                     # Normal output
    pytest tests/ --audit-only           # Dots + summary only
    pytest tests/ --no-audit             # Disable audit trails
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import pytest

# Add tests directory to path for imports
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

from audit import AuditTrailWriter, TestAuditRecord, get_audit_writer, reset_audit_writer


# Global audit writer instance
_writer: Optional[AuditTrailWriter] = None
_test_records: Dict[str, TestAuditRecord] = {}
_test_start_times: Dict[str, float] = {}


def pytest_addoption(parser):
    """Add audit-related command line options."""
    parser.addoption(
        "--audit-only",
        action="store_true",
        default=False,
        help="Show only dots and summary (quiet mode with audit)"
    )
    parser.addoption(
        "--no-audit",
        action="store_true",
        default=False,
        help="Disable audit trail generation"
    )


def pytest_configure(config):
    """Initialize audit writer at start of test session."""
    global _writer

    if config.getoption("--no-audit", default=False):
        _writer = None
        return

    reset_audit_writer()
    _writer = get_audit_writer()

    # Configure quiet mode if audit-only
    if config.getoption("--audit-only", default=False):
        config.option.verbose = 0
        config.option.tbstyle = "no"


def pytest_collection_modifyitems(session, config, items):
    """Record collected tests in audit trail."""
    if _writer is None:
        return

    # Add marker info to test records
    for item in items:
        # Determine category from markers
        category = "unit"  # default
        for marker in item.iter_markers():
            if marker.name == "integration":
                category = "integration"
                break
            elif marker.name == "e2e":
                category = "e2e"
                break


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Create audit record before test runs (GIVEN phase)."""
    global _test_records, _test_start_times

    if _writer is None:
        return

    # Generate test ID
    test_id = item.nodeid

    # Determine category from markers or path
    category = "unit"
    for marker in item.iter_markers():
        if marker.name == "integration":
            category = "integration"
            break
        elif marker.name == "e2e":
            category = "e2e"
            break

    # Check path for level hints
    if "level2" in str(item.fspath) or "integration" in str(item.fspath):
        category = "integration"
    elif "level3" in str(item.fspath) or "e2e" in str(item.fspath):
        category = "e2e"

    # Extract business intent from docstring
    business_intent = "Test execution"
    if item.function.__doc__:
        # First line of docstring is business intent
        business_intent = item.function.__doc__.strip().split('\n')[0]

    # Create audit record
    record = _writer.create_record(
        test_id=test_id,
        test_name=item.name,
        module=str(item.fspath.basename) if hasattr(item.fspath, 'basename') else str(item.fspath),
        category=category,
        business_intent=business_intent
    )

    # Add GIVEN steps based on fixtures
    if hasattr(item, 'fixturenames') and item.fixturenames:
        for fixture in item.fixturenames:
            if fixture not in ('request', 'tmp_path', 'capsys', 'monkeypatch'):
                record.add_given(f"Fixture '{fixture}' is available")

    # Add marker info as GIVEN
    for marker in item.iter_markers():
        if marker.name not in ('parametrize', 'usefixtures'):
            record.add_given(f"Test marked as '{marker.name}'", marker=marker.name)

    # Store record and start time
    _test_records[test_id] = record
    _test_start_times[test_id] = time.time()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item):
    """Record WHEN phase - test is executing."""
    if _writer is None:
        return

    test_id = item.nodeid
    record = _test_records.get(test_id)

    if record:
        record.add_when(
            f"Execute test '{item.name}'",
            function=item.name,
            module=str(item.fspath)
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Record THEN phase - test result."""
    outcome = yield
    report = outcome.get_result()

    if _writer is None:
        return

    test_id = item.nodeid
    record = _test_records.get(test_id)

    if record is None:
        return

    # Only process the call phase (actual test execution)
    if report.when == "call":
        start_time = _test_start_times.get(test_id, time.time())
        duration_ms = (time.time() - start_time) * 1000

        if report.passed:
            record.add_then(
                "Test passed successfully",
                outcome="passed",
                duration_ms=duration_ms
            )
            record.mark_passed(duration_ms=duration_ms)
        elif report.failed:
            error_msg = str(report.longrepr) if report.longrepr else "Unknown error"
            # Truncate long error messages
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "..."
            record.add_then(
                f"Test failed: {error_msg[:100]}",
                outcome="failed",
                error=error_msg
            )
            record.mark_failed(error=error_msg, duration_ms=duration_ms)
        elif report.skipped:
            skip_reason = str(report.longrepr[2]) if report.longrepr else "Unknown reason"
            record.add_then(
                f"Test skipped: {skip_reason}",
                outcome="skipped",
                reason=skip_reason
            )
            record.mark_skipped(reason=skip_reason)

        # Write record to evidence directory
        _writer.write_record(record)

    # Handle setup/teardown failures
    elif report.when in ("setup", "teardown") and report.failed:
        error_msg = str(report.longrepr) if report.longrepr else f"{report.when} failed"
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."
        record.add_then(
            f"Test {report.when} failed: {error_msg[:100]}",
            outcome="error",
            error=error_msg
        )
        record.status = "error"
        record.error_message = error_msg
        _writer.errors += 1
        _writer.write_record(record)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print audit trail summary at end of test run."""
    if _writer is None:
        return

    # Write summary file
    summary_path = _writer.write_summary()

    # Print custom summary
    _writer.print_summary()

    # Print path to audit trail
    terminalreporter.write_line("")
    terminalreporter.write_line(f"Audit Trail: {_writer.get_run_path()}", bold=True)
    terminalreporter.write_line(f"Summary: {summary_path}")


def pytest_sessionfinish(session, exitstatus):
    """Clean up at end of session."""
    global _writer, _test_records, _test_start_times
    _test_records.clear()
    _test_start_times.clear()


# Pytest plugin for dots-only output
class DotsOnlyReporter:
    """Custom reporter that shows only dots during test execution."""

    def __init__(self, config):
        self.config = config
        self._tw = config.get_terminal_writer()

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            if report.passed:
                self._tw.write(".", green=True)
            elif report.failed:
                self._tw.write("F", red=True)
            elif report.skipped:
                self._tw.write("s", yellow=True)


def pytest_configure(config):
    """Register dots-only reporter if audit-only mode."""
    global _writer

    if config.getoption("--no-audit", default=False):
        _writer = None
        return

    reset_audit_writer()
    _writer = get_audit_writer()

    # Configure quiet mode if audit-only
    if config.getoption("--audit-only", default=False):
        config.option.verbose = -1
        # Register dots reporter
        config.pluginmanager.register(DotsOnlyReporter(config), "dots_reporter")
