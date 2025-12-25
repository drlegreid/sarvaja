"""
External MCP → Agno @tool Wrappers - Phase 5 Integration
=========================================================
Wraps external MCP tools (Playwright, PowerShell, Desktop Commander, OctoCode)
as Agno @tool functions for direct agent use.

Pattern per RULE-017 (Cross-Workspace Pattern Reuse).
Per RULE-007 (MCP Tool Matrix).

Usage:
    from agent.external_mcp_tools import (
        PlaywrightTools,
        PowerShellTools,
        DesktopCommanderTools,
        OctoCodeTools
    )

    agent = Agent(tools=[PlaywrightTools(), PowerShellTools()], ...)

Created: 2024-12-24 (Phase 5)
Per: R&D-BACKLOG.md, CROSS-WORKSPACE-WISDOM.md
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Import Agno tools (available in container, may not be locally)
try:
    from agno.tools import tool, Toolkit
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    # Create stubs for local testing
    def tool(func):
        """Stub @tool decorator when agno not available."""
        func._is_tool = True
        return func

    class Toolkit:
        """Stub Toolkit class when agno not available."""
        def __init__(self, name: str = ""):
            self.name = name
            self.functions = {}

        def register(self, func):
            """Register a function as a tool."""
            self.functions[func.__name__] = func


# =============================================================================
# P5.1: PLAYWRIGHT TOOLS - Web Automation
# =============================================================================

@dataclass
class PlaywrightConfig:
    """Configuration for Playwright MCP tools."""
    browser_type: str = "chromium"
    headless: bool = True
    timeout_ms: int = 30000


class PlaywrightTools(Toolkit):
    """
    Agno Toolkit wrapping Playwright MCP tools for web automation.

    Provides browser automation capabilities for agents.
    Per RULE-007: Playwright MCP is Tier 1 (required).

    Available tools:
        - navigate: Navigate to a URL
        - snapshot: Get accessibility snapshot of page
        - click: Click on an element
        - type_text: Type text into an element
        - screenshot: Take a screenshot
        - evaluate: Execute JavaScript on page
        - wait_for: Wait for text or element
    """

    def __init__(self, config: Optional[PlaywrightConfig] = None):
        super().__init__(name="playwright")
        self.config = config or PlaywrightConfig()

        # Register tools
        self.register(self.navigate)
        self.register(self.snapshot)
        self.register(self.click)
        self.register(self.type_text)
        self.register(self.screenshot)
        self.register(self.evaluate)
        self.register(self.wait_for)

    @tool
    def navigate(self, url: str) -> str:
        """
        Navigate to a URL.

        Args:
            url: The URL to navigate to

        Returns:
            JSON with navigation result
        """
        # In production, would call mcp__playwright__browser_navigate
        return json.dumps({
            "action": "navigate",
            "url": url,
            "status": "simulated",
            "message": f"Would navigate to {url}"
        })

    @tool
    def snapshot(self, filename: Optional[str] = None) -> str:
        """
        Capture accessibility snapshot of the current page.

        Args:
            filename: Optional filename to save snapshot

        Returns:
            JSON with page accessibility tree
        """
        # In production, would call mcp__playwright__browser_snapshot
        return json.dumps({
            "action": "snapshot",
            "filename": filename,
            "status": "simulated",
            "message": "Would capture accessibility snapshot"
        })

    @tool
    def click(self, element: str, ref: str) -> str:
        """
        Click on a web page element.

        Args:
            element: Human-readable element description
            ref: Exact target element reference from snapshot

        Returns:
            JSON with click result
        """
        # In production, would call mcp__playwright__browser_click
        return json.dumps({
            "action": "click",
            "element": element,
            "ref": ref,
            "status": "simulated",
            "message": f"Would click on '{element}'"
        })

    @tool
    def type_text(self, element: str, ref: str, text: str, submit: bool = False) -> str:
        """
        Type text into an editable element.

        Args:
            element: Human-readable element description
            ref: Exact target element reference
            text: Text to type
            submit: Whether to press Enter after typing

        Returns:
            JSON with typing result
        """
        # In production, would call mcp__playwright__browser_type
        return json.dumps({
            "action": "type",
            "element": element,
            "ref": ref,
            "text": text,
            "submit": submit,
            "status": "simulated",
            "message": f"Would type '{text}' into '{element}'"
        })

    @tool
    def screenshot(self, filename: Optional[str] = None, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.

        Args:
            filename: Filename to save screenshot
            full_page: Whether to capture full scrollable page

        Returns:
            JSON with screenshot path
        """
        # In production, would call mcp__playwright__browser_take_screenshot
        return json.dumps({
            "action": "screenshot",
            "filename": filename,
            "full_page": full_page,
            "status": "simulated",
            "message": "Would capture screenshot"
        })

    @tool
    def evaluate(self, function: str, element: Optional[str] = None) -> str:
        """
        Evaluate JavaScript on the page.

        Args:
            function: JavaScript function to execute
            element: Optional element context

        Returns:
            JSON with evaluation result
        """
        # In production, would call mcp__playwright__browser_evaluate
        return json.dumps({
            "action": "evaluate",
            "function": function,
            "element": element,
            "status": "simulated",
            "message": "Would evaluate JavaScript"
        })

    @tool
    def wait_for(self, text: Optional[str] = None, time: Optional[int] = None) -> str:
        """
        Wait for text to appear or specified time.

        Args:
            text: Text to wait for
            time: Time to wait in seconds

        Returns:
            JSON with wait result
        """
        # In production, would call mcp__playwright__browser_wait_for
        return json.dumps({
            "action": "wait",
            "text": text,
            "time": time,
            "status": "simulated",
            "message": f"Would wait for {'text: ' + text if text else str(time) + 's'}"
        })


