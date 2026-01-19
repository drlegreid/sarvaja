"""
BDD Step Definitions - Shared Fixtures
======================================
Per GAP-TEST-001: BDD paradigm for E2E tests.
Per TEST-001: Test framework reusability.

Provides shared fixtures for all BDD step definitions.
"""

import pytest

# Skip if pytest-playwright not available (container environment)
pytest.importorskip("pytest_playwright", reason="pytest-playwright required - run locally")

from playwright.sync_api import Page, Browser, BrowserContext

from shared.constants import APP_TITLE, DASHBOARD_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture
def dashboard_url():
    """Return the dashboard URL."""
    return DASHBOARD_URL


@pytest.fixture
def page_with_dashboard(page: Page, dashboard_url: str):
    """Page fixture with dashboard loaded."""
    page.goto(dashboard_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
    return page
