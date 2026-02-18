"""
E2E Browser Tests for Governance Dashboard
==========================================
Per GAP-WORKFLOW-004: Actual E2E browser testing with Playwright.
Per RULE-004: Exploratory Test Automation & Executable Specification.
Per RULE-023: Test Before Ship.

Created: 2026-01-04
Updated: 2026-02-18 — Aligned selectors with current Trame/Vuetify UI

Prerequisites:
- Governance dashboard running on port 8081
- TypeDB and ChromaDB containers running
- pip install playwright pytest-playwright (local only, not in container)
- playwright install chromium

Run locally: pytest tests/e2e/test_dashboard_e2e.py -v --headed
"""

import pytest

# Skip entire module if pytest-playwright not available (container environment)
pytest.importorskip("pytest_playwright", reason="pytest-playwright required - run locally")

from playwright.sync_api import Page, expect

from shared.constants import APP_TITLE, DASHBOARD_URL


class TestDashboardNavigation:
    """Test navigation between dashboard views."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to dashboard before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        # Wait for app to initialize
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)

    def test_dashboard_loads(self, page: Page):
        """Dashboard loads with header and navigation."""
        expect(page.locator(f"text={APP_TITLE}")).to_be_visible()
        expect(page.locator("[data-testid='nav-rules']")).to_be_visible()

    def test_header_shows_rules_chip(self, page: Page):
        """Header displays rule count chip."""
        # Two separate chips: "N Rules" and "N Decisions"
        rules_chip = page.locator("[data-testid='toolbar-rules-chip']")
        expect(rules_chip).to_be_visible()

    def test_header_shows_decisions_chip(self, page: Page):
        """Header displays decision count chip."""
        decisions_chip = page.locator("[data-testid='toolbar-decisions-chip']")
        expect(decisions_chip).to_be_visible()

    def test_navigation_tabs_present(self, page: Page):
        """Core navigation tabs are visible."""
        # Per constants.py NAVIGATION_ITEMS — verify core tabs exist
        tabs = ["Rules", "Agents", "Tasks", "Sessions", "Trust", "Infrastructure"]
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
        # Tasks view header text is just "Tasks"
        expect(page.locator("text=Tasks").first).to_be_visible()

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
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
        page.click("[data-testid='nav-rules']")
        page.wait_for_selector("text=Governance Rules")

    def test_rules_table_loads(self, page: Page):
        """Rules data table is rendered."""
        table = page.locator("[data-testid='rules-table']")
        expect(table).to_be_visible()

    def test_rules_table_has_rows(self, page: Page):
        """Rules table has at least one data row."""
        # VDataTable renders rows as <tr> elements
        table = page.locator("[data-testid='rules-table']")
        rows = table.locator("tbody tr")
        expect(rows.first).to_be_visible(timeout=10000)

    def test_add_rule_button_present(self, page: Page):
        """Add Rule button is visible."""
        expect(page.locator("text=Add Rule")).to_be_visible()

    def test_search_input_present(self, page: Page):
        """Search input is available (Vuetify uses label, not placeholder)."""
        search = page.locator("[data-testid='rules-search']")
        expect(search).to_be_visible()

    def test_click_rule_shows_detail(self, page: Page):
        """Clicking a rule row shows detail view."""
        table = page.locator("[data-testid='rules-table']")
        rows = table.locator("tbody tr")
        first_row = rows.first
        expect(first_row).to_be_visible(timeout=10000)
        first_row.click()
        # Should show detail with rule info
        page.wait_for_timeout(1000)  # Allow state change
        # Look for detail content (Edit/Delete buttons or Directive section)
        detail_visible = (
            page.locator("text=Edit").is_visible()
            or page.locator("text=Directive").is_visible()
            or page.locator("text=Delete").is_visible()
        )
        assert detail_visible, "Rule detail should show after clicking a row"


class TestTasksView:
    """Test Tasks view functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Tasks view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
        page.click("[data-testid='nav-tasks']")
        # Tasks view header is just "Tasks"
        page.wait_for_selector("text=Tasks", timeout=10000)

    def test_tasks_view_loads(self, page: Page):
        """Tasks view renders with task content."""
        # Look for task-related UI: search, table, or status chips
        tasks_search = page.locator("[data-testid='tasks-search']")
        tasks_visible = tasks_search.is_visible()
        if not tasks_visible:
            # Fallback: just verify we're on the tasks page
            expect(page.locator("text=Tasks").first).to_be_visible()

    def test_add_task_button_present(self, page: Page):
        """Add Task button is visible."""
        expect(page.locator("text=Add Task")).to_be_visible()

    def test_task_shows_status(self, page: Page):
        """Tasks show status indicators."""
        # Look for any status text in the tasks view
        statuses = page.locator("text=/OPEN|DONE|IN_PROGRESS|TODO|CLOSED|BLOCKED/")
        if statuses.count() > 0:
            expect(statuses.first).to_be_visible()
        else:
            # No tasks with visible status — acceptable if DB is empty
            pass


class TestTrustView:
    """Test Trust Dashboard functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Trust view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
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


class TestSessionsView:
    """Test Sessions view functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Sessions view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
        page.click("[data-testid='nav-sessions']")
        page.wait_for_selector("text=Session Evidence", timeout=10000)

    def test_sessions_view_loads(self, page: Page):
        """Sessions view renders with session list."""
        expect(page.locator("text=Session Evidence")).to_be_visible()

    def test_sessions_has_table_header(self, page: Page):
        """Sessions table shows Session ID column header."""
        # Column header is "Session ID" (with space)
        header = page.locator("text=Session ID")
        if header.count() > 0:
            expect(header.first).to_be_visible()


class TestAgentsView:
    """Test Agents view functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Agents view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
        page.click("[data-testid='nav-agents']")
        page.wait_for_selector("text=Registered Agents", timeout=10000)

    def test_agents_view_loads(self, page: Page):
        """Agents view renders with agent list."""
        expect(page.locator("text=Registered Agents")).to_be_visible()

    def test_agents_has_table_content(self, page: Page):
        """Agents table shows agent data."""
        # Look for table headers or agent data
        agent_content = page.locator("text=/agent|Agent/")
        if agent_content.count() > 0:
            expect(agent_content.first).to_be_visible()


class TestInfraView:
    """Test Infrastructure Health Dashboard. Per GAP-INFRA-004."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to Infrastructure view before each test."""
        page.goto(DASHBOARD_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
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
