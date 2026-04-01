"""
Pytest Plugin for BDD Evidence Collection.

Per GAP-TEST-EVIDENCE-001: File-based test evidence with BDD structure.
Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level.

Usage:
    pytest tests/ --bdd-evidence                    # Enable BDD evidence
    pytest tests/ --bdd-evidence --evidence-dir=custom  # Custom directory
    pytest tests/ --bdd-evidence --session-id=SESSION-2026-01-21-TEST

Created: 2026-01-21
"""

import os
from typing import Optional

import pytest

from tests.evidence.collector import BDDEvidenceCollector, EvidenceRecord
from tests.evidence.rule_linker import RuleLinker
from tests.evidence.trace_capture import TraceCapture, RequestsTraceAdapter, link_traces_to_evidence
from tests.evidence.holographic_store import get_global_store, reset_global_store, HolographicTestStore

# Try to import session collector for event-based reporting
try:
    from governance.session_collector import get_or_create_session, list_active_sessions
    SESSION_COLLECTOR_AVAILABLE = True
except ImportError:
    SESSION_COLLECTOR_AVAILABLE = False


# Global collector instance for the test session
_collector: Optional[BDDEvidenceCollector] = None
_rule_linker: Optional[RuleLinker] = None
_holographic_store: Optional[HolographicTestStore] = None
_session_reporting_enabled: bool = False
_trace_capture_enabled: bool = False
_current_trace_capture: Optional[TraceCapture] = None
_compressed_summary_enabled: bool = False
_holographic_html_dir: Optional[str] = None


def pytest_addoption(parser):
    """Add BDD evidence options to pytest."""
    group = parser.getgroup("bdd_evidence", "BDD Evidence Collection (GAP-TEST-EVIDENCE-001)")

    group.addoption(
        "--bdd-evidence",
        action="store_true",
        default=False,
        help="Enable BDD-structured evidence collection"
    )
    group.addoption(
        "--evidence-dir",
        action="store",
        default="evidence/tests",
        help="Directory for evidence files (default: evidence/tests)"
    )
    group.addoption(
        "--session-id",
        action="store",
        default=None,
        help="Governance session ID for linking"
    )
    group.addoption(
        "--session-report",
        action="store_true",
        default=False,
        help="Report test results to governance session (per GAP-TEST-EVIDENCE-002)"
    )
    group.addoption(
        "--trace-capture",
        action="store_true",
        default=False,
        help="Enable HTTP/MCP trace capture during tests (per TEST-002)"
    )
    group.addoption(
        "--compressed-summary",
        action="store_true",
        default=False,
        help="Output compressed test summary for LLM context (per EPIC-TEST-COMPRESS-001)"
    )
    group.addoption(
        "--holographic-html",
        action="store",
        default=None,
        help="Output directory for holographic HTML report (per FEAT-009)"
    )


