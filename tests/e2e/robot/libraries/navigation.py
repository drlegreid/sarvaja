"""
Navigation Keyword Library
===========================
Per TEST-E2E-FRAMEWORK-01-v1: SRP — handles only page navigation.

Encapsulates tab switching, page verification, and dashboard loading.
Uses data-testid selectors from selectors.resource.
"""

from datetime import timedelta

from Browser import Browser
from Browser.utils.data_types import ElementState, PageLoadStates
from robot.api import logger
from robot.api.deco import keyword


def _parse_timeout(timeout: str) -> timedelta:
    """Convert RF-style timeout string to timedelta."""
    t = timeout.strip().lower()
    if t.endswith("ms"):
        return timedelta(milliseconds=float(t[:-2]))
    if t.endswith("s"):
        return timedelta(seconds=float(t[:-1]))
    if t.endswith("m"):
        return timedelta(minutes=float(t[:-1]))
    return timedelta(seconds=float(t))


# Tab name → (selector_type, selector_value) after navigation.
# "text" = text content match; "testid" = data-testid attribute.
# Use "testid" for tabs whose heading text is ambiguous (e.g. "Tasks").
_TAB_EXPECTATIONS = {
    "chat": ("testid", "chat-view"),
    "rules": ("text", "Governance Rules"),
    "agents": ("text", "Registered Agents"),
    "tasks": ("testid", "tasks-list"),
    "sessions": ("text", "Session Evidence"),
    "executive": ("text", "Executive"),
    "decisions": ("text", "Decisions"),
    "impact": ("testid", "impact-analyzer"),
    "trust": ("text", "Agent Trust Dashboard"),
    "workflow": ("testid", "workflow-dashboard"),
    "audit": ("testid", "audit-dashboard"),
    "monitor": ("testid", "monitor-dashboard"),
    "infra": ("text", "Infrastructure Health"),
    "metrics": ("testid", "metrics-dashboard"),
    "tests": ("testid", "tests-dashboard"),
    "projects": ("testid", "projects-list"),
    "workspaces": ("testid", "workspaces-list"),
}


class navigation:
    """Page navigation keywords — SRP: only navigation concerns.

    Provides high-level navigation that combines clicking nav items
    with verifying the target page loaded correctly.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_DOC_FORMAT = "TEXT"

    def __init__(self):
        self._browser: Browser | None = None

    def _get_browser(self) -> Browser:
        if self._browser is None:
            from robot.libraries.BuiltIn import BuiltIn
            self._browser = BuiltIn().get_library_instance("Browser")
        return self._browser

    @keyword("Open Dashboard")
    def open_dashboard(self, url: str, timeout: str = "30s"):
        """Navigate to the dashboard and wait for it to load.

        Args:
            url: Dashboard URL (e.g. http://localhost:8081).
            timeout: Max time to wait for page load.
        """
        browser = self._get_browser()
        browser.new_page(url)
        browser.wait_for_load_state(
            PageLoadStates.networkidle, timeout=_parse_timeout(timeout)
        )

    @keyword("Dashboard Should Be Loaded")
    def dashboard_should_be_loaded(self, app_title: str, timeout: str = "15s"):
        """Verify the dashboard has loaded by checking for the app title.

        Args:
            app_title: Expected application title text.
            timeout: Max time to wait for title element.
        """
        browser = self._get_browser()
        browser.wait_for_elements_state(
            f"text={app_title}", ElementState.visible,
            timeout=_parse_timeout(timeout),
        )

    @keyword("Navigate To Tab")
    def navigate_to_tab(self, tab_name: str, timeout: str = "10s"):
        """Click a navigation tab and verify the target page loaded.

        Uses data-testid='nav-{tab_name}' selector for the click.
        Verifies expected content text is visible after navigation.

        Args:
            tab_name: Tab identifier (rules, agents, tasks, sessions, etc.).
            timeout: Max time to wait for page content.
        """
        browser = self._get_browser()
        nav_selector = f"[data-testid='nav-{tab_name.lower()}']"

        browser.click(nav_selector)

        expectation = _TAB_EXPECTATIONS.get(tab_name.lower())
        if expectation:
            sel_type, sel_value = expectation
            if sel_type == "testid":
                content_selector = f"[data-testid='{sel_value}']"
            else:
                content_selector = f"text={sel_value}"
            browser.wait_for_elements_state(
                content_selector, ElementState.visible,
                timeout=_parse_timeout(timeout),
            )
            logger.info(f"Navigated to '{tab_name}' — verified '{sel_value}'")

    @keyword("Verify Tab Is Active")
    def verify_tab_is_active(self, tab_name: str):
        """Verify a specific tab's content is currently displayed.

        Args:
            tab_name: Tab identifier to verify.
        """
        browser = self._get_browser()
        expectation = _TAB_EXPECTATIONS.get(tab_name.lower())
        if expectation:
            sel_type, sel_value = expectation
            if sel_type == "testid":
                selector = f"[data-testid='{sel_value}']"
            else:
                selector = f"text={sel_value}"
        else:
            selector = f"text={tab_name}"
        browser.wait_for_elements_state(
            selector, ElementState.visible,
            timeout=timedelta(seconds=10),
        )

    @keyword("Navigation Tab Should Be Visible")
    def navigation_tab_should_be_visible(self, tab_name: str):
        """Assert that a navigation tab element is present in the sidebar.

        Uses data-testid selector to avoid ambiguity with page content.

        Args:
            tab_name: Tab key (e.g. 'Rules', 'Agents') — maps to nav-{lower}.
        """
        browser = self._get_browser()
        selector = f"[data-testid='nav-{tab_name.lower()}']"
        browser.wait_for_elements_state(
            selector, ElementState.visible,
            timeout=timedelta(seconds=10),
        )

    @keyword("Navigate Back From Detail")
    def navigate_back_from_detail(self, back_selector: str, timeout: str = "10s"):
        """Click a back button in a detail view to return to list.

        Args:
            back_selector: CSS selector for the back button.
            timeout: Max time to wait for list to reappear.
        """
        browser = self._get_browser()
        browser.click(back_selector)
        browser.wait_for_elements_state(
            "tbody tr:has(td)", ElementState.visible,
            timeout=_parse_timeout(timeout),
        )
