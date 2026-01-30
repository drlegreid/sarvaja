"""
E2E Test Configuration
======================
Per GAP-TEST-001: BDD paradigm for E2E tests.
Per TEST-001: Test framework reusability.
Per RULE-023: Test Before Ship.

Provides shared configuration for all E2E tests including:
- Playwright fixtures (optional - skip if not installed)
- BDD step imports
- Test data factories
"""

import pytest

# Optional pytest-playwright import - not required for API-only tests
try:
    import pytest_playwright  # noqa: F401
    from playwright.sync_api import Page
    HAS_PLAYWRIGHT = True
except ImportError:
    Page = None  # type: ignore
    HAS_PLAYWRIGHT = False

from shared.constants import APP_TITLE, DASHBOARD_URL, API_BASE_URL

# Re-export for backward compatibility
API_URL = API_BASE_URL


@pytest.fixture
def dashboard_url():
    """Return the dashboard URL."""
    return DASHBOARD_URL


@pytest.fixture
def api_url():
    """Return the API URL."""
    return API_URL


# Playwright-dependent fixtures (only defined if playwright is installed)
if HAS_PLAYWRIGHT:
    @pytest.fixture(scope="session")
    def browser_context_args(browser_context_args):
        """Configure browser context for all tests."""
        return {
            **browser_context_args,
            "viewport": {"width": 1280, "height": 720},
            "ignore_https_errors": True,
        }

    @pytest.fixture
    def authenticated_page(page: Page, dashboard_url: str):
        """Page fixture with dashboard loaded and authenticated."""
        page.goto(dashboard_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=15000)
        return page


# ============== Test Data Factories ==============

class RuleFactory:
    """Factory for creating test rule data."""

    _counter = 0

    @classmethod
    def create(cls, **overrides):
        """Create a test rule dict with defaults."""
        cls._counter += 1
        defaults = {
            "rule_id": f"RULE-TEST-{cls._counter:03d}",
            "name": f"Test Rule {cls._counter}",
            "category": "technical",
            "priority": "MEDIUM",
            "directive": f"Test directive {cls._counter}",
            "status": "ACTIVE",
        }
        return {**defaults, **overrides}


class TaskFactory:
    """Factory for creating test task data."""

    _counter = 0

    @classmethod
    def create(cls, **overrides):
        """Create a test task dict with defaults."""
        cls._counter += 1
        defaults = {
            "task_id": f"TASK-TEST-{cls._counter:03d}",
            "name": f"Test Task {cls._counter}",
            "status": "pending",
            "priority": "MEDIUM",
            "phase": "TEST",
        }
        return {**defaults, **overrides}


class AgentFactory:
    """Factory for creating test agent data."""

    _counter = 0

    @classmethod
    def create(cls, **overrides):
        """Create a test agent dict with defaults."""
        cls._counter += 1
        defaults = {
            "agent_id": f"agent-test-{cls._counter:03d}",
            "name": f"Test Agent {cls._counter}",
            "agent_type": "test-agent",
            "trust_score": 0.8,
        }
        return {**defaults, **overrides}


@pytest.fixture
def rule_factory():
    """Provide RuleFactory for tests."""
    return RuleFactory


@pytest.fixture
def task_factory():
    """Provide TaskFactory for tests."""
    return TaskFactory


@pytest.fixture
def agent_factory():
    """Provide AgentFactory for tests."""
    return AgentFactory


# ============== Page Objects (Playwright-dependent) ==============

if HAS_PLAYWRIGHT:
    class DashboardPage:
        """Page object for the main dashboard."""

        def __init__(self, page: Page):
            self.page = page
            self.url = DASHBOARD_URL

        def navigate(self):
            """Navigate to the dashboard."""
            self.page.goto(self.url)
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_selector(f"text={APP_TITLE}", timeout=15000)

        def click_nav(self, tab: str):
            """Click a navigation tab."""
            self.page.click(f"[data-testid='nav-{tab.lower()}']")
            self.page.wait_for_load_state("networkidle")

        def get_header_text(self) -> str:
            """Get the header text."""
            return self.page.locator("h1").first.text_content()

    class RulesPage:
        """Page object for the Rules view."""

        def __init__(self, page: Page):
            self.page = page

        def get_rule_count(self) -> int:
            """Get the number of rules loaded."""
            text = self.page.locator("text=/\\d+ rules loaded/").text_content()
            return int(text.split()[0])

        def click_add_rule(self):
            """Click the Add Rule button."""
            self.page.click("text=Add Rule")

        def click_rule(self, rule_id: str):
            """Click on a specific rule."""
            self.page.click(f"text={rule_id}")

        def search_rules(self, query: str):
            """Search for rules."""
            self.page.fill("input[placeholder*='Search']", query)
            self.page.wait_for_load_state("networkidle")

    @pytest.fixture
    def dashboard_page(page: Page):
        """Provide DashboardPage instance."""
        return DashboardPage(page)

    @pytest.fixture
    def rules_page(page: Page):
        """Provide RulesPage instance."""
        return RulesPage(page)
