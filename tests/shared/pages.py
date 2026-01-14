"""
Page Object Models
==================
Per TEST-001: Test framework reusability.
Per RD-TESTING-STRATEGY: UI Page Objects mirror component structure.

Page objects provide:
- Locators that match data-testid
- Actions that mirror UI components
- Assertions for common checks
"""

from typing import Optional, List
from playwright.sync_api import Page, expect


DASHBOARD_URL = "http://localhost:8081"
API_URL = "http://localhost:8082"


class BasePage:
    """Base page object with common functionality."""

    def __init__(self, page: Page):
        self.page = page
        self.url = DASHBOARD_URL

    def navigate(self, path: str = ""):
        """Navigate to a URL path."""
        self.page.goto(f"{self.url}{path}")
        self.page.wait_for_load_state("networkidle")

    def wait_for_text(self, text: str, timeout: int = 10000):
        """Wait for text to appear."""
        self.page.wait_for_selector(f"text={text}", timeout=timeout)

    def click_text(self, text: str):
        """Click on text."""
        self.page.click(f"text={text}")

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return self.page.locator(selector).is_visible()


class DashboardPage(BasePage):
    """
    Page object for the main dashboard.

    Mirrors: agent/governance_ui/views/main_view.py
    """

    # Navigation selectors (data-testid)
    NAV_RULES = "[data-testid='nav-rules']"
    NAV_AGENTS = "[data-testid='nav-agents']"
    NAV_TASKS = "[data-testid='nav-tasks']"
    NAV_SESSIONS = "[data-testid='nav-sessions']"
    NAV_TRUST = "[data-testid='nav-trust']"
    NAV_INFRA = "[data-testid='nav-infra']"

    def navigate_home(self):
        """Navigate to dashboard home."""
        self.navigate()
        self.wait_for_text("Sim.ai Governance Dashboard")

    def click_nav(self, tab: str):
        """Click a navigation tab."""
        selector = getattr(self, f"NAV_{tab.upper()}", None)
        if selector:
            self.page.click(selector)
        else:
            self.click_text(tab)
        self.page.wait_for_load_state("networkidle")

    def get_header_stats(self) -> str:
        """Get header stats text (e.g., '45 Rules | 9 Decisions')."""
        return self.page.locator("text=/\\d+ Rules \\| \\d+ Decisions/").text_content()

    def assert_navigation_visible(self):
        """Assert all navigation tabs are visible."""
        expect(self.page.locator(self.NAV_RULES)).to_be_visible()
        expect(self.page.locator(self.NAV_AGENTS)).to_be_visible()
        expect(self.page.locator(self.NAV_TASKS)).to_be_visible()


class RulesPage(BasePage):
    """
    Page object for the Rules view.

    Mirrors: agent/governance_ui/views/rules_view.py
    """

    # Selectors
    ADD_RULE_BTN = "text=Add Rule"
    SEARCH_INPUT = "input[placeholder*='Search']"
    RULE_LIST = "listitem"

    def navigate_to_rules(self):
        """Navigate to rules view."""
        dashboard = DashboardPage(self.page)
        dashboard.navigate_home()
        dashboard.click_nav("Rules")
        self.wait_for_text("Governance Rules")

    def get_rule_count(self) -> int:
        """Get the number of rules loaded."""
        text = self.page.locator("text=/\\d+ rules loaded/").text_content()
        return int(text.split()[0])

    def click_add_rule(self):
        """Click the Add Rule button."""
        self.page.click(self.ADD_RULE_BTN)

    def search_rules(self, query: str):
        """Search for rules."""
        self.page.fill(self.SEARCH_INPUT, query)
        self.page.wait_for_load_state("networkidle")

    def click_first_rule(self):
        """Click the first rule in the list."""
        self.page.locator(self.RULE_LIST).first.click()

    def click_rule(self, rule_id: str):
        """Click on a specific rule."""
        self.click_text(rule_id)

    def assert_rule_detail_visible(self):
        """Assert rule detail view is visible."""
        expect(self.page.locator("text=Directive")).to_be_visible()
        expect(self.page.locator("text=Edit")).to_be_visible()
        expect(self.page.locator("text=Delete")).to_be_visible()


class TasksPage(BasePage):
    """
    Page object for the Tasks view.

    Mirrors: agent/governance_ui/views/tasks_view.py
    """

    ADD_TASK_BTN = "text=Add Task"
    STATUS_BADGES = "text=/TODO|DONE|IN_PROGRESS|pending/"

    def navigate_to_tasks(self):
        """Navigate to tasks view."""
        dashboard = DashboardPage(self.page)
        dashboard.navigate_home()
        dashboard.click_nav("Tasks")
        self.wait_for_text("Platform Tasks")

    def get_task_count(self) -> int:
        """Get the number of tasks loaded."""
        text = self.page.locator("text=/\\d+ tasks loaded/").text_content()
        return int(text.split()[0])

    def assert_status_badges_visible(self):
        """Assert task status badges are visible."""
        expect(self.page.locator(self.STATUS_BADGES).first).to_be_visible()


class TrustPage(BasePage):
    """
    Page object for the Trust Dashboard view.

    Mirrors: agent/governance_ui/views/trust_view.py
    """

    def navigate_to_trust(self):
        """Navigate to trust view."""
        dashboard = DashboardPage(self.page)
        dashboard.navigate_home()
        dashboard.click_nav("Trust")
        self.wait_for_text("Agent Trust Dashboard")

    def assert_stats_visible(self):
        """Assert trust stats are visible."""
        expect(self.page.locator("text=Total Agents")).to_be_visible()
        expect(self.page.locator("text=Avg Trust Score")).to_be_visible()


class InfraPage(BasePage):
    """
    Page object for the Infrastructure Health view.

    Mirrors: agent/governance_ui/views/infra_view.py
    """

    # Selectors
    CARD_TYPEDB = "[data-testid='infra-card-typedb']"
    CARD_CHROMADB = "[data-testid='infra-card-chromadb']"
    REFRESH_BTN = "[data-testid='infra-refresh-btn']"
    START_ALL_BTN = "[data-testid='infra-start-all']"
    RESTART_BTN = "[data-testid='infra-restart']"
    CLEANUP_BTN = "[data-testid='infra-cleanup']"

    def navigate_to_infra(self):
        """Navigate to infrastructure view."""
        dashboard = DashboardPage(self.page)
        dashboard.navigate_home()
        dashboard.click_nav("Infra")
        self.wait_for_text("Infrastructure Health")

    def click_refresh(self):
        """Click the refresh button."""
        self.page.click(self.REFRESH_BTN)

    def assert_service_cards_visible(self):
        """Assert service status cards are visible."""
        expect(self.page.locator(self.CARD_TYPEDB)).to_be_visible()
        expect(self.page.locator(self.CARD_CHROMADB)).to_be_visible()

    def assert_recovery_buttons_visible(self):
        """Assert recovery action buttons are visible."""
        expect(self.page.locator(self.START_ALL_BTN)).to_be_visible()
        expect(self.page.locator(self.RESTART_BTN)).to_be_visible()
