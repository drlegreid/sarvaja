"""
Vuetify Overlay Management Library
====================================
Per TEST-E2E-FRAMEWORK-01-v1: Centralized platform workaround.

Handles the Vuetify/Trame overlay scrim that intercepts pointer events.
This is a known Trame SPA issue where .v-overlay-container elements
block clicks even when no modal is open.

Used as Suite Setup to inject CSS once per suite.
"""

from Browser import Browser
from robot.api import logger
from robot.api.deco import keyword


# CSS that disables pointer events on all Vuetify overlay elements.
# Idempotent — checks for existing style tag by ID.
_OVERLAY_FIX_JS = """() => {
    if (!document.getElementById('rf-overlay-fix')) {
        const s = document.createElement('style');
        s.id = 'rf-overlay-fix';
        s.textContent = `
            .v-overlay-container,
            .v-overlay-container *,
            .v-overlay__scrim {
                pointer-events: none !important;
            }
        `;
        document.head.appendChild(s);
    }
    return 'overlay-fix-applied';
}"""


class overlay:
    """Vuetify overlay management — SRP: only overlay concerns.

    Injects CSS to disable pointer-events on Vuetify's overlay
    container elements. Should be called once after page load
    via Suite Setup or Test Setup.
    """

    ROBOT_LIBRARY_SCOPE = "SUITE"
    ROBOT_LIBRARY_DOC_FORMAT = "TEXT"

    def __init__(self):
        self._browser: Browser | None = None
        self._applied = False

    def _get_browser(self) -> Browser:
        if self._browser is None:
            from robot.libraries.BuiltIn import BuiltIn
            self._browser = BuiltIn().get_library_instance("Browser")
        return self._browser

    @keyword("Inject Overlay Fix")
    def inject_overlay_fix(self):
        """Inject CSS to disable Vuetify overlay pointer interception.

        Idempotent — safe to call multiple times. Checks for existing
        style tag before injecting.

        Should be called after page load (e.g., in Suite Setup after
        Open Dashboard).
        """
        browser = self._get_browser()
        result = browser.evaluate_javascript(None, _OVERLAY_FIX_JS)
        self._applied = True
        logger.info(f"Overlay fix: {result}")

    @keyword("Overlay Fix Should Be Applied")
    def overlay_fix_should_be_applied(self):
        """Verify the overlay fix CSS is present in the page.

        Raises:
            AssertionError: If the overlay fix style tag is not found.
        """
        browser = self._get_browser()
        result = browser.evaluate_javascript(
            None,
            "() => !!document.getElementById('rf-overlay-fix')"
        )
        if not result:
            raise AssertionError(
                "Overlay fix CSS not found — call 'Inject Overlay Fix' first"
            )

    @keyword("Dismiss Active Overlays")
    def dismiss_active_overlays(self):
        """Force-dismiss any active Vuetify overlay dialogs.

        Unlike the CSS fix (which prevents future overlays from blocking),
        this actively closes any currently-open overlay by pressing Escape.
        Use when a dialog or menu is unexpectedly open.
        """
        browser = self._get_browser()
        browser.keyboard_key("press", "Escape")
        logger.info("Pressed Escape to dismiss active overlays")
