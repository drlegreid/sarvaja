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
import httpx

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


def _is_test_artifact(entity_id: str) -> bool:
    """Return True if entity_id is a CRUD test artifact (not a real governance rule).

    Test artifacts: TEST-9A3E0F65, TEST-00534A6E-SORT-A (uuid-based)
    Real rules: TEST-BUGFIX-01-v1, TEST-DISCOVERY-01-v1 (semantic IDs)
    """
    if not entity_id.startswith("TEST-"):
        return False
    # Real semantic IDs have version suffix like -v1, -v2
    if "-v" in entity_id.split("TEST-", 1)[1]:
        return False
    return True


def cleanup_test_entities(base_url: str = API_BASE_URL) -> dict:
    """Remove all TEST-* test artifacts from the database.

    Paginates through all pages. Skips real governance rules with TEST- prefix
    (e.g. TEST-BUGFIX-01-v1). Returns counts of cleaned entities per type.
    """
    cleaned = {"tasks": 0, "rules": 0, "sessions": 0}
    client = httpx.Client(base_url=base_url, timeout=30.0)
    try:
        # Cleanup tasks — collect all IDs first, then delete
        # (offset pagination shifts during deletion, so collect-then-delete is safer)
        try:
            test_task_ids = []
            offset = 0
            while True:
                resp = client.get("/api/tasks", params={"limit": 200, "offset": offset})
                if resp.status_code != 200:
                    break
                data = resp.json()
                tasks = data.get("items", data) if isinstance(data, dict) else data
                if not tasks:
                    break
                for task in tasks:
                    task_id = task.get("task_id", "")
                    if _is_test_artifact(task_id):
                        test_task_ids.append(task_id)
                pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
                if not pagination.get("has_more", False):
                    break
                offset += len(tasks)
            for task_id in test_task_ids:
                if client.delete(f"/api/tasks/{task_id}").status_code == 204:
                    cleaned["tasks"] += 1
        except Exception as e:
            print(f"Task cleanup error: {e}")

        # Cleanup rules
        try:
            resp = client.get("/api/rules")
            if resp.status_code == 200:
                data = resp.json()
                rules = data.get("items", data) if isinstance(data, dict) else data
                for rule in rules:
                    rule_id = rule.get("id", "")
                    if _is_test_artifact(rule_id):
                        if client.delete(
                            f"/api/rules/{rule_id}",
                            params={"archive": "false"},
                        ).status_code == 204:
                            cleaned["rules"] += 1
        except Exception as e:
            print(f"Rule cleanup error: {e}")

        # Cleanup sessions — end only, preserve history
        try:
            resp = client.get("/api/sessions")
            if resp.status_code == 200:
                data = resp.json()
                sessions = data.get("items", data) if isinstance(data, dict) else data
                for session in sessions:
                    session_id = session.get("session_id", "")
                    if _is_test_artifact(session_id):
                        try:
                            client.put(f"/api/sessions/{session_id}/end")
                            cleaned["sessions"] += 1
                        except Exception:
                            pass
        except Exception as e:
            print(f"Session cleanup error: {e}")
    finally:
        client.close()

    return cleaned


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data_global():
    """Session-scoped cleanup that removes TEST-* entities before and after all E2E tests."""
    pre = cleanup_test_entities()
    if sum(pre.values()) > 0:
        print(f"\n[Pre-test cleanup] Removed: {pre}")

    yield

    post = cleanup_test_entities()
    if sum(post.values()) > 0:
        print(f"\n[Post-test cleanup] Removed: {post}")


@pytest.fixture
def dashboard_url():
    """Return the dashboard URL."""
    return DASHBOARD_URL


@pytest.fixture
def api_url():
    """Return the API URL."""
    return API_URL


# JS snippet that injects a <style> to disable Vuetify overlay pointer events.
# Trame/Vuetify creates .v-overlay-container elements that intercept clicks
# even when no modal is open.  Idempotent — checks for existing tag by id.
_INJECT_OVERLAY_FIX_JS = """() => {
    if (!document.getElementById('e2e-overlay-fix')) {
        const s = document.createElement('style');
        s.id = 'e2e-overlay-fix';
        s.textContent = `
            .v-overlay-container,
            .v-overlay-container *,
            .v-overlay__scrim {
                pointer-events: none !important;
            }
        `;
        document.head.appendChild(s);
    }
}"""

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

    @pytest.fixture(autouse=True)
    def dismiss_vuetify_overlays(page: Page):
        """Inject CSS to disable Vuetify overlay pointer interception.

        Runs automatically for every Playwright E2E test. Hooks into
        framenavigated so the fix re-applies after SPA route changes
        and page.goto() calls.
        """
        def _on_navigate(frame):
            if frame == frame.page.main_frame:
                try:
                    frame.page.evaluate(_INJECT_OVERLAY_FIX_JS)
                except Exception:
                    pass  # Page may be closing

        page.on("framenavigated", _on_navigate)
        yield page

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
