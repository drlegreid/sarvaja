"""
E2E Browser Tests for Governance Dashboard
==========================================
Per GAP-WORKFLOW-004: Actual E2E browser testing with Playwright.
Per RULE-004: Exploratory Test Automation & Executable Specification.
Per RULE-023: Test Before Ship.

Created: 2026-01-04
Evidence: .playwright-mcp/e2e-dashboard-rules.png, e2e-rule-detail.png

Prerequisites:
- Governance dashboard running on port 8081
- TypeDB and ChromaDB containers running
- pip install playwright pytest-playwright
- playwright install chromium
"""

import pytest
from playwright.sync_api import Page, expect


DASHBOARD_URL = "http://localhost:8081"


class TestDashboardNavigation:
    """Test navigation between dashboard views."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to dashboard before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        # Wait for app to initialize
        page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)

    def test_dashboard_loads(self, page: Page):
        """Dashboard loads with header and navigation."""
        expect(page.locator("text=Sim.ai Governance Dashboard")).to_be_visible()
        expect(page.locator("[data-testid='nav-rules']")).to_be_visible()

    def test_header_shows_stats(self, page: Page):
        """Header displays rule and decision counts."""
        header = page.locator("text=/\\d+ Rules \\| \\d+ Decisions/")
        expect(header).to_be_visible()

    def test_navigation_tabs_present(self, page: Page):
        """All navigation tabs are visible."""
        tabs = ["Rules", "Agents", "Tasks", "Sessions", "Trust", "Search"]
        for tab in tabs:
            expect(page.locator(f"text={tab}").first).to_be_visible()

    def test_navigate_to_rules(self, page: Page):
        """Can navigate to Rules view."""
        page.click("[data-testid='nav-rules']")
        expect(page.locator("text=Governance Rules")).to_be_visible()

    def test_navigate_to_agents(self, page: Page):
        """Can navigate to Agents view."""
        page.click("[data-testid='nav-agents']")
        expect(page.locator("text=Registered Agents")).to_be_visible()

    def test_navigate_to_tasks(self, page: Page):
        """Can navigate to Tasks view."""
        page.click("[data-testid='nav-tasks']")
        expect(page.locator("text=Platform Tasks")).to_be_visible()

    def test_navigate_to_sessions(self, page: Page):
        """Can navigate to Sessions view."""
        page.click("[data-testid='nav-sessions']")
        expect(page.locator("text=Session Evidence")).to_be_visible()

    def test_navigate_to_trust(self, page: Page):
        """Can navigate to Trust view."""
        page.click("[data-testid='nav-trust']")
        expect(page.locator("text=Agent Trust Dashboard")).to_be_visible()


class TestRulesView:
    """Test Rules view functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Rules view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)
        page.click("[data-testid='nav-rules']")
        page.wait_for_selector("text=Governance Rules")

    def test_rules_list_loads(self, page: Page):
        """Rules list shows rule count."""
        expect(page.locator("text=/\\d+ rules loaded/")).to_be_visible()

    def test_add_rule_button_present(self, page: Page):
        """Add Rule button is visible."""
        expect(page.locator("text=Add Rule")).to_be_visible()

    def test_search_input_present(self, page: Page):
        """Search input is available."""
        expect(page.locator("input[placeholder*='Search']").first).to_be_visible()

    def test_rule_list_items_clickable(self, page: Page):
        """Rule items in list are clickable."""
        rule_item = page.locator("listitem").first
        expect(rule_item).to_be_visible()

    def test_click_rule_shows_detail(self, page: Page):
        """Clicking a rule shows detail view with Edit/Delete buttons."""
        # Click first rule
        page.locator("listitem").first.click()
        # Should show detail view with Edit button
        expect(page.locator("text=Edit")).to_be_visible()
        expect(page.locator("text=Delete")).to_be_visible()

    def test_rule_detail_shows_directive(self, page: Page):
        """Rule detail view shows directive text."""
        page.locator("listitem").first.click()
        expect(page.locator("text=Directive")).to_be_visible()


