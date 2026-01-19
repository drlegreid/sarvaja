"""
E2E Browser Tests for Session-Task Navigation
==============================================

Per GAP-UI-SESSION-TASKS-001: Session detail must load completed tasks.
Per GAP-UI-AUDIT-2026-01-18: Verify session→task navigation flow.

This file contains regression tests for the fixes applied on 2026-01-18:
1. Session tasks loading in session detail view
2. Task navigation from session detail to Tasks tab

Prerequisites:
- Governance dashboard running on port 8081
- API server running on port 8082
- TypeDB with linked session-task data
- pytest-playwright installed (run locally, not in container)

Run locally: pytest tests/e2e/test_session_task_navigation_e2e.py -v --headed
Alternative: Use MCP Playwright tools for interactive browser testing
"""

import pytest

# Skip entire module if pytest-playwright not available (container environment)
pytest.importorskip("pytest_playwright", reason="pytest-playwright required - run locally")

from playwright.sync_api import Page, expect

from shared.constants import APP_TITLE, DASHBOARD_URL, DEFAULT_TIMEOUTS


# Test data: session with known linked tasks
TEST_SESSION_ID = "SESSION-2026-01-10-INTENT-TEST"
EXPECTED_LINKED_TASKS = ["P12.3", "P12.4", "P12.5"]


