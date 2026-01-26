"""
Robot Framework Library for External MCP OctoCode Tools Tests.

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


class ExternalMCPOctoCodeLibrary:
    """Library for OctoCode tools tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # OctoCodeConfig Tests
    # =========================================================================

    @keyword("OctoCode Default Config")
    def octocode_default_config(self):
        """Test default configuration values."""
        try:
            from agent.external_mcp_tools import OctoCodeConfig
            config = OctoCodeConfig()
            return {
                "default_limit_10": config.default_limit == 10,
                "include_minified_true": config.include_minified is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("OctoCode Custom Config")
    def octocode_custom_config(self):
        """Test custom configuration."""
        try:
            from agent.external_mcp_tools import OctoCodeConfig
            config = OctoCodeConfig(default_limit=5, include_minified=False)
            return {
                "default_limit_5": config.default_limit == 5,
                "include_minified_false": config.include_minified is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # OctoCodeTools Tests
    # =========================================================================

    @keyword("OctoCode Toolkit Creation")
    def octocode_toolkit_creation(self):
        """Test toolkit can be created."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            return {
                "name_correct": tools.name == "octocode"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("OctoCode Tool Registration")
    def octocode_tool_registration(self):
        """Test all tools are registered."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            expected_tools = [
                "search_code", "get_file_content", "view_repo_structure",
                "search_repositories", "search_pull_requests"
            ]
            results = {}
            for tool_name in expected_tools:
                results[f"{tool_name}_registered"] = tool_name in tools.functions
            return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("OctoCode Search Code Tool")
    def octocode_search_code_tool(self):
        """Test search_code tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'search_code', keywords="useState", owner="facebook", repo="react", match="file")
            parsed = json.loads(result)
            return {
                "action_search_code": parsed["action"] == "search_code",
                "keywords_correct": parsed["keywords"] == "useState",
                "owner_correct": parsed["owner"] == "facebook",
                "repo_correct": parsed["repo"] == "react",
                "match_file": parsed["match"] == "file"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode Search Code No Owner")
    def octocode_search_code_no_owner(self):
        """Test search_code without owner/repo."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'search_code', keywords="authentication")
            parsed = json.loads(result)
            return {
                "owner_none": parsed["owner"] is None,
                "repo_none": parsed["repo"] is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode Get File Content Tool")
    def octocode_get_file_content_tool(self):
        """Test get_file_content tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'get_file_content',
                owner="anthropics",
                repo="claude-code",
                path="README.md",
                branch="main"
            )
            parsed = json.loads(result)
            return {
                "action_get_file_content": parsed["action"] == "get_file_content",
                "owner_correct": parsed["owner"] == "anthropics",
                "repo_correct": parsed["repo"] == "claude-code",
                "path_correct": parsed["path"] == "README.md",
                "branch_main": parsed["branch"] == "main"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode Get File Content With Match")
    def octocode_get_file_content_with_match(self):
        """Test get_file_content with match_string."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'get_file_content',
                owner="test",
                repo="repo",
                path="file.py",
                match_string="def main"
            )
            parsed = json.loads(result)
            return {
                "match_string_correct": parsed["match_string"] == "def main"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode View Repo Structure Tool")
    def octocode_view_repo_structure_tool(self):
        """Test view_repo_structure tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'view_repo_structure',
                owner="microsoft",
                repo="vscode",
                branch="main",
                path="src",
                depth=2
            )
            parsed = json.loads(result)
            return {
                "action_view_structure": parsed["action"] == "view_structure",
                "owner_correct": parsed["owner"] == "microsoft",
                "repo_correct": parsed["repo"] == "vscode",
                "path_src": parsed["path"] == "src",
                "depth_2": parsed["depth"] == 2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode Search Repositories Tool")
    def octocode_search_repositories_tool(self):
        """Test search_repositories tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'search_repositories',
                keywords="machine learning",
                topics="python,ai",
                stars=">1000",
                limit=5
            )
            parsed = json.loads(result)
            return {
                "action_search_repos": parsed["action"] == "search_repos",
                "keywords_correct": parsed["keywords"] == "machine learning",
                "topics_correct": parsed["topics"] == "python,ai",
                "stars_correct": parsed["stars"] == ">1000",
                "limit_5": parsed["limit"] == 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode Search Pull Requests Tool")
    def octocode_search_pull_requests_tool(self):
        """Test search_pull_requests tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'search_pull_requests',
                owner="drlegreid",
                repo="platform-gai",
                query="fix bug",
                state="closed",
                limit=3
            )
            parsed = json.loads(result)
            return {
                "action_search_prs": parsed["action"] == "search_prs",
                "owner_correct": parsed["owner"] == "drlegreid",
                "repo_correct": parsed["repo"] == "platform-gai",
                "query_correct": parsed["query"] == "fix bug",
                "state_closed": parsed["state"] == "closed"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("OctoCode Search Pull Requests Open")
    def octocode_search_pull_requests_open(self):
        """Test search_pull_requests for open PRs."""
        try:
            from agent.external_mcp_tools import OctoCodeTools
            tools = OctoCodeTools()
            result = call_tool(tools, 'search_pull_requests', state="open")
            parsed = json.loads(result)
            return {
                "state_open": parsed["state"] == "open"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}
