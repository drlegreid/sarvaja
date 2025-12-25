"""
Decisions Page Object - Strategic Decisions browser.
Per RULE-004: Page Object Model (POM) Requirements
Per ENTITY-API-UI-MAP.md: Decision entity specification
"""
from .base_page import BasePage, Locator


class DecisionsPage(BasePage):
    """
    Page Object for Decisions List.

    Expected operations per ENTITY-API-UI-MAP.md:
    - LIST: View all decisions with columns [decision_id, title, date, status]
    - READ: Click decision to view detail (context, rationale, impacts)
    """

    LOCATORS = {
        **BasePage.LOCATORS,

        # List view
        'decisions_list_title': Locator(text='Decisions'),
        'decisions_table': Locator(css='table'),
        'decision_row': Locator(css='tr'),

        # Columns (decision_id visible per exploration)
        'col_decision_id': Locator(data_testid='decision-id'),
        'col_title': Locator(data_testid='decision-title'),
        'col_date': Locator(data_testid='decision-date'),
        'col_status': Locator(css='.badge'),

        # Detail view - GAP-UI-003: Missing
        'detail_context': Locator(data_testid='decision-context'),
        'detail_rationale': Locator(data_testid='decision-rationale'),
        'detail_impacts': Locator(data_testid='decision-impacts'),
    }

    def navigate_to_decisions(self) -> None:
        """Navigate to decisions list view."""
        self.click_nav_tab('Decisions')

    def get_decisions_count(self) -> int:
        """Get number of decisions in the list."""
        return 0

    def click_decision(self, decision_id: str) -> None:
        """Click on a decision to view detail."""
        # GAP-UI-007: Not clickable
        pass

    def get_decision_by_id(self, decision_id: str) -> dict:
        """Get decision data by ID."""
        return {}