# =============================================================================
# P5.2: POWERSHELL TOOLS - DevOps Automation
# =============================================================================

@dataclass
class PowerShellConfig:
    """Configuration for PowerShell MCP tools."""
    timeout: int = 300  # 5 minutes default
    working_directory: Optional[str] = None


class PowerShellTools(Toolkit):
    """
    Agno Toolkit wrapping PowerShell MCP tools for DevOps automation.

    Provides PowerShell execution capabilities for agents.
    Per RULE-007: PowerShell MCP is Tier 2 (recommended).

    Available tools:
        - run_script: Execute PowerShell code
        - run_command: Run a single PowerShell command
    """

    def __init__(self, config: Optional[PowerShellConfig] = None):
        super().__init__(name="powershell")
        self.config = config or PowerShellConfig()

        # Register tools
        self.register(self.run_script)
        self.register(self.run_command)

    @tool
    def run_script(self, code: str, timeout: Optional[int] = None) -> str:
        """
        Execute PowerShell code.

        Args:
            code: PowerShell code to execute (max 10,000 chars)
            timeout: Timeout in seconds (default 300)

        Returns:
            JSON with execution output
        """
        # In production, would call mcp__powershell__run_powershell
        return json.dumps({
            "action": "run_script",
            "code_length": len(code),
            "timeout": timeout or self.config.timeout,
            "status": "simulated",
            "message": "Would execute PowerShell script"
        })

    @tool
    def run_command(self, command: str) -> str:
        """
        Run a single PowerShell command.

        Args:
            command: PowerShell command to run

        Returns:
            JSON with command output
        """
        # Wrapper for run_script with single command
        return self.run_script(command)


# =============================================================================
# P5.3: DESKTOP COMMANDER TOOLS - File Operations
# =============================================================================

@dataclass
class DesktopCommanderConfig:
    """Configuration for Desktop Commander MCP tools."""
    allowed_directories: Optional[List[str]] = None
    file_read_limit: int = 1000  # lines