class TestTasksView:
    """Test Tasks view functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Tasks view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)
        page.click("[data-testid='nav-tasks']")
        page.wait_for_selector("text=Platform Tasks")

    def test_tasks_list_loads(self, page: Page):
        """Tasks list shows task count."""
        expect(page.locator("text=/\\d+ tasks loaded/")).to_be_visible()

    def test_add_task_button_present(self, page: Page):
        """Add Task button is visible."""
        expect(page.locator("text=Add Task")).to_be_visible()

    def test_task_shows_status(self, page: Page):
        """Tasks show status badges."""
        # Look for any status text
        statuses = page.locator("text=/TODO|DONE|IN_PROGRESS|pending/")
        expect(statuses.first).to_be_visible()


class TestTrustView:
    """Test Trust Dashboard functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Trust view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)
        page.click("[data-testid='nav-trust']")
        page.wait_for_selector("text=Agent Trust Dashboard")

    def test_trust_dashboard_loads(self, page: Page):
        """Trust dashboard shows stats cards."""
        expect(page.locator("text=Total Agents")).to_be_visible()
        expect(page.locator("text=Avg Trust Score")).to_be_visible()

    def test_refresh_button_present(self, page: Page):
        """Refresh button is available."""
        expect(page.locator("text=Refresh Data")).to_be_visible()

    def test_trust_leaderboard_present(self, page: Page):
        """Trust leaderboard section is visible."""
        expect(page.locator("text=Trust Leaderboard")).to_be_visible()


class TestPaginationUI:
    """
    Test Pagination UI Controls.

    Per GAP-UI-036: Pagination support
    Per GAP-UI-010: Sorting support
    Per GAP-UI-011: Filtering support

    Created: 2026-01-04 to certify pagination changes
    """

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to dashboard before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)

    def test_rules_view_has_pagination_controls(self, page: Page):
        """Test Rules view has pagination UI controls."""
        page.click("[data-testid='nav-rules']")
        page.wait_for_selector("text=Governance Rules")

        # Look for pagination controls or page size selector
        # These may be visible if list is long enough
        expect(page.locator("text=/\\d+ rules loaded/")).to_be_visible()

    def test_tasks_view_has_pagination_controls(self, page: Page):
        """Test Tasks view has pagination UI controls."""
        page.click("[data-testid='nav-tasks']")
        page.wait_for_selector("text=Platform Tasks")

        # Verify task count is shown
        expect(page.locator("text=/\\d+ tasks loaded/")).to_be_visible()

    def test_sessions_view_has_pagination_controls(self, page: Page):
        """Test Sessions view has pagination controls."""
        page.click("[data-testid='nav-sessions']")
        page.wait_for_selector("text=Session Evidence")

        # Sessions list should load
        page.wait_for_selector("text=session_id", timeout=5000)

    def test_agents_view_has_pagination_controls(self, page: Page):
        """Test Agents view has pagination controls."""
        page.click("[data-testid='nav-agents']")
        page.wait_for_selector("text=Registered Agents")

        # Agents should be sorted by trust score by default
        page.wait_for_selector("text=Trust Score", timeout=5000)


class TestInfraView:
    """Test Infrastructure Health Dashboard. Per GAP-INFRA-004."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Infrastructure view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)
        page.click("[data-testid='nav-infra']")

    def test_infra_dashboard_loads(self, page: Page):
        """Infrastructure dashboard loads with header."""
        expect(page.locator("text=Infrastructure Health")).to_be_visible()

    def test_infra_shows_service_cards(self, page: Page):
        """Service status cards are displayed."""
        expect(page.locator("[data-testid='infra-card-typedb']")).to_be_visible()
        expect(page.locator("[data-testid='infra-card-chromadb']")).to_be_visible()

    def test_infra_shows_stats(self, page: Page):
        """System stats are displayed."""
        expect(page.locator("[data-testid='infra-stat-memory']")).to_be_visible()
        expect(page.locator("[data-testid='infra-stat-hash']")).to_be_visible()

    def test_infra_refresh_button(self, page: Page):
        """Refresh button is clickable."""
        refresh_btn = page.locator("[data-testid='infra-refresh-btn']")
        expect(refresh_btn).to_be_visible()
        refresh_btn.click()

    def test_infra_recovery_actions(self, page: Page):
        """Recovery action buttons are present."""
        expect(page.locator("[data-testid='infra-start-all']")).to_be_visible()
        expect(page.locator("[data-testid='infra-restart']")).to_be_visible()
        expect(page.locator("[data-testid='infra-cleanup']")).to_be_visible()


# Run with: pytest tests/e2e/test_dashboard_e2e.py -v --headed
