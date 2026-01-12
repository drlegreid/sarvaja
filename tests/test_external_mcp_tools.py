"""
Tests for External MCP Tools - Phase 5 Integration
===================================================
Tests for Playwright, PowerShell, Desktop Commander, and OctoCode wrappers.

Per RULE-001 (Session Evidence Logging).
Per RULE-007 (MCP Tool Matrix).
"""

import pytest
import json
from agent.external_mcp_tools import (
    # Config classes
    PlaywrightConfig,
    PowerShellConfig,
    DesktopCommanderConfig,
    OctoCodeConfig,
    # Toolkit classes
    PlaywrightTools,
    PowerShellTools,
    DesktopCommanderTools,
    OctoCodeTools,
    ExternalMCPTools,
    # Convenience functions
    get_all_external_tools,
    get_web_automation_tools,
    get_devops_tools,
    get_file_tools,
    get_code_research_tools,
    # Module-level flag
    AGNO_AVAILABLE,
)


def call_tool(tools, method_name, *args, **kwargs):
    """
    Call a tool method, handling both agno and stub cases.

    When agno is available, methods are wrapped in Function objects
    and must be called via their entrypoint.
    When using the stub, methods are directly callable.
    """
    method = getattr(tools, method_name)

    # Check if this is an agno Function object
    if hasattr(method, 'entrypoint'):
        # Agno case: call entrypoint with self bound
        return method.entrypoint(tools, *args, **kwargs)
    else:
        # Stub case: direct call
        return method(*args, **kwargs)


def is_tool_callable(method):
    """
    Check if a method is callable as a tool.

    For agno Functions, check if entrypoint is callable.
    For stubs, check if method is directly callable.
    """
    if hasattr(method, 'entrypoint'):
        return callable(method.entrypoint)
    return callable(method)


def is_valid_tool(method):
    """
    Check if a method is a valid registered tool.

    For agno Functions, check for 'name' attribute.
    For stubs, check for '_is_tool' attribute or callable.
    """
    if hasattr(method, 'name') and hasattr(method, 'entrypoint'):
        return True  # Agno Function
    if hasattr(method, '_is_tool'):
        return True  # Stub with marker
    return callable(method)


# =============================================================================
# P5.1: PLAYWRIGHT TOOLS TESTS
# =============================================================================

class TestPlaywrightConfig:
    """Tests for PlaywrightConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PlaywrightConfig()
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.timeout_ms == 30000

    def test_custom_config(self):
        """Test custom configuration."""
        config = PlaywrightConfig(
            browser_type="firefox",
            headless=False,
            timeout_ms=60000
        )
        assert config.browser_type == "firefox"
        assert config.headless is False
        assert config.timeout_ms == 60000


class TestPlaywrightTools:
    """Tests for PlaywrightTools toolkit."""

    def test_toolkit_creation(self):
        """Test toolkit can be created."""
        tools = PlaywrightTools()
        assert tools.name == "playwright"
        assert tools.config is not None

    def test_toolkit_with_config(self):
        """Test toolkit with custom config."""
        config = PlaywrightConfig(browser_type="webkit")
        tools = PlaywrightTools(config=config)
        assert tools.config.browser_type == "webkit"

    def test_tool_registration(self):
        """Test all tools are registered."""
        tools = PlaywrightTools()
        expected_tools = [
            "navigate", "snapshot", "click", "type_text",
            "screenshot", "evaluate", "wait_for"
        ]
        for tool_name in expected_tools:
            assert tool_name in tools.functions

    def test_navigate_tool(self):
        """Test navigate tool returns valid JSON."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'navigate', url="https://example.com")
        parsed = json.loads(result)
        assert parsed["action"] == "navigate"
        assert parsed["url"] == "https://example.com"
        assert parsed["status"] == "simulated"

    def test_snapshot_tool(self):
        """Test snapshot tool returns valid JSON."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'snapshot', filename="test.md")
        parsed = json.loads(result)
        assert parsed["action"] == "snapshot"
        assert parsed["filename"] == "test.md"

    def test_click_tool(self):
        """Test click tool returns valid JSON."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'click', element="Submit button", ref="btn-submit")
        parsed = json.loads(result)
        assert parsed["action"] == "click"
        assert parsed["element"] == "Submit button"
        assert parsed["ref"] == "btn-submit"

    def test_type_text_tool(self):
        """Test type_text tool returns valid JSON."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'type_text', element="Username field", ref="input-user", text="admin", submit=True)
        parsed = json.loads(result)
        assert parsed["action"] == "type"
        assert parsed["text"] == "admin"
        assert parsed["submit"] is True

    def test_screenshot_tool(self):
        """Test screenshot tool returns valid JSON."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'screenshot', filename="page.png", full_page=True)
        parsed = json.loads(result)
        assert parsed["action"] == "screenshot"
        assert parsed["full_page"] is True

    def test_evaluate_tool(self):
        """Test evaluate tool returns valid JSON."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'evaluate', function="() => document.title")
        parsed = json.loads(result)
        assert parsed["action"] == "evaluate"
        assert parsed["function"] == "() => document.title"

    def test_wait_for_text(self):
        """Test wait_for with text."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'wait_for', text="Loading complete")
        parsed = json.loads(result)
        assert parsed["action"] == "wait"
        assert parsed["text"] == "Loading complete"

    def test_wait_for_time(self):
        """Test wait_for with time."""
        tools = PlaywrightTools()
        result = call_tool(tools, 'wait_for', time=5)
        parsed = json.loads(result)
        assert parsed["time"] == 5


