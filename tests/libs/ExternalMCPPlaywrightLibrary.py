"""
Robot Framework Library for External MCP Playwright Tools Tests.

Per: RULE-007 (MCP Tool Matrix), DOC-SIZE-01-v1.
Split from tests/test_external_mcp_tools.py
"""
import json
from pathlib import Path
from robot.api.deco import keyword


def call_tool(tools, method_name, *args, **kwargs):
    """Call a tool method, handling both agno and stub cases."""
    method = getattr(tools, method_name)
    if hasattr(method, 'entrypoint'):
        return method.entrypoint(tools, *args, **kwargs)
    else:
        return method(*args, **kwargs)


class ExternalMCPPlaywrightLibrary:
    """Library for Playwright tools tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # PlaywrightConfig Tests
    # =========================================================================

    @keyword("Playwright Default Config")
    def playwright_default_config(self):
        """Test default configuration values."""
        try:
            from agent.external_mcp_tools import PlaywrightConfig
            config = PlaywrightConfig()
            return {
                "browser_chromium": config.browser_type == "chromium",
                "headless_true": config.headless is True,
                "timeout_30000": config.timeout_ms == 30000
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Playwright Custom Config")
    def playwright_custom_config(self):
        """Test custom configuration."""
        try:
            from agent.external_mcp_tools import PlaywrightConfig
            config = PlaywrightConfig(
                browser_type="firefox",
                headless=False,
                timeout_ms=60000
            )
            return {
                "browser_firefox": config.browser_type == "firefox",
                "headless_false": config.headless is False,
                "timeout_60000": config.timeout_ms == 60000
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # PlaywrightTools Tests
    # =========================================================================

    @keyword("Playwright Toolkit Creation")
    def playwright_toolkit_creation(self):
        """Test toolkit can be created."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            return {
                "name_correct": tools.name == "playwright",
                "config_exists": tools.config is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Playwright Toolkit With Config")
    def playwright_toolkit_with_config(self):
        """Test toolkit with custom config."""
        try:
            from agent.external_mcp_tools import PlaywrightConfig, PlaywrightTools
            config = PlaywrightConfig(browser_type="webkit")
            tools = PlaywrightTools(config=config)
            return {
                "browser_webkit": tools.config.browser_type == "webkit"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Playwright Tool Registration")
    def playwright_tool_registration(self):
        """Test all tools are registered."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            expected_tools = [
                "navigate", "snapshot", "click", "type_text",
                "screenshot", "evaluate", "wait_for"
            ]
            results = {}
            for tool_name in expected_tools:
                results[f"{tool_name}_registered"] = tool_name in tools.functions
            return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Playwright Navigate Tool")
    def playwright_navigate_tool(self):
        """Test navigate tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'navigate', url="https://example.com")
            parsed = json.loads(result)
            return {
                "action_navigate": parsed["action"] == "navigate",
                "url_correct": parsed["url"] == "https://example.com",
                "status_simulated": parsed["status"] == "simulated"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Snapshot Tool")
    def playwright_snapshot_tool(self):
        """Test snapshot tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'snapshot', filename="test.md")
            parsed = json.loads(result)
            return {
                "action_snapshot": parsed["action"] == "snapshot",
                "filename_correct": parsed["filename"] == "test.md"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Click Tool")
    def playwright_click_tool(self):
        """Test click tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'click', element="Submit button", ref="btn-submit")
            parsed = json.loads(result)
            return {
                "action_click": parsed["action"] == "click",
                "element_correct": parsed["element"] == "Submit button",
                "ref_correct": parsed["ref"] == "btn-submit"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Type Text Tool")
    def playwright_type_text_tool(self):
        """Test type_text tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'type_text', element="Username field", ref="input-user", text="admin", submit=True)
            parsed = json.loads(result)
            return {
                "action_type": parsed["action"] == "type",
                "text_correct": parsed["text"] == "admin",
                "submit_true": parsed["submit"] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Screenshot Tool")
    def playwright_screenshot_tool(self):
        """Test screenshot tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'screenshot', filename="page.png", full_page=True)
            parsed = json.loads(result)
            return {
                "action_screenshot": parsed["action"] == "screenshot",
                "full_page_true": parsed["full_page"] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Evaluate Tool")
    def playwright_evaluate_tool(self):
        """Test evaluate tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'evaluate', function="() => document.title")
            parsed = json.loads(result)
            return {
                "action_evaluate": parsed["action"] == "evaluate",
                "function_correct": parsed["function"] == "() => document.title"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Wait For Text")
    def playwright_wait_for_text(self):
        """Test wait_for with text."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'wait_for', text="Loading complete")
            parsed = json.loads(result)
            return {
                "action_wait": parsed["action"] == "wait",
                "text_correct": parsed["text"] == "Loading complete"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Playwright Wait For Time")
    def playwright_wait_for_time(self):
        """Test wait_for with time."""
        try:
            from agent.external_mcp_tools import PlaywrightTools
            tools = PlaywrightTools()
            result = call_tool(tools, 'wait_for', time=5)
            parsed = json.loads(result)
            return {
                "time_correct": parsed["time"] == 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}