class DesktopCommanderTools(Toolkit):
    """
    Agno Toolkit wrapping Desktop Commander MCP tools for file operations.

    Provides file system capabilities for agents.
    Per RULE-007: Desktop Commander MCP is Tier 2 (recommended).

    Available tools:
        - read_file: Read file contents
        - write_file: Write file contents
        - list_directory: List directory contents
        - search_files: Search for files
        - get_file_info: Get file metadata
        - create_directory: Create a directory
        - move_file: Move or rename files
    """

    def __init__(self, config: Optional[DesktopCommanderConfig] = None):
        super().__init__(name="desktop_commander")
        self.config = config or DesktopCommanderConfig()

        # Register tools
        self.register(self.read_file)
        self.register(self.write_file)
        self.register(self.list_directory)
        self.register(self.search_files)
        self.register(self.get_file_info)
        self.register(self.create_directory)
        self.register(self.move_file)

    @tool
    def read_file(self, path: str, offset: int = 0, length: int = 1000) -> str:
        """
        Read contents from a file.

        Args:
            path: Absolute path to the file
            offset: Line offset to start reading
            length: Number of lines to read

        Returns:
            JSON with file contents
        """
        # In production, would call mcp__desktop-commander__read_file
        return json.dumps({
            "action": "read_file",
            "path": path,
            "offset": offset,
            "length": length,
            "status": "simulated",
            "message": f"Would read {length} lines from {path}"
        })

    @tool
    def write_file(self, path: str, content: str, mode: str = "rewrite") -> str:
        """
        Write content to a file.

        Args:
            path: Absolute path to the file
            content: Content to write
            mode: 'rewrite' or 'append'

        Returns:
            JSON with write result
        """
        # In production, would call mcp__desktop-commander__write_file
        return json.dumps({
            "action": "write_file",
            "path": path,
            "content_length": len(content),
            "mode": mode,
            "status": "simulated",
            "message": f"Would {mode} {len(content)} chars to {path}"
        })

    @tool
    def list_directory(self, path: str, depth: int = 2) -> str:
        """
        List directory contents.

        Args:
            path: Path to directory
            depth: How deep to recurse (1-2)

        Returns:
            JSON with directory listing
        """
        # In production, would call mcp__desktop-commander__list_directory
        return json.dumps({
            "action": "list_directory",
            "path": path,
            "depth": depth,
            "status": "simulated",
            "message": f"Would list {path} to depth {depth}"
        })

    @tool
    def search_files(
        self,
        path: str,
        pattern: str,
        search_type: str = "files"
    ) -> str:
        """
        Search for files or content.

        Args:
            path: Directory to search in
            pattern: Search pattern
            search_type: 'files' or 'content'

        Returns:
            JSON with search results
        """
        # In production, would call mcp__desktop-commander__start_search
        return json.dumps({
            "action": "search",
            "path": path,
            "pattern": pattern,
            "search_type": search_type,
            "status": "simulated",
            "message": f"Would search for '{pattern}' in {path}"
        })

    @tool
    def get_file_info(self, path: str) -> str:
        """
        Get file or directory metadata.

        Args:
            path: Path to file or directory

        Returns:
            JSON with file metadata
        """
        # In production, would call mcp__desktop-commander__get_file_info
        return json.dumps({
            "action": "get_file_info",
            "path": path,
            "status": "simulated",
            "message": f"Would get info for {path}"
        })

    @tool
    def create_directory(self, path: str) -> str:
        """
        Create a directory.

        Args:
            path: Path for new directory

        Returns:
            JSON with creation result
        """
        # In production, would call mcp__desktop-commander__create_directory
        return json.dumps({
            "action": "create_directory",
            "path": path,
            "status": "simulated",
            "message": f"Would create directory {path}"
        })

    @tool
    def move_file(self, source: str, destination: str) -> str:
        """
        Move or rename a file.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            JSON with move result
        """
        # In production, would call mcp__desktop-commander__move_file
        return json.dumps({
            "action": "move_file",
            "source": source,
            "destination": destination,
            "status": "simulated",
            "message": f"Would move {source} to {destination}"
        })


# =============================================================================
# P5.4: OCTOCODE TOOLS - Code Research
# =============================================================================

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


# =============================================================================
# COMBINED TOOLKIT
# =============================================================================

class ExternalMCPTools(Toolkit):
    """
    Combined toolkit providing all external MCP tools.

    Aggregates Playwright, PowerShell, Desktop Commander, and OctoCode tools.

    Usage:
        from agent.external_mcp_tools import ExternalMCPTools

        tools = ExternalMCPTools()
        agent = Agent(tools=[tools], ...)
    """

    def __init__(
        self,
        enable_playwright: bool = True,
        enable_powershell: bool = True,
        enable_desktop_commander: bool = True,
        enable_octocode: bool = True
    ):
        super().__init__(name="external_mcp")

        # Initialize enabled toolkits
        self._toolkits = []

        if enable_playwright:
            self._toolkits.append(PlaywrightTools())
        if enable_powershell:
            self._toolkits.append(PowerShellTools())
        if enable_desktop_commander:
            self._toolkits.append(DesktopCommanderTools())
        if enable_octocode:
            self._toolkits.append(OctoCodeTools())

        # Register all tools from sub-toolkits
        for toolkit in self._toolkits:
            for name, func in toolkit.functions.items():
                prefixed_name = f"{toolkit.name}_{name}"
                self.functions[prefixed_name] = func

    @property
    def enabled_toolkits(self) -> List[str]:
        """Get list of enabled toolkit names."""
        return [t.name for t in self._toolkits]


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

def get_all_external_tools() -> List[Toolkit]:
    """Get all external MCP toolkits as a list."""
    return [
        PlaywrightTools(),
        PowerShellTools(),
        DesktopCommanderTools(),
        OctoCodeTools()
    ]


def get_web_automation_tools() -> PlaywrightTools:
    """Get Playwright tools for web automation."""
    return PlaywrightTools()


def get_devops_tools() -> PowerShellTools:
    """Get PowerShell tools for DevOps."""
    return PowerShellTools()


def get_file_tools() -> DesktopCommanderTools:
    """Get Desktop Commander tools for file operations."""
    return DesktopCommanderTools()


def get_code_research_tools() -> OctoCodeTools:
    """Get OctoCode tools for code research."""
    return OctoCodeTools()
