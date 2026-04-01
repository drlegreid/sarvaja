"""
Robot Framework Holographic Listener - pushes test results to HolographicTestStore.

Per BUG-014 / TEST-HOLO-01-v1: Holographic evidence must be auto-populated
at all test levels including Robot Framework E2E.

Usage in robot:
    robot --listener tests.evidence.robot_listener.HolographicListener tests/e2e/

Or in robot.yaml:
    listeners:
      - tests.evidence.robot_listener.HolographicListener
"""

from tests.evidence.holographic_store import get_global_store
from tests.evidence.holographic_report import save_html_report

# Category keywords to detect from Robot tags
_CATEGORY_TAGS = {"unit", "integration", "e2e"}


class HolographicListener:
    """Robot Framework listener v3 that pushes results to HolographicTestStore."""

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, session_id: str = None, output_dir: str = None):
        self._store = get_global_store(session_id=session_id)
        self._output_dir = output_dir

    def end_test(self, data, result):
        """Called after each test completes. Pushes to holographic store."""
        # Detect category from tags (default: e2e for Robot tests)
        tags = [str(t).lower() for t in getattr(data, "tags", [])]
        category = "e2e"
        for tag in tags:
            if tag in _CATEGORY_TAGS:
                category = tag
                break

        # Map Robot status to holographic status
        status = "passed" if result.status == "PASS" else "failed"

        # Extract duration in ms
        try:
            duration_ms = result.elapsed_time.total_seconds() * 1000
        except (AttributeError, TypeError):
            duration_ms = 0.0

        # Error message for failures
        error_message = None
        if result.status == "FAIL" and result.message:
            error_message = str(result.message)[:200]

        self._store.push_event(
            test_id=getattr(data, "full_name", data.name),
            name=data.name,
            status=status,
            category=category,
            duration_ms=duration_ms,
            error_message=error_message,
        )

    def close(self):
        """Called when Robot execution ends. Prints summary + generates HTML."""
        if self._store.count == 0:
            return

        z1 = self._store.query(zoom=1, format="text")
        summary_text = z1 if isinstance(z1, str) else z1.get("summary", "")
        print(f"\n[HOLOGRAPHIC-SUMMARY] Robot E2E | {self._store.count} tests")
        print(summary_text)

        # Auto-generate HTML report (per FEAT-009)
        if self._output_dir:
            path = save_html_report(self._store, output_dir=self._output_dir)
            print(f"[HOLOGRAPHIC-HTML] {path}")