def pytest_configure(config):
    """Configure BDD evidence collection."""
    global _collector, _rule_linker, _holographic_store, _session_reporting_enabled, _trace_capture_enabled, _compressed_summary_enabled, _holographic_html_dir

    # Register markers
    config.addinivalue_line(
        "markers",
        "rules(*rule_ids): Mark test as validating specific governance rules"
    )
    config.addinivalue_line(
        "markers",
        "gaps(*gap_ids): Mark test as addressing specific gaps"
    )
    config.addinivalue_line(
        "markers",
        "intent(description): High-level test purpose for BDD evidence"
    )

    # Always initialize holographic store (per BUG-014 / TEST-HOLO-01-v1)
    reset_global_store()
    _holographic_store = get_global_store()

    # Check if BDD evidence is enabled
    try:
        bdd_enabled = config.getoption("--bdd-evidence", default=False)
        session_report = config.getoption("--session-report", default=False)
        trace_capture = config.getoption("--trace-capture", default=False)
        compressed_summary = config.getoption("--compressed-summary", default=False)
        holographic_html = config.getoption("--holographic-html", default=None)
    except (ValueError, AttributeError):
        return

    # Enable session reporting if requested
    _session_reporting_enabled = session_report and SESSION_COLLECTOR_AVAILABLE
    _trace_capture_enabled = trace_capture
    _compressed_summary_enabled = compressed_summary
    _holographic_html_dir = holographic_html

    if _session_reporting_enabled:
        print("\n[SESSION-REPORT] Event-based reporting enabled (GAP-TEST-EVIDENCE-002)")

    if _trace_capture_enabled:
        print("\n[TRACE-CAPTURE] HTTP/MCP trace capture enabled (TEST-002)")

    if _compressed_summary_enabled:
        print("\n[COMPRESSED-SUMMARY] LLM-optimized summary enabled (EPIC-TEST-COMPRESS-001)")

    if not bdd_enabled:
        return

    # Get options
    evidence_dir = config.getoption("--evidence-dir", default="evidence/tests")
    session_id = config.getoption("--session-id", default=None)

    # Try to get session ID from environment if not provided
    if not session_id:
        session_id = os.environ.get("GOVERNANCE_SESSION_ID")

    # Initialize collector
    _collector = BDDEvidenceCollector(
        base_dir=evidence_dir,
        session_id=session_id
    )
    _rule_linker = RuleLinker()

    # Start run
    _collector.start_run()

    print(f"\n[BDD-EVIDENCE] Enabled - Output: {_collector.get_run_dir()}")
    if session_id:
        print(f"[BDD-EVIDENCE] Linked to session: {session_id}")


def pytest_collection_modifyitems(config, items):
    """Process markers on collected tests."""
    global _rule_linker

    if not _rule_linker:
        return

    for item in items:
        # Extract rule/gap references from docstring
        docstring = item.obj.__doc__ if hasattr(item, 'obj') else None

        # Get explicit markers
        rules_marker = item.get_closest_marker("rules")
        gaps_marker = item.get_closest_marker("gaps")

        explicit_rules = list(rules_marker.args) if rules_marker else []
        explicit_gaps = list(gaps_marker.args) if gaps_marker else []

        # Register test with linker
        _rule_linker.register_test(
            test_id=item.nodeid,
            docstring=docstring,
            rules=explicit_rules,
            gaps=explicit_gaps
        )


def pytest_runtest_setup(item):
    """Called before each test runs."""
    global _collector, _rule_linker, _trace_capture_enabled, _current_trace_capture

    # Initialize trace capture if enabled
    if _trace_capture_enabled:
        _current_trace_capture = TraceCapture(test_id=item.nodeid)
        _current_trace_capture.start()

    if not _collector:
        return

    # Determine test category from path
    rel_path = str(item.fspath)
    if "/e2e/" in rel_path or "_e2e.py" in rel_path:
        category = "e2e"
    elif "/integration/" in rel_path:
        category = "integration"
    else:
        category = "unit"

    # Get intent from marker or docstring
    intent_marker = item.get_closest_marker("intent")
    if intent_marker and intent_marker.args:
        intent = intent_marker.args[0]
    elif hasattr(item, 'obj') and item.obj.__doc__:
        # Use first line of docstring as intent
        doc = item.obj.__doc__.strip()
        intent = doc.split('\n')[0].strip()
    else:
        intent = f"Test: {item.name}"

    # Get linked rules/gaps
    rules = _rule_linker.get_test_rules(item.nodeid) if _rule_linker else []
    gaps = _rule_linker.get_test_gaps(item.nodeid) if _rule_linker else []

    # Start test evidence collection
    _collector.start_test(
        test_id=item.nodeid,
        category=category,
        intent=intent,
        rules=rules,
        gaps=gaps
    )


def _detect_category(fspath: str) -> str:
    """Detect test category from file path."""
    rel_path = str(fspath)
    if "/e2e/" in rel_path or "_e2e.py" in rel_path:
        return "e2e"
    elif "/integration/" in rel_path:
        return "integration"
    return "unit"


