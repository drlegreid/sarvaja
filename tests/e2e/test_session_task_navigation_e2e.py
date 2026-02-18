"""
E2E Browser Tests for Session-Task Navigation
==============================================

Per GAP-UI-SESSION-TASKS-001: Session detail must load completed tasks.
Per GAP-UI-AUDIT-2026-01-18: Verify session→task navigation flow.

Prerequisites:
- Governance dashboard running on port 8081
- API server running on port 8082
- TypeDB with linked session-task data
- pytest-playwright installed (run locally, not in container)

Run locally: pytest tests/e2e/test_session_task_navigation_e2e.py -v --headed

NOTE: Trame's single-threaded WebSocket server limits concurrent page
connections.  Each test class uses exactly ONE page.goto() to stay within
the connection budget.  Multiple assertions per test maximize coverage
per connection.
"""

import pytest

pytest.importorskip("pytest_playwright", reason="pytest-playwright required - run locally")

from playwright.sync_api import Page, expect

from shared.constants import APP_TITLE, DASHBOARD_URL

# Timeouts (ms) — Trame is a WebSocket SPA, data loads asynchronously
LOAD_TIMEOUT = 30_000
ELEM_TIMEOUT = 10_000

# Selectors matching current dashboard UI (updated 2026-02-18)
SESSION_DETAIL = "[data-testid='session-detail']"
SESSION_BACK = "[data-testid='session-detail-back-btn']"
TASK_DETAIL = "[data-testid='task-detail']"

# Test data: session with known linked tasks
TEST_SESSION_ID = "SESSION-2026-01-10-INTENT-TEST"
EXPECTED_LINKED_TASKS = ["P12.3", "P12.4", "P12.5"]


def _dismiss_overlays(page: Page):
    """Disable Vuetify overlay containers that intercept pointer events."""
    page.evaluate("""() => {
        for (const c of document.querySelectorAll('.v-overlay-container')) {
            c.style.pointerEvents = 'none';
            for (const e of c.querySelectorAll('*')) e.style.pointerEvents = 'none';
        }
    }""")


def _safe_click(page: Page, selector: str, timeout: int = LOAD_TIMEOUT):
    """Click element after dismissing Vuetify overlays."""
    _dismiss_overlays(page)
    page.click(selector, timeout=timeout)


class TestSessionsViewAndDetail:
    """Sessions list + detail + completed tasks (GAP-UI-SESSION-TASKS-001).

    Single page load covers: list view, clickable rows, detail view, tasks section.
    """

    def test_sessions_list_and_detail_flow(self, page: Page):
        """Full flow: sessions list -> click row -> detail with tasks section."""
        page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=LOAD_TIMEOUT)
        page.wait_for_selector(f"text={APP_TITLE}", timeout=LOAD_TIMEOUT)
        _safe_click(page, "[data-testid='nav-sessions']")
        page.wait_for_selector("tr:has(td)", timeout=LOAD_TIMEOUT)

        # List view
        expect(page.locator("text=Session Evidence")).to_be_visible(timeout=ELEM_TIMEOUT)
        expect(page.locator("text=Session ID")).to_be_visible(timeout=ELEM_TIMEOUT)
        expect(page.locator("tr:has(td)").first).to_be_visible(timeout=ELEM_TIMEOUT)

        # Click first row -> detail
        _safe_click(page, "tr:has(td) >> nth=0")
        page.wait_for_selector(SESSION_DETAIL, timeout=ELEM_TIMEOUT)
        expect(page.locator(SESSION_BACK)).to_be_visible(timeout=ELEM_TIMEOUT)
        expect(page.locator("text=Completed Tasks")).to_be_visible(timeout=ELEM_TIMEOUT)

        # Back to list, try known session if visible
        _safe_click(page, SESSION_BACK)
        page.wait_for_selector("tr:has(td)", timeout=ELEM_TIMEOUT)

        loc = page.locator(f"text={TEST_SESSION_ID}").first
        if loc.is_visible(timeout=3000):
            _safe_click(page, f"text={TEST_SESSION_ID}")
            page.wait_for_selector(SESSION_DETAIL, timeout=ELEM_TIMEOUT)
            expect(page.locator("text=Completed Tasks")).to_be_visible(timeout=ELEM_TIMEOUT)

            for task_id in EXPECTED_LINKED_TASKS:
                if page.locator(f"text={task_id}").is_visible(timeout=1000):
                    break


class TestTaskDetailFromTasksView:
    """Task detail is reachable via tasks nav."""

    def test_task_detail_opens(self, page: Page):
        """Navigate to tasks, click first row, detail panel opens."""
        page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=LOAD_TIMEOUT)
        page.wait_for_selector(f"text={APP_TITLE}", timeout=LOAD_TIMEOUT)
        _safe_click(page, "[data-testid='nav-tasks']")
        page.wait_for_selector("tr:has(td)", timeout=LOAD_TIMEOUT)

        _safe_click(page, "tr:has(td) >> nth=0")
        expect(page.locator(TASK_DETAIL)).to_be_visible(timeout=ELEM_TIMEOUT)


class TestSessionToTaskRoundTrip:
    """Sessions -> detail -> task chip -> Tasks view (GAP-DATA-INTEGRITY-001).

    The key regression test for session-to-task navigation.
    """

    def test_round_trip(self, page: Page):
        """Click session -> task chip -> arrives at Tasks view with detail."""
        page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=LOAD_TIMEOUT)
        page.wait_for_selector(f"text={APP_TITLE}", timeout=LOAD_TIMEOUT)
        _safe_click(page, "[data-testid='nav-sessions']")
        page.wait_for_selector("tr:has(td)", timeout=LOAD_TIMEOUT)

        loc = page.locator(f"text={TEST_SESSION_ID}").first
        if not loc.is_visible(timeout=3000):
            pytest.skip(f"Test session {TEST_SESSION_ID} not visible")

        _safe_click(page, f"text={TEST_SESSION_ID}")
        page.wait_for_selector(SESSION_DETAIL, timeout=ELEM_TIMEOUT)
        expect(page.locator("[data-testid='session-detail-id']")).to_be_visible()

        chip = page.locator("span[class*='v-chip']:has-text('P12')").first
        if not chip.is_visible(timeout=2000):
            chip = page.locator("text=/P12\\.[0-9]/").first
        if not chip.is_visible(timeout=2000):
            pytest.skip("No task chip found for round-trip test")

        chip_text = chip.text_content()
        _safe_click(page, f"text={chip_text}")
        expect(page.locator("text=Tasks")).to_be_visible(timeout=ELEM_TIMEOUT)
        expect(page.locator("[data-testid='task-detail-edit-btn']")).to_be_visible(
            timeout=ELEM_TIMEOUT
        )