# =============================================================================
# P5.2: POWERSHELL TOOLS TESTS
# =============================================================================

class TestPowerShellConfig:
    """Tests for PowerShellConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PowerShellConfig()
        assert config.timeout == 300
        assert config.working_directory is None

    def test_custom_config(self):
        """Test custom configuration."""
        config = PowerShellConfig(timeout=600, working_directory="C:\\Scripts")
        assert config.timeout == 600
        assert config.working_directory == "C:\\Scripts"


class TestPowerShellTools:
    """Tests for PowerShellTools toolkit."""

    def test_toolkit_creation(self):
        """Test toolkit can be created."""
        tools = PowerShellTools()
        assert tools.name == "powershell"

    def test_tool_registration(self):
        """Test all tools are registered."""
        tools = PowerShellTools()
        assert "run_script" in tools.functions
        assert "run_command" in tools.functions

    def test_run_script_tool(self):
        """Test run_script tool returns valid JSON."""
        tools = PowerShellTools()
        code = "Get-Process | Select-Object -First 5"
        result = call_tool(tools, 'run_script', code=code)
        parsed = json.loads(result)
        assert parsed["action"] == "run_script"
        assert parsed["code_length"] == len(code)
        assert parsed["timeout"] == 300  # Default

    def test_run_script_with_timeout(self):
        """Test run_script with custom timeout."""
        tools = PowerShellTools()
        result = call_tool(tools, 'run_script', code="Get-Date", timeout=60)
        parsed = json.loads(result)
        assert parsed["timeout"] == 60

    def test_run_command_tool(self):
        """Test run_command wraps run_script."""
        tools = PowerShellTools()
        result = call_tool(tools, 'run_command', command="Get-Location")
        parsed = json.loads(result)
        assert parsed["action"] == "run_script"


# =============================================================================
# P5.3: DESKTOP COMMANDER TOOLS TESTS
# =============================================================================

class TestDesktopCommanderConfig:
    """Tests for DesktopCommanderConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DesktopCommanderConfig()
        assert config.allowed_directories is None
        assert config.file_read_limit == 1000

    def test_custom_config(self):
        """Test custom configuration."""
        config = DesktopCommanderConfig(
            allowed_directories=["C:\\Projects", "D:\\Data"],
            file_read_limit=500
        )
        assert len(config.allowed_directories) == 2
        assert config.file_read_limit == 500