def pytest_runtest_logreport(report):
    """Called after each test phase (setup, call, teardown)."""
    global _collector, _rule_linker, _holographic_store, _session_reporting_enabled, _trace_capture_enabled, _current_trace_capture, _compressed_summary_enabled

    # Only process 'call' phase (actual test execution) or setup skip
    evidence = None
    if report.when == "call":
        # Always push to holographic store (per BUG-014 / TEST-HOLO-01-v1)
        if _holographic_store is not None:
            category = _detect_category(report.fspath)
            name = report.nodeid.split("::")[-1] if "::" in report.nodeid else report.nodeid
            _holographic_store.push_event(
                test_id=report.nodeid,
                name=name,
                status=report.outcome,
                category=category,
                duration_ms=report.duration * 1000 if hasattr(report, 'duration') else 0,
                error_message=str(report.longrepr)[:200] if report.failed else None,
            )

        # End trace capture if active
        trace_data = None
        if _trace_capture_enabled and _current_trace_capture:
            _current_trace_capture.end()
            trace_data = {
                "traces": _current_trace_capture.get_traces(),
                "summary": _current_trace_capture.get_summary(),
            }

        if _collector and _collector.current_test:
            # End test with result
            evidence = _collector.end_test(
                status=report.outcome,
                duration_ms=report.duration * 1000,
                error=str(report.longrepr)[:500] if report.failed else None,
                traceback=str(report.longrepr) if report.failed else None
            )

            # Link traces to evidence if available
            if trace_data and evidence:
                evidence_dict = evidence.to_dict()
                evidence_dict["trace_data"] = trace_data
                evidence_dict["correlation_id"] = _current_trace_capture.correlation_id

        # Report to governance session (GAP-TEST-EVIDENCE-002)
        if _session_reporting_enabled and SESSION_COLLECTOR_AVAILABLE:
            _report_test_to_session(report, evidence)

    elif report.when == "setup" and report.skipped:
        # Test was skipped during setup — push to holographic store (BUG-014)
        if _holographic_store is not None:
            category = _detect_category(report.fspath)
            name = report.nodeid.split("::")[-1] if "::" in report.nodeid else report.nodeid
            skip_reason = str(report.longrepr)[:200] if report.longrepr else "Skipped"
            _holographic_store.push_event(
                test_id=report.nodeid,
                name=name,
                status="skipped",
                category=category,
                duration_ms=0.0,
                error_message=skip_reason,
            )

        skip_reason = str(report.longrepr) if report.longrepr else "Skipped"
        if _collector and _collector.current_test:
            evidence = _collector.end_test(
                status="skipped",
                duration_ms=0.0,
                error=skip_reason
            )

        # Report to governance session (GAP-TEST-EVIDENCE-002)
        if _session_reporting_enabled and SESSION_COLLECTOR_AVAILABLE:
            _report_test_to_session(report, evidence)


def _report_test_to_session(report, evidence: Optional[EvidenceRecord]) -> None:
    """Report test result to governance session. Per GAP-TEST-EVIDENCE-002."""
    global _rule_linker

    try:
        sessions = list_active_sessions()
        if not sessions:
            return  # No active session to report to

        collector = get_or_create_session(sessions[-1].split("-")[-1].lower())

        # Extract test info
        test_id = report.nodeid
        name = test_id.split("::")[-1] if "::" in test_id else test_id

        # Determine category from path
        if "/e2e/" in test_id or "_e2e.py" in test_id:
            category = "e2e"
        elif "/integration/" in test_id:
            category = "integration"
        else:
            category = "unit"

        # Get linked rules/gaps
        rules = []
        gaps = []
        intent = None
        if _rule_linker:
            rules = _rule_linker.get_test_rules(test_id)
            gaps = _rule_linker.get_test_gaps(test_id)
        if evidence:
            intent = evidence.intent
            rules = evidence.linked_rules or rules
            gaps = evidence.linked_gaps or gaps

        # Report to session
        collector.capture_test_result(
            test_id=test_id,
            name=name,
            category=category,
            status=report.outcome,
            duration_ms=report.duration * 1000 if hasattr(report, 'duration') else 0.0,
            intent=intent,
            linked_rules=rules,
            linked_gaps=gaps,
            error_message=str(report.longrepr)[:500] if report.failed else None
        )
    except Exception:
        pass  # Silent fail - don't disrupt test run


