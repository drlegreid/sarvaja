"""
Unit tests for Playwright MCP Tools.

Per DOC-SIZE-01-v1: Tests for agent/external_mcp/playwright.py.
Tests: PlaywrightConfig, PlaywrightTools — navigate, snapshot, click,
       type_text, screenshot, evaluate, wait_for.
"""

import json

from agent.external_mcp.playwright import PlaywrightTools, PlaywrightConfig


def _call(tools, name, **kwargs):
    """Call a tool through the agno Function entrypoint."""
    fn = tools.functions[name]
    return json.loads(fn.entrypoint(**kwargs))


# ── PlaywrightConfig ─────────────────────────────────────


class TestPlaywrightConfig:
    def test_defaults(self):
        cfg = PlaywrightConfig()
        assert cfg.browser_type == "chromium"
        assert cfg.headless is True
        assert cfg.timeout_ms == 30000

    def test_custom(self):
        cfg = PlaywrightConfig(browser_type="firefox", headless=False, timeout_ms=5000)
        assert cfg.browser_type == "firefox"
        assert cfg.headless is False


# ── PlaywrightTools Registration ─────────────────────────


class TestRegistration:
    def test_registers_seven_tools(self):
        tools = PlaywrightTools()
        assert len(tools.functions) == 7

    def test_tool_names(self):
        tools = PlaywrightTools()
        expected = {"navigate", "snapshot", "click", "type_text",
                    "screenshot", "evaluate", "wait_for"}
        assert set(tools.functions.keys()) == expected

    def test_default_config(self):
        tools = PlaywrightTools()
        assert tools.config.browser_type == "chromium"

    def test_custom_config(self):
        cfg = PlaywrightConfig(headless=False)
        tools = PlaywrightTools(config=cfg)
        assert tools.config.headless is False


# ── navigate ─────────────────────────────────────────────


class TestNavigate:
    def test_returns_json(self):
        tools = PlaywrightTools()
        result = _call(tools, "navigate", url="https://example.com")
        assert result["action"] == "navigate"
        assert result["url"] == "https://example.com"
        assert result["status"] == "simulated"


# ── snapshot ─────────────────────────────────────────────


class TestSnapshot:
    def test_without_filename(self):
        tools = PlaywrightTools()
        result = _call(tools, "snapshot")
        assert result["action"] == "snapshot"
        assert result["filename"] is None

    def test_with_filename(self):
        tools = PlaywrightTools()
        result = _call(tools, "snapshot", filename="page.html")
        assert result["filename"] == "page.html"


# ── click ────────────────────────────────────────────────


class TestClick:
    def test_click(self):
        tools = PlaywrightTools()
        result = _call(tools, "click", element="Login button", ref="ref123")
        assert result["action"] == "click"
        assert result["element"] == "Login button"
        assert result["ref"] == "ref123"


# ── type_text ────────────────────────────────────────────


class TestTypeText:
    def test_type(self):
        tools = PlaywrightTools()
        result = _call(tools, "type_text", element="Search box",
                        ref="ref456", text="hello")
        assert result["action"] == "type"
        assert result["text"] == "hello"
        assert result["submit"] is False

    def test_type_with_submit(self):
        tools = PlaywrightTools()
        result = _call(tools, "type_text", element="Search", ref="ref",
                        text="q", submit=True)
        assert result["submit"] is True


# ── screenshot ───────────────────────────────────────────


class TestScreenshot:
    def test_defaults(self):
        tools = PlaywrightTools()
        result = _call(tools, "screenshot")
        assert result["action"] == "screenshot"
        assert result["filename"] is None
        assert result["full_page"] is False

    def test_full_page(self):
        tools = PlaywrightTools()
        result = _call(tools, "screenshot", filename="page.png", full_page=True)
        assert result["full_page"] is True
        assert result["filename"] == "page.png"


# ── evaluate ─────────────────────────────────────────────


class TestEvaluate:
    def test_evaluate(self):
        tools = PlaywrightTools()
        result = _call(tools, "evaluate", function="document.title")
        assert result["action"] == "evaluate"
        assert result["function"] == "document.title"
        assert result["element"] is None

    def test_with_element(self):
        tools = PlaywrightTools()
        result = _call(tools, "evaluate", function="el.textContent", element="h1")
        assert result["element"] == "h1"


# ── wait_for ─────────────────────────────────────────────


class TestWaitFor:
    def test_wait_for_text(self):
        tools = PlaywrightTools()
        result = _call(tools, "wait_for", text="Loading complete")
        assert result["action"] == "wait"
        assert result["text"] == "Loading complete"

    def test_wait_for_time(self):
        tools = PlaywrightTools()
        result = _call(tools, "wait_for", time=5)
        assert result["time"] == 5
