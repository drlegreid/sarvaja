"""
Desktop Commander MCP Tools
===========================
Agno Toolkit wrapping Desktop Commander MCP tools for file operations.

Per RULE-007: Desktop Commander MCP is Tier 2 (recommended)
Per GAP-FILE-011: Extracted from external_mcp_tools.py

Created: 2024-12-28
"""

import json
from typing import Optional, List
from dataclasses import dataclass

from .common import tool, Toolkit


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
