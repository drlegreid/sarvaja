"""
Unit tests for OctoCode MCP Tools.

Per DOC-SIZE-01-v1: Tests for agent/external_mcp/octocode.py module.
Tests: OctoCodeConfig, OctoCodeTools — search_code, get_file_content,
       view_repo_structure, search_repositories, search_pull_requests.
"""

import json

from agent.external_mcp.octocode import OctoCodeConfig, OctoCodeTools


def _call(tools, method_name, *args, **kwargs):
    """Call an agno-wrapped tool method via its entrypoint."""
    fn = getattr(tools, method_name)
    if hasattr(fn, "entrypoint"):
        return fn.entrypoint(tools, *args, **kwargs)
    return fn(*args, **kwargs)


# ── OctoCodeConfig ─────────────────────────────────────────


class TestOctoCodeConfig:
    def test_defaults(self):
        cfg = OctoCodeConfig()
        assert cfg.default_limit == 10
        assert cfg.include_minified is True

    def test_custom(self):
        cfg = OctoCodeConfig(default_limit=5, include_minified=False)
        assert cfg.default_limit == 5
        assert cfg.include_minified is False


# ── OctoCodeTools init ─────────────────────────────────────


class TestOctoCodeToolsInit:
    def test_default_config(self):
        tools = OctoCodeTools()
        assert tools.name == "octocode"
        assert tools.config.default_limit == 10

    def test_custom_config(self):
        cfg = OctoCodeConfig(default_limit=3)
        tools = OctoCodeTools(config=cfg)
        assert tools.config.default_limit == 3

    def test_registers_five_tools(self):
        tools = OctoCodeTools()
        assert len(tools.functions) == 5
        expected = {
            "search_code", "get_file_content", "view_repo_structure",
            "search_repositories", "search_pull_requests",
        }
        assert set(tools.functions.keys()) == expected


# ── search_code ────────────────────────────────────────────


class TestSearchCode:
    def test_basic_search(self):
        tools = OctoCodeTools()
        raw = _call(tools, "search_code", "def main")
        result = json.loads(raw)
        assert result["action"] == "search_code"
        assert result["keywords"] == "def main"
        assert result["status"] == "simulated"

    def test_with_owner_and_repo(self):
        tools = OctoCodeTools()
        raw = _call(tools, "search_code", "import", owner="org", repo="myrepo")
        result = json.loads(raw)
        assert result["owner"] == "org"
        assert result["repo"] == "myrepo"
        assert "org/myrepo" in result["message"]

    def test_match_path(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_code", "test", match="path"))
        assert result["match"] == "path"

    def test_custom_limit(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_code", "foo", limit=3))
        assert result["limit"] == 3

    def test_defaults(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_code", "x"))
        assert result["match"] == "file"
        assert result["limit"] == 10
        assert result["owner"] is None
        assert result["repo"] is None


# ── get_file_content ───────────────────────────────────────


class TestGetFileContent:
    def test_basic(self):
        tools = OctoCodeTools()
        raw = _call(tools, "get_file_content", "org", "repo", "src/main.py")
        result = json.loads(raw)
        assert result["action"] == "get_file_content"
        assert result["owner"] == "org"
        assert result["path"] == "src/main.py"

    def test_with_branch(self):
        tools = OctoCodeTools()
        result = json.loads(
            _call(tools, "get_file_content", "o", "r", "f.py", branch="dev")
        )
        assert result["branch"] == "dev"

    def test_with_match_string(self):
        tools = OctoCodeTools()
        result = json.loads(
            _call(tools, "get_file_content", "o", "r", "f.py", match_string="class Foo")
        )
        assert result["match_string"] == "class Foo"

    def test_defaults(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "get_file_content", "o", "r", "f.py"))
        assert result["branch"] is None
        assert result["match_string"] is None

    def test_message_format(self):
        tools = OctoCodeTools()
        result = json.loads(
            _call(tools, "get_file_content", "owner", "repo", "path.py")
        )
        assert "owner/repo/path.py" in result["message"]


# ── view_repo_structure ────────────────────────────────────


class TestViewRepoStructure:
    def test_basic(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "view_repo_structure", "org", "repo"))
        assert result["action"] == "view_structure"
        assert result["owner"] == "org"
        assert result["repo"] == "repo"

    def test_defaults(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "view_repo_structure", "o", "r"))
        assert result["branch"] == "main"
        assert result["path"] == ""
        assert result["depth"] == 1

    def test_custom_params(self):
        tools = OctoCodeTools()
        result = json.loads(
            _call(tools, "view_repo_structure", "o", "r", branch="dev", path="src", depth=2)
        )
        assert result["branch"] == "dev"
        assert result["path"] == "src"
        assert result["depth"] == 2


# ── search_repositories ───────────────────────────────────


class TestSearchRepositories:
    def test_by_keywords(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_repositories", keywords="governance"))
        assert result["action"] == "search_repos"
        assert result["keywords"] == "governance"

    def test_by_topics(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_repositories", topics="python,mcp"))
        assert result["topics"] == "python,mcp"

    def test_with_stars(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_repositories", stars=">1000"))
        assert result["stars"] == ">1000"

    def test_defaults(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_repositories"))
        assert result["keywords"] is None
        assert result["topics"] is None
        assert result["stars"] is None
        assert result["limit"] == 10

    def test_custom_limit(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_repositories", keywords="x", limit=5))
        assert result["limit"] == 5


# ── search_pull_requests ──────────────────────────────────


class TestSearchPullRequests:
    def test_basic(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_pull_requests", owner="org", repo="r"))
        assert result["action"] == "search_prs"
        assert result["owner"] == "org"

    def test_defaults(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_pull_requests"))
        assert result["state"] == "closed"
        assert result["limit"] == 5
        assert result["owner"] is None
        assert result["query"] is None

    def test_open_state(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_pull_requests", state="open"))
        assert result["state"] == "open"

    def test_with_query(self):
        tools = OctoCodeTools()
        result = json.loads(_call(tools, "search_pull_requests", query="fix bug"))
        assert result["query"] == "fix bug"
