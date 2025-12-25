"""
Base Page Object - Common functionality for all pages.
Per RULE-004: Page Object Model (POM) Requirements
Per UI-FIRST-SPRINT-WORKFLOW.md: Spec-First TDD

All page objects inherit from BasePage for:
- Common navigation
- Shared locators (header, nav, footer)
- Utility methods (wait, screenshot)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Locator:
    """Centralized locator with multiple selector strategies."""
    data_testid: Optional[str] = None
    css: Optional[str] = None
    role: Optional[str] = None
    text: Optional[str] = None

    def __str__(self) -> str:
        """Return best available selector."""
        if self.data_testid:
            return f'[data-testid="{self.data_testid}"]'
        if self.css:
            return self.css
        if self.role:
            return f'[role="{self.role}"]'
        if self.text:
            return f':has-text("{self.text}")'
        return ''


class BasePage:
    """
    Base Page Object with common functionality.

    All page objects inherit from this to get:
    - Shared locators (nav, header, footer)
    - Common actions (navigate, wait, screenshot)
    - Assertion helpers
    """

    BASE_URL = "http://localhost:8081"

    # Common locators (GAP-UI-001: Need data-testid attributes)
    LOCATORS = {
        # Header
        'header': Locator(css='header', role='banner'),
        'header_title': Locator(text='Sim.ai Governance Dashboard'),
        'header_stats': Locator(text='Rules'),

        # Navigation tabs
        'nav': Locator(css='nav', role='navigation'),
        'nav_rules': Locator(text='Rules'),
        'nav_decisions': Locator(text='Decisions'),
        'nav_sessions': Locator(text='Sessions'),
        'nav_tasks': Locator(text='Tasks'),
        'nav_search': Locator(text='Search'),

        # Main content area
        'main': Locator(css='main', role='main'),

        # Common UI components
        'loading_spinner': Locator(css='.loading, [role="progressbar"]'),
        'error_message': Locator(css='.error, [role="alert"]'),
        'empty_state': Locator(text='No data available'),

        # Table components
        'data_table': Locator(css='table', role='table'),
        'table_row': Locator(css='tr', role='row'),
        'table_cell': Locator(css='td', role='cell'),
        'pagination': Locator(css='nav[aria-label*="Pagination"]'),
    }

    def __init__(self, browser=None):
        """Initialize with optional browser instance."""
        self.browser = browser

    def get_locator(self, name: str) -> str:
        """Get locator by name."""
        locator = self.LOCATORS.get(name)
        if locator:
            return str(locator)
        raise ValueError(f"Unknown locator: {name}")

    def navigate(self) -> None:
        """Navigate to page URL."""
        # To be implemented with browser
        pass

    def wait_for_load(self, timeout: int = 30) -> None:
        """Wait for page to be fully loaded."""
        pass

    def take_screenshot(self, name: str) -> str:
        """Capture screenshot for evidence."""
        pass

    def is_loaded(self) -> bool:
        """Check if page is loaded."""
        return False

    def get_header_stats(self) -> dict:
        """Get stats from header (e.g., '11 Rules | 5 Decisions')."""
        return {'rules': 0, 'decisions': 0}

    def click_nav_tab(self, tab_name: str) -> None:
        """Click navigation tab by name."""
        pass

    def has_error(self) -> bool:
        """Check if error message is displayed."""
        return False

    def is_loading(self) -> bool:
        """Check if loading spinner is visible."""
        return False
