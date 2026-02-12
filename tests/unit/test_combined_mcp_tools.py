"""
Unit tests for Combined External MCP Toolkit.

Per DOC-SIZE-01-v1: Tests for agent/external_mcp/combined.py module.
Tests: ExternalMCPTools (init, enable/disable, prefixed names),
       factory functions (get_all_external_tools, get_web_automation_tools, etc.).
"""

from agent.external_mcp.combined import (
    ExternalMCPTools,
    get_all_external_tools,
    get_web_automation_tools,
    get_devops_tools,
    get_file_tools,
    get_code_research_tools,
)


# ── ExternalMCPTools ───────────────────────────────────────


class TestExternalMCPToolsInit:
    def test_default_all_enabled(self):
        tools = ExternalMCPTools()
        assert tools.name == "external_mcp"
        assert len(tools._toolkits) == 4

    def test_enabled_toolkits_list(self):
        tools = ExternalMCPTools()
        names = tools.enabled_toolkits
        assert "playwright" in names
        assert "powershell" in names
        assert "desktop_commander" in names
        assert "octocode" in names

    def test_prefixed_function_names(self):
        tools = ExternalMCPTools()
        # Functions should be prefixed with toolkit name
        fn_names = list(tools.functions.keys())
        assert any(n.startswith("playwright_") for n in fn_names)
        assert any(n.startswith("powershell_") for n in fn_names)
        assert any(n.startswith("desktop_commander_") for n in fn_names)
        assert any(n.startswith("octocode_") for n in fn_names)

    def test_has_all_sub_tools(self):
        tools = ExternalMCPTools()
        # 5 playwright + 5 powershell + 7 desktop_commander + 5 octocode = 22
        assert len(tools.functions) >= 20


class TestExternalMCPToolsDisable:
    def test_disable_playwright(self):
        tools = ExternalMCPTools(enable_playwright=False)
        assert "playwright" not in tools.enabled_toolkits
        assert not any(n.startswith("playwright_") for n in tools.functions)

    def test_disable_powershell(self):
        tools = ExternalMCPTools(enable_powershell=False)
        assert "powershell" not in tools.enabled_toolkits

    def test_disable_desktop_commander(self):
        tools = ExternalMCPTools(enable_desktop_commander=False)
        assert "desktop_commander" not in tools.enabled_toolkits

    def test_disable_octocode(self):
        tools = ExternalMCPTools(enable_octocode=False)
        assert "octocode" not in tools.enabled_toolkits

    def test_disable_all(self):
        tools = ExternalMCPTools(
            enable_playwright=False,
            enable_powershell=False,
            enable_desktop_commander=False,
            enable_octocode=False,
        )
        assert len(tools._toolkits) == 0
        assert len(tools.functions) == 0

    def test_enable_only_one(self):
        tools = ExternalMCPTools(
            enable_playwright=False,
            enable_powershell=False,
            enable_desktop_commander=False,
            enable_octocode=True,
        )
        assert len(tools._toolkits) == 1
        assert tools.enabled_toolkits == ["octocode"]
        assert all(n.startswith("octocode_") for n in tools.functions)


# ── Factory functions ──────────────────────────────────────


class TestFactoryFunctions:
    def test_get_all_external_tools(self):
        toolkits = get_all_external_tools()
        assert len(toolkits) == 4
        names = [t.name for t in toolkits]
        assert "playwright" in names
        assert "powershell" in names
        assert "desktop_commander" in names
        assert "octocode" in names

    def test_get_web_automation_tools(self):
        tools = get_web_automation_tools()
        assert tools.name == "playwright"

    def test_get_devops_tools(self):
        tools = get_devops_tools()
        assert tools.name == "powershell"

    def test_get_file_tools(self):
        tools = get_file_tools()
        assert tools.name == "desktop_commander"

    def test_get_code_research_tools(self):
        tools = get_code_research_tools()
        assert tools.name == "octocode"
