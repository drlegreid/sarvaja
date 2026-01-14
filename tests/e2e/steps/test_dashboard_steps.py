"""
BDD Step Definitions - Dashboard Navigation
============================================
Per GAP-TEST-001: BDD paradigm for E2E tests.
Per RULE-004: Exploratory Test Automation & Executable Specification.

Step definitions for dashboard.feature scenarios.
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, expect


# Load all scenarios from the feature file
scenarios("../features/dashboard.feature")


DASHBOARD_URL = "http://localhost:8081"

# Map tab names to data-testid
TAB_SELECTORS = {
    "Rules": "[data-testid='nav-rules']",
    "Agents": "[data-testid='nav-agents']",
    "Tasks": "[data-testid='nav-tasks']",
    "Sessions": "[data-testid='nav-sessions']",
    "Trust": "[data-testid='nav-trust']",
    "Infra": "[data-testid='nav-infra']",
}


# ============== GIVEN Steps ==============

@given("the dashboard is running on port 8081")
def dashboard_running():
    """Verify dashboard is accessible."""
    # This is a precondition - actual verification happens in navigation
    pass


@given("the browser is open")
def browser_open(page: Page):
    """Browser fixture provided by pytest-playwright."""
    assert page is not None


# ============== WHEN Steps ==============

@when("I navigate to the dashboard")
def navigate_to_dashboard(page: Page):
    """Navigate to the dashboard home page."""
    page.goto(DASHBOARD_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_selector("text=Sim.ai Governance Dashboard", timeout=10000)


@when(parsers.parse('I click on "{tab}" navigation'))
def click_navigation_tab(page: Page, tab: str):
    """Click on a navigation tab."""
    selector = TAB_SELECTORS.get(tab)
    if selector:
        page.click(selector)
    else:
        # Fallback to text-based selector
        page.click(f"text={tab}")
    page.wait_for_load_state("networkidle")


@when("I click on the first rule in the list")
def click_first_rule(page: Page):
    """Click on the first rule in the rules list."""
    page.locator("listitem").first.click()
    page.wait_for_load_state("networkidle")


# ============== THEN Steps ==============

@then(parsers.parse('I should see "{text}"'))
def should_see_text(page: Page, text: str):
    """Verify text is visible on the page."""
    expect(page.locator(f"text={text}").first).to_be_visible()


@then("I should see the navigation menu")
def should_see_navigation_menu(page: Page):
    """Verify navigation menu is visible."""
    expect(page.locator("[data-testid='nav-rules']")).to_be_visible()


@then(parsers.parse('I should see "{button}" button'))
def should_see_button(page: Page, button: str):
    """Verify a button is visible."""
    expect(page.locator(f"text={button}").first).to_be_visible()


@then("I should see task status badges")
def should_see_task_status_badges(page: Page):
    """Verify task status badges are visible."""
    statuses = page.locator("text=/TODO|DONE|IN_PROGRESS|pending/")
    expect(statuses.first).to_be_visible()


@then("I should see service status cards")
def should_see_service_status_cards(page: Page):
    """Verify infrastructure service cards are visible."""
    expect(page.locator("[data-testid='infra-card-typedb']")).to_be_visible()
    expect(page.locator("[data-testid='infra-card-chromadb']")).to_be_visible()


@then("I should see recovery action buttons")
def should_see_recovery_action_buttons(page: Page):
    """Verify recovery action buttons are visible."""
    expect(page.locator("[data-testid='infra-start-all']")).to_be_visible()
    expect(page.locator("[data-testid='infra-restart']")).to_be_visible()
