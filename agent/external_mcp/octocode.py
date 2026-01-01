"""
OctoCode MCP Tools
==================
Agno Toolkit wrapping OctoCode MCP tools for code research.

Per RULE-007: OctoCode MCP is Tier 2 (recommended)
Per GAP-FILE-011: Extracted from external_mcp_tools.py

Created: 2024-12-28
"""

import json
from typing import Optional
from dataclasses import dataclass

from .common import tool, Toolkit


@dataclass
class OctoCodeConfig:
    """Configuration for OctoCode MCP tools."""
    default_limit: int = 10
    include_minified: bool = True


class OctoCodeTools(Toolkit):
    """
    Agno Toolkit wrapping OctoCode MCP tools for code research.

    Provides GitHub code search and analysis capabilities for agents.
    Per RULE-007: OctoCode MCP is Tier 2 (recommended).

    Available tools:
        - search_code: Search code in repositories
        - get_file_content: Get file content from GitHub
        - view_repo_structure: View repository structure
        - search_repositories: Search for repositories
        - search_pull_requests: Search pull requests
    """

    def __init__(self, config: Optional[OctoCodeConfig] = None):
        super().__init__(name="octocode")
        self.config = config or OctoCodeConfig()

        # Register tools
        self.register(self.search_code)
        self.register(self.get_file_content)
        self.register(self.view_repo_structure)
        self.register(self.search_repositories)
        self.register(self.search_pull_requests)

    @tool
    def search_code(
        self,
        keywords: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        match: str = "file",
        limit: int = 10
    ) -> str:
        """
        Search code in GitHub repositories.

        Args:
            keywords: Keywords to search for
            owner: Repository owner (optional)
            repo: Repository name (optional)
            match: 'file' or 'path'
            limit: Max results (1-10)

        Returns:
            JSON with search results
        """
        # In production, would call mcp__octocode__githubSearchCode
        return json.dumps({
            "action": "search_code",
            "keywords": keywords,
            "owner": owner,
            "repo": repo,
            "match": match,
            "limit": limit,
            "status": "simulated",
            "message": f"Would search for '{keywords}' in {owner}/{repo if repo else 'all'}"
        })

    @tool
    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: Optional[str] = None,
        match_string: Optional[str] = None
    ) -> str:
        """
        Get file content from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name (optional)
            match_string: String to match for context

        Returns:
            JSON with file content
        """
        # In production, would call mcp__octocode__githubGetFileContent
        return json.dumps({
            "action": "get_file_content",
            "owner": owner,
            "repo": repo,
            "path": path,
            "branch": branch,
            "match_string": match_string,
            "status": "simulated",
            "message": f"Would get {owner}/{repo}/{path}"
        })

    @tool
    def view_repo_structure(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        path: str = "",
        depth: int = 1
    ) -> str:
        """
        View repository directory structure.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            path: Starting path
            depth: How deep to explore (1-2)

        Returns:
            JSON with directory structure
        """
        # In production, would call mcp__octocode__githubViewRepoStructure
        return json.dumps({
            "action": "view_structure",
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": path,
            "depth": depth,
            "status": "simulated",
            "message": f"Would view {owner}/{repo} structure"
        })

    @tool
    def search_repositories(
        self,
        keywords: Optional[str] = None,
        topics: Optional[str] = None,
        stars: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """
        Search GitHub repositories.

        Args:
            keywords: Keywords to search
            topics: Topics (comma-separated)
            stars: Star filter (e.g., '>1000')
            limit: Max results

        Returns:
            JSON with repository results
        """
        # In production, would call mcp__octocode__githubSearchRepositories
        return json.dumps({
            "action": "search_repos",
            "keywords": keywords,
            "topics": topics,
            "stars": stars,
            "limit": limit,
            "status": "simulated",
            "message": f"Would search repos with '{keywords or topics}'"
        })

    @tool
    def search_pull_requests(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        query: Optional[str] = None,
        state: str = "closed",
        limit: int = 5
    ) -> str:
        """
        Search pull requests.

        Args:
            owner: Repository owner
            repo: Repository name
            query: Search query
            state: 'open' or 'closed'
            limit: Max results

        Returns:
            JSON with PR results
        """
        # In production, would call mcp__octocode__githubSearchPullRequests
        return json.dumps({
            "action": "search_prs",
            "owner": owner,
            "repo": repo,
            "query": query,
            "state": state,
            "limit": limit,
            "status": "simulated",
            "message": f"Would search PRs in {owner}/{repo if repo else 'all'}"
        })