def pytest_sessionfinish(session, exitstatus):
    """Called after all tests complete."""
    global _collector, _rule_linker, _holographic_store, _compressed_summary_enabled, _holographic_html_dir

    # Output compressed summary from holographic store (BUG-014 / TEST-HOLO-01-v1)
    if _compressed_summary_enabled and _holographic_store and _holographic_store.count > 0:
        z1 = _holographic_store.query(zoom=1, format="text")
        if isinstance(z1, str):
            print(f"\n[HOLOGRAPHIC-SUMMARY] zoom=1")
            print(z1)
        elif isinstance(z1, dict) and "summary" in z1:
            print(f"\n[HOLOGRAPHIC-SUMMARY] zoom=1")
            print(z1["summary"])

    # Generate HTML report (per FEAT-009)
    if _holographic_html_dir and _holographic_store and _holographic_store.count > 0:
        from tests.evidence.holographic_report import save_html_report
        path = save_html_report(_holographic_store, output_dir=_holographic_html_dir)
        print(f"\n[HOLOGRAPHIC-HTML] {path}")

    if not _collector:
        return

    # End run and generate summary
    summary = _collector.end_run()

    if summary:
        print(f"\n[BDD-EVIDENCE] Run complete:")
        print(f"  - Tests: {summary.get('total_tests', 0)}")
        print(f"  - Passed: {summary.get('passed', 0)}")
        print(f"  - Failed: {summary.get('failed', 0)}")
        print(f"  - Skipped: {summary.get('skipped', 0)}")
        print(f"  - Success Rate: {summary.get('success_rate', '0%')}")
        print(f"  - Rules Covered: {len(summary.get('linked_rules', []))}")
        print(f"  - Gaps Covered: {len(summary.get('linked_gaps', []))}")
        print(f"  - Output: {_collector.get_run_dir() / 'summary.json'}")

    if _rule_linker:
        coverage = _rule_linker.get_coverage_summary()
        print(f"  - Rule Coverage: {coverage.get('coverage_rate', '0%')}")


# Fixture for manual BDD step recording
@pytest.fixture
def bdd_evidence():
    """
    Fixture for recording BDD steps manually in tests.

    Usage:
        def test_user_login(bdd_evidence):
            bdd_evidence.given("a registered user exists")
            # ... setup code ...

            bdd_evidence.when("the user submits credentials")
            # ... action code ...

            bdd_evidence.then("the user is logged in")
            # ... assertion code ...
    """
    global _collector

    class BDDStepRecorder:
        """Helper class for recording BDD steps."""

        def given(self, description: str, data: dict = None):
            """Record a GIVEN step."""
            if _collector:
                _collector.given(description, data)

        def when(self, description: str, data: dict = None):
            """Record a WHEN step."""
            if _collector:
                _collector.when(description, data)

        def then(self, description: str, data: dict = None):
            """Record a THEN step."""
            if _collector:
                _collector.then(description, data)

        def and_step(self, description: str, data: dict = None):
            """Record an AND step."""
            if _collector:
                _collector.and_step(description, data)

        def but_step(self, description: str, data: dict = None):
            """Record a BUT step."""
            if _collector:
                _collector.but_step(description, data)

        def step_failed(self, error: str):
            """Mark the last step as failed."""
            if _collector:
                _collector.mark_step_failed(error)

    return BDDStepRecorder()