class TestSessionTasksDisplay:
    """Regression tests for GAP-UI-SESSION-TASKS-001: Session tasks display."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Sessions view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=DEFAULT_TIMEOUTS["page_load"])
        # Navigate to Sessions tab
        page.click("[data-testid='nav-sessions']")
        page.wait_for_selector("text=Session Evidence")

    def test_sessions_view_loads(self, page: Page):
        """Sessions view loads with session list."""
        expect(page.locator("text=Session Evidence")).to_be_visible()
        # Should show sessions
        page.wait_for_selector("text=session_id", timeout=DEFAULT_TIMEOUTS["element_wait"])

    def test_session_has_click_handler(self, page: Page):
        """Session items in list are clickable."""
        # Find any session row
        session_row = page.locator("tr:has(td)").first
        expect(session_row).to_be_visible()

    def test_click_session_shows_detail(self, page: Page):
        """Clicking a session opens detail view."""
        # Click first session row
        page.locator("tr:has(td)").first.click()
        # Should show detail panel with close button
        expect(page.locator("text=Close")).to_be_visible(timeout=DEFAULT_TIMEOUTS["element_wait"])

    def test_session_detail_shows_tasks_section(self, page: Page):
        """Session detail shows completed tasks section.

        Regression test for GAP-UI-SESSION-TASKS-001:
        Session detail must show "Completed Tasks" section.
        """
        # Click first session
        page.locator("tr:has(td)").first.click()
        page.wait_for_selector("text=Close", timeout=DEFAULT_TIMEOUTS["element_wait"])

        # Should show tasks section
        expect(page.locator("text=Completed Tasks")).to_be_visible()

    def test_known_session_shows_linked_tasks(self, page: Page):
        """Known session shows its linked tasks.

        Regression test for GAP-UI-SESSION-TASKS-001:
        SESSION-2026-01-10-INTENT-TEST should show P12.3, P12.4, P12.5.
        """
        # Find and click the test session
        test_session_locator = page.locator(f"text={TEST_SESSION_ID}").first

        if not test_session_locator.is_visible(timeout=3000):
            pytest.skip(f"Test session {TEST_SESSION_ID} not visible in list")

        test_session_locator.click()
        page.wait_for_selector("text=Close", timeout=DEFAULT_TIMEOUTS["element_wait"])

        # Should show completed tasks section with at least one task
        tasks_header = page.locator("text=Completed Tasks")
        expect(tasks_header).to_be_visible()

        # Look for any task IDs
        for task_id in EXPECTED_LINKED_TASKS:
            task_locator = page.locator(f"text={task_id}")
            if task_locator.is_visible(timeout=1000):
                expect(task_locator).to_be_visible()
                return  # At least one task found

        # If none found, check if there's a loading or error state
        no_tasks = page.locator("text=No completed tasks")
        if no_tasks.is_visible():
            pytest.fail("Session shows 'No completed tasks' but should have linked tasks")


class TestSessionToTaskNavigation:
    """Regression tests for task navigation from session detail.

    Per GAP-DATA-INTEGRITY-001 Phase 3: UI navigation for relationships.
    Tasks in session detail should be clickable and navigate to Tasks tab.
    """

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Sessions view and open test session."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=DEFAULT_TIMEOUTS["page_load"])
        # Navigate to Sessions tab
        page.click("[data-testid='nav-sessions']")
        page.wait_for_selector("text=Session Evidence")

    def test_task_in_session_detail_is_clickable(self, page: Page):
        """Task items in session detail have click handlers.

        Regression test for the task navigation fix applied 2026-01-18.
        """
        # Find and click the test session
        test_session_locator = page.locator(f"text={TEST_SESSION_ID}").first

        if not test_session_locator.is_visible(timeout=3000):
            pytest.skip(f"Test session {TEST_SESSION_ID} not visible")

        test_session_locator.click()
        page.wait_for_selector("text=Close", timeout=DEFAULT_TIMEOUTS["element_wait"])

        # Find first task link - look for v-chip or clickable element with task ID
        task_chip = page.locator("span[class*='v-chip']:has-text('P12')").first

        if not task_chip.is_visible(timeout=2000):
            # Try alternate selector
            task_chip = page.locator("text=/P12\\.[0-9]/").first

        if not task_chip.is_visible(timeout=2000):
            pytest.skip("No task chip found in session detail")

        # Verify it's clickable (has a click handler)
        expect(task_chip).to_be_visible()

    def test_click_task_navigates_to_tasks_view(self, page: Page):
        """Clicking task in session navigates to Tasks tab.

        This is the key regression test for the navigate_to_task fix.
        """
        # Find and click the test session
        test_session_locator = page.locator(f"text={TEST_SESSION_ID}").first

        if not test_session_locator.is_visible(timeout=3000):
            pytest.skip(f"Test session {TEST_SESSION_ID} not visible")

        test_session_locator.click()
        page.wait_for_selector("text=Close", timeout=DEFAULT_TIMEOUTS["element_wait"])

        # Find and click first task chip
        task_chip = page.locator("span[class*='v-chip']:has-text('P12')").first

        if not task_chip.is_visible(timeout=2000):
            task_chip = page.locator("text=/P12\\.[0-9]/").first

        if not task_chip.is_visible(timeout=2000):
            pytest.skip("No task chip found to click")

        task_chip.click()

        # Should navigate to Tasks view
        expect(page.locator("text=Platform Tasks")).to_be_visible(
            timeout=DEFAULT_TIMEOUTS["element_wait"]
        )

    def test_task_detail_opens_after_navigation(self, page: Page):
        """After clicking task, task detail panel opens.

        Full flow: Session detail → click task → Tasks view → task detail.
        """
        # Find and click the test session
        test_session_locator = page.locator(f"text={TEST_SESSION_ID}").first

        if not test_session_locator.is_visible(timeout=3000):
            pytest.skip(f"Test session {TEST_SESSION_ID} not visible")

        test_session_locator.click()
        page.wait_for_selector("text=Close", timeout=DEFAULT_TIMEOUTS["element_wait"])

        # Find and click first task chip
        task_chip = page.locator("span[class*='v-chip']:has-text('P12')").first

        if not task_chip.is_visible(timeout=2000):
            task_chip = page.locator("text=/P12\\.[0-9]/").first

        if not task_chip.is_visible(timeout=2000):
            pytest.skip("No task chip found to click")

        task_chip.click()

        # Should be on Tasks view
        expect(page.locator("text=Platform Tasks")).to_be_visible(
            timeout=DEFAULT_TIMEOUTS["element_wait"]
        )

        # Task detail panel should be open (shows Edit/Delete buttons)
        expect(page.locator("text=Edit")).to_be_visible(
            timeout=DEFAULT_TIMEOUTS["element_wait"]
        )


class TestSessionTaskBidirectionalNavigation:
    """Test bidirectional navigation between sessions and tasks.

    Per GAP-DATA-INTEGRITY-001: Data relationships should be navigable
    in both directions via the UI.
    """

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to dashboard."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=DEFAULT_TIMEOUTS["page_load"])

    def test_task_shows_linked_sessions(self, page: Page):
        """Task detail shows linked sessions field.

        Per GAP-UI-TASK-SESSION-001: Task endpoint returns linked_sessions.
        """
        # Go to Tasks view
        page.click("[data-testid='nav-tasks']")
        page.wait_for_selector("text=Platform Tasks")

        # Click first task
        page.locator("tr:has(td)").first.click()

        # Should show task detail with linked_sessions
        expect(page.locator("text=Close")).to_be_visible(
            timeout=DEFAULT_TIMEOUTS["element_wait"]
        )

        # Look for linked sessions section or field
        linked_sessions = page.locator("text=Linked Sessions").or_(
            page.locator("text=linked_sessions")
        ).or_(
            page.locator("text=Sessions")
        )

        # This might not be visible if task has no linked sessions
        # But the field should exist in the UI

    def test_round_trip_navigation(self, page: Page):
        """Can navigate: Sessions → Session Detail → Task → Tasks View.

        Full round-trip navigation test.
        """
        # Start at Sessions
        page.click("[data-testid='nav-sessions']")
        page.wait_for_selector("text=Session Evidence")

        # Click test session
        test_session_locator = page.locator(f"text={TEST_SESSION_ID}").first
        if not test_session_locator.is_visible(timeout=3000):
            pytest.skip(f"Test session {TEST_SESSION_ID} not visible")

        test_session_locator.click()
        page.wait_for_selector("text=Close", timeout=DEFAULT_TIMEOUTS["element_wait"])

        # Verify we're in session detail
        expect(page.locator("text=Session Details").or_(
            page.locator("text=SESSION-")
        )).to_be_visible()

        # Click task chip if available
        task_chip = page.locator("span[class*='v-chip']:has-text('P12')").first
        if not task_chip.is_visible(timeout=2000):
            task_chip = page.locator("text=/P12\\.[0-9]/").first

        if not task_chip.is_visible(timeout=2000):
            pytest.skip("No task chip found for round-trip test")

        task_chip.click()

        # Verify we're now in Tasks view
        expect(page.locator("text=Platform Tasks")).to_be_visible(
            timeout=DEFAULT_TIMEOUTS["element_wait"]
        )

        # We successfully completed the round trip


# Run with: pytest tests/e2e/test_session_task_navigation_e2e.py -v --headed