class TestDesktopCommanderTools:
    """Tests for DesktopCommanderTools toolkit."""

    def test_toolkit_creation(self):
        """Test toolkit can be created."""
        tools = DesktopCommanderTools()
        assert tools.name == "desktop_commander"

    def test_tool_registration(self):
        """Test all tools are registered."""
        tools = DesktopCommanderTools()
        expected_tools = [
            "read_file", "write_file", "list_directory",
            "search_files", "get_file_info", "create_directory", "move_file"
        ]
        for tool_name in expected_tools:
            assert tool_name in tools.functions

    def test_read_file_tool(self):
        """Test read_file tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'read_file', path="C:\\test.txt", offset=10, length=50)
        parsed = json.loads(result)
        assert parsed["action"] == "read_file"
        assert parsed["path"] == "C:\\test.txt"
        assert parsed["offset"] == 10
        assert parsed["length"] == 50

    def test_write_file_tool(self):
        """Test write_file tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'write_file', path="C:\\output.txt", content="Hello World", mode="append")
        parsed = json.loads(result)
        assert parsed["action"] == "write_file"
        assert parsed["content_length"] == 11
        assert parsed["mode"] == "append"

    def test_list_directory_tool(self):
        """Test list_directory tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'list_directory', path="C:\\Projects", depth=1)
        parsed = json.loads(result)
        assert parsed["action"] == "list_directory"
        assert parsed["path"] == "C:\\Projects"
        assert parsed["depth"] == 1

    def test_search_files_tool(self):
        """Test search_files tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'search_files', path="C:\\Code", pattern="*.py", search_type="files")
        parsed = json.loads(result)
        assert parsed["action"] == "search"
        assert parsed["pattern"] == "*.py"
        assert parsed["search_type"] == "files"

    def test_search_content(self):
        """Test search_files for content."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'search_files', path="C:\\Code", pattern="TODO", search_type="content")
        parsed = json.loads(result)
        assert parsed["search_type"] == "content"

    def test_get_file_info_tool(self):
        """Test get_file_info tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'get_file_info', path="C:\\test.txt")
        parsed = json.loads(result)
        assert parsed["action"] == "get_file_info"
        assert parsed["path"] == "C:\\test.txt"

    def test_create_directory_tool(self):
        """Test create_directory tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'create_directory', path="C:\\NewFolder")
        parsed = json.loads(result)
        assert parsed["action"] == "create_directory"
        assert parsed["path"] == "C:\\NewFolder"

    def test_move_file_tool(self):
        """Test move_file tool returns valid JSON."""
        tools = DesktopCommanderTools()
        result = call_tool(tools, 'move_file', source="C:\\old.txt", destination="C:\\new.txt")
        parsed = json.loads(result)
        assert parsed["action"] == "move_file"
        assert parsed["source"] == "C:\\old.txt"
        assert parsed["destination"] == "C:\\new.txt"


# =============================================================================
# P5.4: OCTOCODE TOOLS TESTS
# =============================================================================

class TestOctoCodeConfig:
    """Tests for OctoCodeConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OctoCodeConfig()
        assert config.default_limit == 10
        assert config.include_minified is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = OctoCodeConfig(default_limit=5, include_minified=False)
        assert config.default_limit == 5
        assert config.include_minified is False


