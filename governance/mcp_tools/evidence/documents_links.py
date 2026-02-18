"""Document Link Extraction MCP Tools. Per DOC-LINK-01-v1."""

import logging
import re
from pathlib import Path

from governance.mcp_tools.common import format_mcp_result

logger = logging.getLogger(__name__)
from .common import (
    EVIDENCE_DIR,
    DOCS_DIR,
    BACKLOG_DIR,
    RULES_DIR,
    GAPS_DIR,
)


def register_link_document_tools(mcp) -> None:
    """Register document link extraction MCP tools."""

    @mcp.tool()
    def doc_links_extract(path: str) -> str:
        """
        Extract all links from a markdown document.

        Extracts markdown links, rule references (legacy and semantic),
        gap references, and task references from the document.

        Args:
            path: Document path (relative to project root or absolute)

        Returns:
            JSON with extracted links categorized by type and summary stats
        """
        doc_path = Path(path)
        candidates = []
        if not doc_path.is_absolute():
            candidates = [
                Path(path),
                DOCS_DIR / path,
                EVIDENCE_DIR / path,
                RULES_DIR / path,
                GAPS_DIR / path,
                BACKLOG_DIR / path,
            ]
            for candidate in candidates:
                if candidate.exists():
                    doc_path = candidate
                    break

        if not doc_path.exists():
            return format_mcp_result({
                "error": f"Document not found: {path}",
                "tried_paths": [str(c) for c in candidates] if candidates else [path]
            })

        try:
            content = doc_path.read_text(encoding="utf-8")

            # Extract markdown links
            md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            md_links = []
            for match in re.finditer(md_link_pattern, content):
                text, link_path = match.groups()
                if link_path.startswith(('http://', 'https://', 'mailto:')):
                    md_links.append({
                        "text": text,
                        "path": link_path,
                        "type": "external",
                        "position": match.start()
                    })
                else:
                    resolved = (
                        Path(link_path) if link_path.startswith('/')
                        else (doc_path.parent / link_path).resolve()
                    )
                    md_links.append({
                        "text": text,
                        "path": link_path,
                        "resolved": str(resolved),
                        "exists": resolved.exists(),
                        "type": "internal",
                        "position": match.start()
                    })

            # Extract rule references
            legacy_pattern = r'\bRULE-(\d{3})\b'
            legacy_refs = [
                {"rule_id": f"RULE-{m.group(1)}", "position": m.start()}
                for m in re.finditer(legacy_pattern, content)
            ]

            semantic_pattern = r'\b([A-Z]+-[A-Z]+-\d{2}-v\d+)\b'
            semantic_refs = [
                {"semantic_id": m.group(1), "position": m.start()}
                for m in re.finditer(semantic_pattern, content)
            ]

            # Extract gap references
            gap_pattern = r'\b(GAP-[A-Z]+-\d{3})\b'
            gap_refs = [
                {"gap_id": m.group(1), "position": m.start()}
                for m in re.finditer(gap_pattern, content)
            ]

            # Extract task references
            task_pattern = r'\b(P\d+\.\d+|RD-\d{3})\b'
            task_refs = [
                {"task_id": m.group(1), "position": m.start()}
                for m in re.finditer(task_pattern, content)
            ]

            return format_mcp_result({
                "source": str(doc_path),
                "links": {
                    "markdown": md_links,
                    "rules_legacy": legacy_refs,
                    "rules_semantic": semantic_refs,
                    "gaps": gap_refs,
                    "tasks": task_refs
                },
                "summary": {
                    "markdown_links": len(md_links),
                    "internal_links": len([l for l in md_links if l["type"] == "internal"]),
                    "external_links": len([l for l in md_links if l["type"] == "external"]),
                    "rule_refs": len(legacy_refs) + len(semantic_refs),
                    "gap_refs": len(gap_refs),
                    "task_refs": len(task_refs)
                }
            })

        # BUG-370-DLK-001: Log full error but return only type name
        except Exception as e:
            logger.error(f"doc_links_extract failed: {e}", exc_info=True)
            return format_mcp_result({"error": f"doc_links_extract failed: {type(e).__name__}"})

    @mcp.tool()
    def doc_link_resolve(link: str, context_path: str = "") -> str:
        """
        Resolve a link or reference to its document path.

        Handles semantic rule IDs, legacy rule IDs, gap IDs, task IDs,
        and regular file paths. Searches common directories if path
        is relative.

        Args:
            link: The link or reference to resolve (e.g., "RULE-001", "GAP-MCP-001")
            context_path: Optional context path for relative link resolution

        Returns:
            JSON with resolved path, existence status, and reference type
        """
        from governance.rule_linker import SEMANTIC_TO_LEGACY, LEGACY_TO_SEMANTIC

        result = {
            "input": link,
            "context": context_path,
            "resolved": None,
            "exists": False,
            "type": None
        }

        # Check for semantic rule ID
        semantic_match = re.match(r'^([A-Z]+-[A-Z]+-\d{2}-v\d+)$', link)
        if semantic_match:
            result["type"] = "semantic_rule_id"
            semantic_id = semantic_match.group(1)
            leaf_path = RULES_DIR / "leaf" / f"{semantic_id}.md"
            if leaf_path.exists():
                result["resolved"], result["exists"] = str(leaf_path), True
            else:
                legacy_id = SEMANTIC_TO_LEGACY.get(semantic_id)
                if legacy_id:
                    result["legacy_id"] = legacy_id
                    for rule_file in ["RULES-GOVERNANCE.md", "RULES-TECHNICAL.md", "RULES-OPERATIONAL.md"]:
                        rule_path = RULES_DIR / rule_file
                        if rule_path.exists():
                            content = rule_path.read_text(encoding="utf-8")
                            if f"## {legacy_id}" in content or semantic_id in content:
                                result["resolved"] = str(rule_path)
                                result["exists"] = True
                                result["section"] = legacy_id
                                break
            return format_mcp_result(result)

        # Check for legacy rule ID
        legacy_match = re.match(r'^RULE-(\d{3})$', link)
        if legacy_match:
            result["type"] = "legacy_rule_id"
            semantic_id = LEGACY_TO_SEMANTIC.get(link)
            if semantic_id:
                result["semantic_id"] = semantic_id
                leaf_path = RULES_DIR / "leaf" / f"{semantic_id}.md"
                if leaf_path.exists():
                    result["resolved"], result["exists"] = str(leaf_path), True
                    return format_mcp_result(result)
            for rule_file in ["RULES-GOVERNANCE.md", "RULES-TECHNICAL.md", "RULES-OPERATIONAL.md"]:
                rule_path = RULES_DIR / rule_file
                if rule_path.exists() and f"## {link}" in rule_path.read_text(encoding="utf-8"):
                    result["resolved"] = str(rule_path)
                    result["exists"] = True
                    result["section"] = link
                    break
            return format_mcp_result(result)

        # Check for gap ID
        gap_match = re.match(r'^GAP-([A-Z]+)-(\d{3})$', link)
        if gap_match:
            result["type"] = "gap_id"
            gap_index = GAPS_DIR / "GAP-INDEX.md"
            if gap_index.exists():
                result["resolved"] = str(gap_index)
                result["exists"] = True
                result["section"] = link
            gap_file = GAPS_DIR / f"{link}.md"
            if gap_file.exists():
                result["resolved"], result["exists"] = str(gap_file), True
            return format_mcp_result(result)

        # Check for task ID
        task_match = re.match(r'^(P\d+\.\d+|RD-\d{3})$', link)
        if task_match:
            result["type"] = "task_id"
            todo_file = Path("TODO.md")
            if todo_file.exists() and link in todo_file.read_text(encoding="utf-8"):
                result["resolved"] = str(todo_file)
                result["exists"] = True
                result["section"] = link
            if link.startswith("RD-"):
                rd_file = BACKLOG_DIR / "R&D-BACKLOG.md"
                if rd_file.exists():
                    result["resolved"], result["exists"] = str(rd_file), True
            return format_mcp_result(result)

        # Handle as regular path
        result["type"] = "path"
        link_path = Path(link)

        if link_path.is_absolute():
            result["resolved"], result["exists"] = str(link_path), link_path.exists()
        elif context_path:
            context = Path(context_path)
            resolved = (
                (context.parent / link_path).resolve()
                if context.is_file()
                else (context / link_path).resolve()
            )
            result["resolved"], result["exists"] = str(resolved), resolved.exists()
        else:
            candidates = [
                Path(link),
                DOCS_DIR / link,
                EVIDENCE_DIR / link,
                RULES_DIR / link,
                GAPS_DIR / link,
                BACKLOG_DIR / link,
            ]
            for candidate in candidates:
                if candidate.exists():
                    result["resolved"], result["exists"] = str(candidate), True
                    break
            if not result["resolved"]:
                result["resolved"] = str(Path(link).resolve())
                result["tried_paths"] = [str(c) for c in candidates]

        return format_mcp_result(result)
