"""
Sessions Page Object - Session browser.
Per RULE-004: Page Object Model (POM) Requirements
Per ENTITY-API-UI-MAP.md: Session entity specification
"""
from .base_page import BasePage, Locator


class SessionsPage(BasePage):
    """
    Page Object for Sessions Browser.

    Expected operations per ENTITY-API-UI-MAP.md:
    - LIST: View all sessions with [session_id, date, summary]
    - READ: Click session to view timeline, evidence, decisions
    """

    LOCATORS = {
        **BasePage.LOCATORS,

        # List view
        'sessions_list_title': Locator(text='Sessions'),
        'sessions_table': Locator(css='table'),
        'session_row': Locator(css='tr'),

        # Columns
        'col_session_id': Locator(data_testid='session-id'),
        'col_date': Locator(data_testid='session-date'),
        'col_summary': Locator(data_testid='session-summary'),

        # Detail view - GAP-UI-003: Missing
        'detail_timeline': Locator(data_testid='session-timeline'),
        'detail_evidence': Locator(data_testid='session-evidence'),
        'detail_decisions': Locator(data_testid='session-decisions'),
    }

    def navigate_to_sessions(self) -> None:
        """Navigate to sessions list view."""
        self.click_nav_tab('Sessions')

    def get_sessions_count(self) -> int:
        """Get number of sessions in the list."""
        return 0

    def click_session(self, session_id: str) -> None:
        """Click on a session to view detail."""
        # GAP-UI-007: Not clickable
        pass
