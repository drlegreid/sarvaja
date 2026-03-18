"""
Generic Browser Actions Library
================================
Per TEST-E2E-FRAMEWORK-01-v1: Centralized actions following SRP.
Handles: click, wait (Fibonacci backoff), scroll, fill.

All low-level browser interactions go through this library.
Platform workarounds (Vuetify overlays, Trame WS delays) are
handled centrally here so test suites stay clean.
"""

from datetime import timedelta

from Browser import Browser
from Browser.utils.data_types import ElementState
from robot.api import logger
from robot.api.deco import keyword


def _parse_state(state: str) -> ElementState:
    """Convert string state name to ElementState enum."""
    return ElementState[state.lower()]


def _parse_timeout(timeout: str) -> timedelta:
    """Convert RF-style timeout string to timedelta.

    Supports: '10s', '1000ms', '1m', plain seconds as string.
    """
    t = timeout.strip().lower()
    if t.endswith("ms"):
        return timedelta(milliseconds=float(t[:-2]))
    if t.endswith("s"):
        return timedelta(seconds=float(t[:-1]))
    if t.endswith("m"):
        return timedelta(minutes=float(t[:-1]))
    return timedelta(seconds=float(t))


# Fibonacci sequence for backoff intervals (seconds)
_FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21]


class actions:
    """Generic browser actions — SRP: only element interactions.

    All keywords accept CSS selectors (data-testid preferred).
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_DOC_FORMAT = "TEXT"

    def __init__(self):
        self._browser: Browser | None = None

    def _get_browser(self) -> Browser:
        """Lazy-load Browser library instance from RF context."""
        if self._browser is None:
            from robot.libraries.BuiltIn import BuiltIn
            self._browser = BuiltIn().get_library_instance("Browser")
        return self._browser

    @keyword("Click Element Safely")
    def click_element_safely(self, selector: str, timeout: str = "10s"):
        """Click an element after ensuring it's actionable.

        Waits for element to be visible before clicking. Overlay CSS
        is injected at suite level via overlay library.

        Args:
            selector: CSS selector for the element to click.
            timeout: Max time to wait for element (default 10s).
        """
        browser = self._get_browser()
        browser.wait_for_elements_state(
            selector, ElementState.visible, timeout=_parse_timeout(timeout)
        )
        browser.click(selector)

    @keyword("Click Element Forced")
    def click_element_forced(self, selector: str):
        """Force-click an element using JavaScript click().

        Use for elements that don't respond to standard clicks
        (e.g. Vuetify table rows after WS degradation).

        Args:
            selector: CSS selector for the element to click.
        """
        browser = self._get_browser()
        # evaluate_javascript(selector, js_function) — element is 'e' arg
        browser.evaluate_javascript(
            selector, "(e) => { if (e) e.click(); }"
        )

    @keyword("Wait For Element With Backoff")
    def wait_for_element_with_backoff(
        self, selector: str, max_attempts: int = 6, state: str = "visible"
    ) -> bool:
        """Wait for element using Fibonacci backoff intervals.

        Intervals: 1s, 1s, 2s, 3s, 5s, 8s (default 6 attempts = 20s total).
        Suitable for Trame WebSocket SPA where state changes are async.

        Args:
            selector: CSS selector to wait for.
            max_attempts: Maximum retry attempts (default 6, max 8).
            state: Element state to wait for — 'visible', 'attached',
                   'hidden', 'detached' (default 'visible').

        Returns:
            True if element found within attempts.

        Raises:
            AssertionError: If element not found after all attempts.
        """
        browser = self._get_browser()
        max_attempts = min(int(max_attempts), len(_FIBONACCI))
        elem_state = _parse_state(state) if isinstance(state, str) else state

        for attempt in range(max_attempts):
            try:
                interval_td = timedelta(seconds=_FIBONACCI[attempt])
                browser.wait_for_elements_state(
                    selector, elem_state, timeout=interval_td
                )
                logger.info(
                    f"Element '{selector}' found on attempt "
                    f"{attempt + 1}/{max_attempts}"
                )
                return True
            except Exception:
                if attempt == max_attempts - 1:
                    total = sum(_FIBONACCI[:max_attempts])
                    raise AssertionError(
                        f"Element '{selector}' not {state} after "
                        f"{max_attempts} attempts ({total}s total)"
                    )
                logger.info(
                    f"Attempt {attempt + 1}/{max_attempts}: "
                    f"'{selector}' not yet {state}, "
                    f"retrying in {_FIBONACCI[attempt + 1]}s..."
                )
        return False

    @keyword("Fill Input Field")
    def fill_input_field(self, selector: str, value: str, clear: bool = True):
        """Clear and fill an input field with the given value.

        Args:
            selector: CSS selector for the input element.
            value: Text to type into the field.
            clear: Whether to clear existing content first (default True).
        """
        browser = self._get_browser()
        if clear:
            browser.clear_text(selector)
        browser.fill_text(selector, value)

    @keyword("Scroll To Element")
    def scroll_to_element(self, selector: str):
        """Scroll an element into the viewport.

        Args:
            selector: CSS selector for the element to scroll to.
        """
        browser = self._get_browser()
        browser.scroll_to_element(selector)

    @keyword("Element Should Be Visible With Backoff")
    def element_should_be_visible_with_backoff(
        self, selector: str, max_attempts: int = 6
    ):
        """Assert element is visible using Fibonacci backoff.

        Convenience keyword combining wait + assertion for BDD steps.

        Args:
            selector: CSS selector to verify.
            max_attempts: Maximum retry attempts (default 6).
        """
        self.wait_for_element_with_backoff(selector, max_attempts, "visible")

    @keyword("Wait For Table Rows")
    def wait_for_table_rows(
        self, table_selector: str = "tbody", max_attempts: int = 6
    ):
        """Wait for a data table to have at least one data row.

        Uses Fibonacci backoff. Targets first row to avoid strict mode
        violations when multiple rows exist.

        Args:
            table_selector: CSS selector for the table body (default 'tbody').
            max_attempts: Maximum retry attempts (default 6).
        """
        selector = f"{table_selector} tr:has(td) >> nth=0"
        self.wait_for_element_with_backoff(selector, max_attempts, "visible")

    @keyword("Click Table Row")
    def click_table_row(self, index: int = 0, table_selector: str = "tbody"):
        """Click a specific table row by index.

        Args:
            index: Zero-based row index (default 0 = first row).
            table_selector: CSS selector for the table body (default 'tbody').
        """
        selector = f"{table_selector} tr:has(td) >> nth={index}"
        self.click_element_safely(selector)

    @keyword("Get Element Text Safely")
    def get_element_text_safely(self, selector: str) -> str:
        """Get text content of an element.

        Args:
            selector: CSS selector for the element.

        Returns:
            Text content of the element.
        """
        browser = self._get_browser()
        return browser.get_text(selector)
