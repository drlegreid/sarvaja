# Page Objects Package
# Per RULE-004: Page Object Model (POM) Requirements
"""
Page Object Model structure for Sarvaja Governance Dashboard.

Each page object encapsulates:
- Locators (data-testid selectors)
- Actions (click, fill, submit)
- Assertions (verification methods)

Usage in Robot Framework:
    Import Library    pages.RulesPage
    ${page}=    RulesPage
    ${page}.navigate()
    ${page}.click_rule("RULE-001")
"""
from .base_page import BasePage
from .rules_page import RulesPage
from .decisions_page import DecisionsPage
from .sessions_page import SessionsPage

__all__ = ['BasePage', 'RulesPage', 'DecisionsPage', 'SessionsPage']
