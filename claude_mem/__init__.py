"""
Claude-Mem: Memory MCP Server for AMNESIA Recovery
==================================================
Created: 2026-01-11
Per RULE-024: AMNESIA Protocol

Provides ChromaDB-backed semantic memory for context recovery
across Claude Code sessions.

Collection: claude_memories
"""

from claude_mem.mcp_server import mcp

__all__ = ["mcp"]
__version__ = "1.0.0"