class TestOctoCodeTools:
    """Tests for OctoCodeTools toolkit."""

    def test_toolkit_creation(self):
        """Test toolkit can be created."""
        tools = OctoCodeTools()
        assert tools.name == "octocode"

    def test_tool_registration(self):
        """Test all tools are registered."""
        tools = OctoCodeTools()
        expected_tools = [
            "search_code", "get_file_content", "view_repo_structure",
            "search_repositories", "search_pull_requests"
        ]
        for tool_name in expected_tools:
            assert tool_name in tools.functions

    def test_search_code_tool(self):
        """Test search_code tool returns valid JSON."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'search_code', keywords="useState", owner="facebook", repo="react", match="file")
        parsed = json.loads(result)
        assert parsed["action"] == "search_code"
        assert parsed["keywords"] == "useState"
        assert parsed["owner"] == "facebook"
        assert parsed["repo"] == "react"
        assert parsed["match"] == "file"

    def test_search_code_no_owner(self):
        """Test search_code without owner/repo."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'search_code', keywords="authentication")
        parsed = json.loads(result)
        assert parsed["owner"] is None
        assert parsed["repo"] is None

    def test_get_file_content_tool(self):
        """Test get_file_content tool returns valid JSON."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'get_file_content',
            owner="anthropics",
            repo="claude-code",
            path="README.md",
            branch="main"
        )
        parsed = json.loads(result)
        assert parsed["action"] == "get_file_content"
        assert parsed["owner"] == "anthropics"
        assert parsed["repo"] == "claude-code"
        assert parsed["path"] == "README.md"
        assert parsed["branch"] == "main"

    def test_get_file_content_with_match(self):
        """Test get_file_content with match_string."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'get_file_content',
            owner="test",
            repo="repo",
            path="file.py",
            match_string="def main"
        )
        parsed = json.loads(result)
        assert parsed["match_string"] == "def main"

    def test_view_repo_structure_tool(self):
        """Test view_repo_structure tool returns valid JSON."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'view_repo_structure',
            owner="microsoft",
            repo="vscode",
            branch="main",
            path="src",
            depth=2
        )
        parsed = json.loads(result)
        assert parsed["action"] == "view_structure"
        assert parsed["owner"] == "microsoft"
        assert parsed["repo"] == "vscode"
        assert parsed["path"] == "src"
        assert parsed["depth"] == 2

    def test_search_repositories_tool(self):
        """Test search_repositories tool returns valid JSON."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'search_repositories',
            keywords="machine learning",
            topics="python,ai",
            stars=">1000",
            limit=5
        )
        parsed = json.loads(result)
        assert parsed["action"] == "search_repos"
        assert parsed["keywords"] == "machine learning"
        assert parsed["topics"] == "python,ai"
        assert parsed["stars"] == ">1000"
        assert parsed["limit"] == 5

    def test_search_pull_requests_tool(self):
        """Test search_pull_requests tool returns valid JSON."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'search_pull_requests',
            owner="drlegreid",
            repo="platform-gai",
            query="fix bug",
            state="closed",
            limit=3
        )
        parsed = json.loads(result)
        assert parsed["action"] == "search_prs"
        assert parsed["owner"] == "drlegreid"
        assert parsed["repo"] == "platform-gai"
        assert parsed["query"] == "fix bug"
        assert parsed["state"] == "closed"

    def test_search_pull_requests_open(self):
        """Test search_pull_requests for open PRs."""
        tools = OctoCodeTools()
        result = call_tool(tools, 'search_pull_requests', state="open")
        parsed = json.loads(result)
        assert parsed["state"] == "open"


# =============================================================================
# COMBINED TOOLKIT TESTS
# =============================================================================

class TestExternalMCPTools:
    """Tests for ExternalMCPTools combined toolkit."""

    def test_combined_toolkit_creation(self):
        """Test combined toolkit can be created."""
        tools = ExternalMCPTools()
        assert tools.name == "external_mcp"

    def test_all_toolkits_enabled(self):
        """Test all toolkits enabled by default."""
        tools = ExternalMCPTools()
        assert "playwright" in tools.enabled_toolkits
        assert "powershell" in tools.enabled_toolkits
        assert "desktop_commander" in tools.enabled_toolkits
        assert "octocode" in tools.enabled_toolkits

    def test_selective_toolkits(self):
        """Test selective toolkit enabling."""
        tools = ExternalMCPTools(
            enable_playwright=True,
            enable_powershell=False,
            enable_desktop_commander=False,
            enable_octocode=True
        )
        assert "playwright" in tools.enabled_toolkits
        assert "powershell" not in tools.enabled_toolkits
        assert "desktop_commander" not in tools.enabled_toolkits
        assert "octocode" in tools.enabled_toolkits

    def test_prefixed_tool_names(self):
        """Test tools have prefixed names."""
        tools = ExternalMCPTools()
        # Check for prefixed tools
        assert "playwright_navigate" in tools.functions
        assert "powershell_run_script" in tools.functions
        assert "desktop_commander_read_file" in tools.functions
        assert "octocode_search_code" in tools.functions

    def test_total_tool_count(self):
        """Test total number of registered tools."""
        tools = ExternalMCPTools()
        # Playwright: 7, PowerShell: 2, Desktop Commander: 7, OctoCode: 5 = 21
        assert len(tools.functions) == 21

    def test_disabled_toolkit_not_registered(self):
        """Test disabled toolkit tools not registered."""
        tools = ExternalMCPTools(enable_powershell=False)
        assert "powershell_run_script" not in tools.functions
        assert "playwright_navigate" in tools.functions  # Still enabled


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_all_external_tools(self):
        """Test get_all_external_tools returns all toolkits."""
        toolkits = get_all_external_tools()
        assert len(toolkits) == 4
        names = [t.name for t in toolkits]
        assert "playwright" in names
        assert "powershell" in names
        assert "desktop_commander" in names
        assert "octocode" in names

    def test_get_web_automation_tools(self):
        """Test get_web_automation_tools returns PlaywrightTools."""
        tools = get_web_automation_tools()
        assert isinstance(tools, PlaywrightTools)
        assert tools.name == "playwright"

    def test_get_devops_tools(self):
        """Test get_devops_tools returns PowerShellTools."""
        tools = get_devops_tools()
        assert isinstance(tools, PowerShellTools)
        assert tools.name == "powershell"

    def test_get_file_tools(self):
        """Test get_file_tools returns DesktopCommanderTools."""
        tools = get_file_tools()
        assert isinstance(tools, DesktopCommanderTools)
        assert tools.name == "desktop_commander"

    def test_get_code_research_tools(self):
        """Test get_code_research_tools returns OctoCodeTools."""
        tools = get_code_research_tools()
        assert isinstance(tools, OctoCodeTools)
        assert tools.name == "octocode"


# =============================================================================
# MODULE-LEVEL TESTS
# =============================================================================

class TestModuleLevel:
    """Tests for module-level attributes."""

    def test_agno_available_flag(self):
        """Test AGNO_AVAILABLE flag exists."""
        assert isinstance(AGNO_AVAILABLE, bool)

    def test_stub_decorator_when_no_agno(self):
        """Test stub decorator marks functions."""
        tools = PlaywrightTools()
        # Check that navigate has been decorated (agno Function or stub)
        assert is_valid_tool(tools.navigate)


# =============================================================================
# JSON OUTPUT VALIDATION TESTS
# =============================================================================

class TestJsonOutputFormat:
    """Tests for JSON output format consistency."""

    def test_all_tools_return_valid_json(self):
        """Test all tools return parseable JSON."""
        tools_to_test = [
            (PlaywrightTools(), [
                ("navigate", {"url": "https://test.com"}),
                ("snapshot", {}),
                ("click", {"element": "btn", "ref": "r1"}),
                ("type_text", {"element": "inp", "ref": "r2", "text": "hi"}),
                ("screenshot", {}),
                ("evaluate", {"function": "() => 1"}),
                ("wait_for", {"time": 1}),
            ]),
            (PowerShellTools(), [
                ("run_script", {"code": "Get-Date"}),
                ("run_command", {"command": "ls"}),
            ]),
            (DesktopCommanderTools(), [
                ("read_file", {"path": "C:\\t.txt"}),
                ("write_file", {"path": "C:\\t.txt", "content": "x"}),
                ("list_directory", {"path": "C:\\"}),
                ("search_files", {"path": "C:\\", "pattern": "*"}),
                ("get_file_info", {"path": "C:\\t.txt"}),
                ("create_directory", {"path": "C:\\new"}),
                ("move_file", {"source": "C:\\a", "destination": "C:\\b"}),
            ]),
            (OctoCodeTools(), [
                ("search_code", {"keywords": "test"}),
                ("get_file_content", {"owner": "o", "repo": "r", "path": "p"}),
                ("view_repo_structure", {"owner": "o", "repo": "r"}),
                ("search_repositories", {}),
                ("search_pull_requests", {}),
            ]),
        ]

        for toolkit, tool_calls in tools_to_test:
            for tool_name, kwargs in tool_calls:
                result = call_tool(toolkit, tool_name, **kwargs)
                # Should not raise
                parsed = json.loads(result)
                assert "status" in parsed, f"{tool_name} missing status"
                assert parsed["status"] == "simulated"

    def test_all_results_have_action_field(self):
        """Test all results include action field."""
        toolkit = PlaywrightTools()
        result = call_tool(toolkit, 'navigate', url="https://example.com")
        parsed = json.loads(result)
        assert "action" in parsed

    def test_all_results_have_message_field(self):
        """Test all results include message field."""
        toolkit = DesktopCommanderTools()
        result = call_tool(toolkit, 'read_file', path="C:\\test.txt")
        parsed = json.loads(result)
        assert "message" in parsed


# =============================================================================
# INTEGRATION TESTS (SKIPPED WITHOUT AGNO)
# =============================================================================

@pytest.mark.skipif(not AGNO_AVAILABLE, reason="Agno not available")
class TestAgnoIntegration:
    """Integration tests requiring Agno."""

    def test_toolkit_inheritance(self):
        """Test toolkits inherit from real Toolkit."""
        from agno.tools import Toolkit as RealToolkit
        tools = PlaywrightTools()
        assert isinstance(tools, RealToolkit)

    def test_tool_decorator_applied(self):
        """Test @tool decorator applied correctly."""
        tools = PlaywrightTools()
        # Check navigate is an agno Function with entrypoint
        assert hasattr(tools.navigate, 'entrypoint'), "navigate should be an agno Function"
        assert hasattr(tools.navigate, 'name'), "navigate Function should have name"
        assert callable(tools.navigate.entrypoint), "entrypoint should be callable"


# =============================================================================
# TOOL MATRIX COMPLIANCE (RULE-007)
# =============================================================================

class TestToolMatrixCompliance:
    """Tests for RULE-007 Tool Matrix compliance."""

    def test_tier_1_tools_present(self):
        """Test Tier 1 tools (required) are present."""
        # Playwright is Tier 1
        tools = PlaywrightTools()
        assert len(tools.functions) >= 5

    def test_tier_2_tools_present(self):
        """Test Tier 2 tools (recommended) are present."""
        # PowerShell, Desktop Commander, OctoCode are Tier 2
        ps = PowerShellTools()
        dc = DesktopCommanderTools()
        oc = OctoCodeTools()

        assert len(ps.functions) >= 2
        assert len(dc.functions) >= 5
        assert len(oc.functions) >= 4
