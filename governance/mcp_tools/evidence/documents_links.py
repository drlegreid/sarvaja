"""
Document Link Extraction MCP Tools
===================================
Link extraction and resolution for document navigation.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per DOC-LINK-01-v1: Relative Document Linking support

Extracted from documents.py per DOC-SIZE-01-v1.

Tools:
- governance_extract_links: Extract all links from a document
- governance_resolve_link: Resolve a relative link to absolute path

Created: 2026-01-13 (extracted from documents.py)
"""

import json
import re
from pathlib import Path

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
    def governance_extract_links(path: str) -> str:
        """
        Extract all links from a markdown document.

        Per DOC-LINK-01-v1: Relative Document Linking support.
        Extracts markdown links [text](path), rule references (RULE-XXX, SEMANTIC-ID),
        and document references for navigation.

        Args:
            path: Document path (relative to project root or absolute)

        Returns:
            JSON object with extracted links categorized by type
        """
        # Resolve path
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
            return json.dumps({
                "error": f"Document not found: {path}",
                "tried_paths": [str(c) for c in candidates] if candidates else [path]
            })

        try:
            content = doc_path.read_text(encoding="utf-8")

            # Extract markdown links [text](path)
            md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            md_links = []
            for match in re.finditer(md_link_pattern, content):
                text, link_path = match.groups()
                # Skip external URLs
                if link_path.startswith(('http://', 'https://', 'mailto:')):
                    md_links.append({
                        "text": text,
                        "path": link_path,
                        "type": "external",
                        "position": match.start()
                    })
                else:
                    # Resolve relative path
                    if link_path.startswith('/'):
                        resolved = Path(link_path)
                    else:
                        resolved = (doc_path.parent / link_path).resolve()
                    md_links.append({
                        "text": text,
                        "path": link_path,
                        "resolved": str(resolved),
                        "exists": resolved.exists(),
                        "type": "internal",
                        "position": match.start()
                    })

            # Extract legacy rule references (RULE-XXX)
            legacy_pattern = r'\bRULE-(\d{3})\b'
            legacy_refs = []
            for match in re.finditer(legacy_pattern, content):
                rule_id = f"RULE-{match.group(1)}"
                legacy_refs.append({
                    "rule_id": rule_id,
                    "position": match.start()
                })

            # Extract semantic rule references (DOMAIN-SUB-NN-vN)
            semantic_pattern = r'\b([A-Z]+-[A-Z]+-\d{2}-v\d+)\b'
            semantic_refs = []
            for match in re.finditer(semantic_pattern, content):
                semantic_id = match.group(1)
                semantic_refs.append({
                    "semantic_id": semantic_id,
                    "position": match.start()
                })

            # Extract GAP references
            gap_pattern = r'\b(GAP-[A-Z]+-\d{3})\b'
            gap_refs = []
            for match in re.finditer(gap_pattern, content):
                gap_id = match.group(1)
                gap_refs.append({
                    "gap_id": gap_id,
                    "position": match.start()
                })

            # Extract task references (P10.1, RD-001)
            task_pattern = r'\b(P\d+\.\d+|RD-\d{3})\b'
            task_refs = []
            for match in re.finditer(task_pattern, content):
                task_id = match.group(1)
                task_refs.append({
                    "task_id": task_id,
                    "position": match.start()
                })

            return json.dumps({
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
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to extract links: {str(e)}"})

    @mcp.tool()
    def governance_resolve_link(
        link: str,
        context_path: str = ""
    ) -> str:
        """
        Resolve a link/reference to its document path.

        Per DOC-LINK-01-v1: Supports relative paths, rule IDs, semantic IDs,
        GAP IDs, and task IDs.

        Args:
            link: Link to resolve (path, RULE-XXX, semantic ID, GAP-XXX, etc.)
            context_path: Context document for resolving relative paths

        Returns:
            JSON object with resolved path and document info
        """
        from governance.rule_linker import SEMANTIC_TO_LEGACY, LEGACY_TO_SEMANTIC

        result = {
            "input": link,
            "context": context_path,
            "resolved": None,
            "exists": False,
            "type": None
        }

        # Determine link type and resolve
        # 1. Semantic rule ID (e.g., SESSION-EVID-01-v1)
        semantic_match = re.match(r'^([A-Z]+-[A-Z]+-\d{2}-v\d+)$', link)
        if semantic_match:
            semantic_id = semantic_match.group(1)
            result["type"] = "semantic_rule_id"

            # Try leaf file first
            leaf_path = RULES_DIR / "leaf" / f"{semantic_id}.md"
            if leaf_path.exists():
                result["resolved"] = str(leaf_path)
                result["exists"] = True
            else:
                # Get legacy ID and search in main rule files
                legacy_id = SEMANTIC_TO_LEGACY.get(semantic_id)
                if legacy_id:
                    result["legacy_id"] = legacy_id
                    # Search in rule files
                    for rule_file in ["RULES-GOVERNANCE.md", "RULES-TECHNICAL.md", "RULES-OPERATIONAL.md"]:
                        rule_path = RULES_DIR / rule_file
                        if rule_path.exists():
                            content = rule_path.read_text(encoding="utf-8")
                            if f"## {legacy_id}" in content or semantic_id in content:
                                result["resolved"] = str(rule_path)
                                result["exists"] = True
                                result["section"] = legacy_id
                                break
            return json.dumps(result, indent=2)

        # 2. Legacy rule ID (e.g., RULE-001)
        legacy_match = re.match(r'^RULE-(\d{3})$', link)
        if legacy_match:
            rule_id = link
            result["type"] = "legacy_rule_id"

            # Get semantic ID
            semantic_id = LEGACY_TO_SEMANTIC.get(rule_id)
            if semantic_id:
                result["semantic_id"] = semantic_id
                # Try leaf file
                leaf_path = RULES_DIR / "leaf" / f"{semantic_id}.md"
                if leaf_path.exists():
                    result["resolved"] = str(leaf_path)
                    result["exists"] = True
                    return json.dumps(result, indent=2)

            # Search in main rule files
            for rule_file in ["RULES-GOVERNANCE.md", "RULES-TECHNICAL.md", "RULES-OPERATIONAL.md"]:
                rule_path = RULES_DIR / rule_file
                if rule_path.exists():
                    content = rule_path.read_text(encoding="utf-8")
                    if f"## {rule_id}" in content:
                        result["resolved"] = str(rule_path)
                        result["exists"] = True
                        result["section"] = rule_id
                        break
            return json.dumps(result, indent=2)

        # 3. GAP ID (e.g., GAP-MCP-008)
        gap_match = re.match(r'^GAP-([A-Z]+)-(\d{3})$', link)
        if gap_match:
            result["type"] = "gap_id"
            # Try GAP-INDEX.md
            gap_index = GAPS_DIR / "GAP-INDEX.md"
            if gap_index.exists():
                result["resolved"] = str(gap_index)
                result["exists"] = True
                result["section"] = link
            # Also try specific gap file
            gap_file = GAPS_DIR / f"{link}.md"
            if gap_file.exists():
                result["resolved"] = str(gap_file)
                result["exists"] = True
            return json.dumps(result, indent=2)

        # 4. Task ID (e.g., P10.1, RD-001)
        task_match = re.match(r'^(P\d+\.\d+|RD-\d{3})$', link)
        if task_match:
            result["type"] = "task_id"
            # Try TODO.md
            todo_file = Path("TODO.md")
            if todo_file.exists():
                content = todo_file.read_text(encoding="utf-8")
                if link in content:
                    result["resolved"] = str(todo_file)
                    result["exists"] = True
                    result["section"] = link
            # Try R&D-BACKLOG.md for RD tasks
            if link.startswith("RD-"):
                rd_file = BACKLOG_DIR / "R&D-BACKLOG.md"
                if rd_file.exists():
                    result["resolved"] = str(rd_file)
                    result["exists"] = True
            return json.dumps(result, indent=2)

        # 5. Relative/absolute path
        result["type"] = "path"
        link_path = Path(link)

        if link_path.is_absolute():
            result["resolved"] = str(link_path)
            result["exists"] = link_path.exists()
        elif context_path:
            # Resolve relative to context document
            context = Path(context_path)
            if context.is_file():
                resolved = (context.parent / link_path).resolve()
            else:
                resolved = (context / link_path).resolve()
            result["resolved"] = str(resolved)
            result["exists"] = resolved.exists()
        else:
            # Try common directories
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
                    result["resolved"] = str(candidate)
                    result["exists"] = True
                    break
            if not result["resolved"]:
                result["resolved"] = str(Path(link).resolve())
                result["tried_paths"] = [str(c) for c in candidates]

        return json.dumps(result, indent=2)
