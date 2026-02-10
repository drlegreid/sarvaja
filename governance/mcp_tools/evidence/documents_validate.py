"""
Document Link Validation MCP Tool.

Per RD-DOCUMENT-MCP-SERVICE Quick Win: Automated stale link detection.
Validates all links in a markdown document and reports broken ones.

Created: 2026-02-11
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from governance.mcp_tools.common import format_mcp_result
from .common import DOCS_DIR, EVIDENCE_DIR, RULES_DIR, GAPS_DIR, BACKLOG_DIR

_MARKDOWN_LINK = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_SEARCH_DIRS = [DOCS_DIR, EVIDENCE_DIR, RULES_DIR, GAPS_DIR, BACKLOG_DIR]


def _resolve_link(link: str, context_dir: Path) -> Dict[str, Any]:
    """Resolve a single link and check if target exists."""
    result = {"link": link, "exists": False, "resolved": ""}

    # Skip external URLs
    if link.startswith(("http://", "https://", "mailto:", "#")):
        result["type"] = "external"
        result["exists"] = True  # Don't validate external links
        result["resolved"] = link
        return result

    result["type"] = "internal"
    link_path = Path(link)

    # Try relative to context first
    resolved = (context_dir / link_path).resolve()
    if resolved.exists():
        result["exists"] = True
        result["resolved"] = str(resolved)
        return result

    # Try project root
    resolved = (_PROJECT_ROOT / link_path).resolve()
    if resolved.exists():
        result["exists"] = True
        result["resolved"] = str(resolved)
        return result

    # Try search directories
    for search_dir in _SEARCH_DIRS:
        candidate = search_dir / link_path.name
        if candidate.exists():
            result["exists"] = True
            result["resolved"] = str(candidate)
            return result

    result["resolved"] = str(resolved)
    return result


def validate_document_links(path: str) -> Dict[str, Any]:
    """Validate all links in a markdown document.

    Args:
        path: Document path (relative to project root or absolute)

    Returns:
        Dict with total, valid, broken counts and details of broken links.
    """
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = _PROJECT_ROOT / file_path
    if not file_path.exists():
        return {"error": f"File not found: {path}"}

    content = file_path.read_text(errors="replace")
    context_dir = file_path.parent

    links = _MARKDOWN_LINK.findall(content)
    results = []
    broken = []

    for text, href in links:
        link_result = _resolve_link(href, context_dir)
        link_result["text"] = text
        results.append(link_result)
        if not link_result["exists"]:
            broken.append(link_result)

    return {
        "file": str(file_path),
        "total_links": len(results),
        "valid": len(results) - len(broken),
        "broken": len(broken),
        "broken_links": broken,
    }


def register_validate_document_tools(mcp) -> None:
    """Register document validation MCP tool."""

    @mcp.tool()
    def doc_validate(path: str) -> str:
        """Validate all links in a markdown document.

        Scans the document for markdown links and checks if
        each target file exists. Reports broken links.

        Per RD-DOCUMENT-MCP-SERVICE: Automated stale link detection.

        Args:
            path: Document path (relative to project root or absolute)

        Returns:
            Validation results with total, valid, and broken link counts.
        """
        result = validate_document_links(path)
        return format_mcp_result(result)
