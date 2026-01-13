"""
Document Viewing MCP Tools
==========================
Document viewing operations for evidence, rules, and tasks.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py
Per P10.8 / GAP-DOC-001, GAP-DOC-002: Document viewing
Per DOC-LINK-01-v1: Relative Document Linking support

Tools:
- governance_get_document: Get document content by path
- governance_list_documents: List documents in directory
- governance_get_rule_document: Get full rule markdown document
- governance_get_task_document: Get task details from workspace documents
- governance_extract_links: Extract all links from a document
- governance_resolve_link: Resolve a relative link to absolute path

Created: 2024-12-28
Updated: 2026-01-13 - Added URI-based link navigation
"""

import json
import re
import glob
from pathlib import Path

from governance.mcp_tools.common import get_typedb_client
from .common import (
    EVIDENCE_DIR,
    DOCS_DIR,
    BACKLOG_DIR,
    RULES_DIR,
    GAPS_DIR,
)


def register_document_tools(mcp) -> None:
    """Register document viewing MCP tools."""

    @mcp.tool()
    def governance_get_document(
        path: str,
        max_lines: int = 500
    ) -> str:
        """
        Get document content by path. Supports relative or absolute paths.

        Use this to view rule markdown files, evidence files, task details,
        or any document linked from TypeDB entities.

        Args:
            path: Document path (relative to project root or absolute)
            max_lines: Maximum lines to return (default 500, 0 = unlimited)

        Returns:
            JSON object with path, content, line_count, and metadata
        """
        # Resolve path
        doc_path = Path(path)
        candidates = []
        if not doc_path.is_absolute():
            # Try relative to common directories
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
            lines = content.split("\n")

            # Apply line limit
            if max_lines > 0 and len(lines) > max_lines:
                content = "\n".join(lines[:max_lines])
                truncated = True
            else:
                truncated = False

            # Extract metadata from markdown
            metadata = {}
            for line in lines[:20]:
                if line.startswith("# "):
                    metadata["title"] = line[2:].strip()
                elif line.startswith("**Status:**"):
                    metadata["status"] = line.replace("**Status:**", "").strip()
                elif line.startswith("**Updated:**") or line.startswith("**Last Updated:**"):
                    metadata["updated"] = line.split(":**")[1].strip() if ":**" in line else ""
                elif line.startswith("**Priority:**"):
                    metadata["priority"] = line.replace("**Priority:**", "").strip()

            return json.dumps({
                "path": str(doc_path),
                "filename": doc_path.name,
                "content": content,
                "line_count": len(lines),
                "truncated": truncated,
                "metadata": metadata
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to read document: {str(e)}"})

    @mcp.tool()
    def governance_list_documents(
        directory: str = "docs",
        pattern: str = "*.md",
        recursive: bool = False
    ) -> str:
        """
        List documents in a directory.

        Args:
            directory: Directory to list (relative to project root)
            pattern: File pattern (default "*.md")
            recursive: Search recursively (default False)

        Returns:
            JSON array of document paths with basic metadata
        """
        base_dir = Path(directory)
        if not base_dir.exists():
            return json.dumps({"error": f"Directory not found: {directory}"})

        documents = []
        glob_pattern = f"**/{pattern}" if recursive else pattern

        for filepath in sorted(base_dir.glob(glob_pattern)):
            if filepath.is_file():
                try:
                    # Get first heading as title
                    content = filepath.read_text(encoding="utf-8")
                    title = filepath.stem
                    for line in content.split("\n")[:10]:
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break

                    documents.append({
                        "path": str(filepath),
                        "filename": filepath.name,
                        "title": title,
                        "size_bytes": filepath.stat().st_size
                    })
                except Exception:
                    documents.append({
                        "path": str(filepath),
                        "filename": filepath.name,
                        "title": filepath.stem,
                        "error": "Could not read file"
                    })

        return json.dumps({
            "directory": str(base_dir),
            "pattern": pattern,
            "recursive": recursive,
            "documents": documents,
            "count": len(documents)
        }, indent=2)

    @mcp.tool()
    def governance_get_rule_document(rule_id: str) -> str:
        """
        Get full rule markdown document for a rule ID.

        Rules are stored in docs/rules/ directory. This tool finds and returns
        the full rule content for detailed viewing.

        Args:
            rule_id: Rule ID (e.g., "RULE-001", "RULE-012")

        Returns:
            JSON object with rule content, file path, and extracted metadata
        """
        # Search for rule in rule files
        rule_files = [
            RULES_DIR / "RULES-GOVERNANCE.md",
            RULES_DIR / "RULES-TECHNICAL.md",
            RULES_DIR / "RULES-OPERATIONAL.md",
        ]

        for rule_file in rule_files:
            if not rule_file.exists():
                continue

            content = rule_file.read_text(encoding="utf-8")

            # Find rule section (## RULE-XXX: format)
            rule_pattern = rf"## {rule_id}[:\s]"
            match = re.search(rule_pattern, content)

            if match:
                # Extract rule section (until next ## RULE- or ## section)
                start_idx = match.start()
                remaining = content[start_idx:]

                # Find end of this rule section (next ## heading)
                next_rule = re.search(r"\n## RULE-\d+", remaining[10:])
                if next_rule:
                    rule_content = remaining[:next_rule.start() + 10].strip()
                else:
                    # Find next major section (## or end)
                    next_section = re.search(r"\n## ", remaining[10:])
                    if next_section:
                        rule_content = remaining[:next_section.start() + 10].strip()
                    else:
                        rule_content = remaining.strip()

                # Extract metadata from rule content
                metadata = {"rule_id": rule_id}
                for line in rule_content.split("\n"):
                    if "**Priority:**" in line:
                        metadata["priority"] = line.split(":**")[1].strip().rstrip("*")
                    elif "**Status:**" in line:
                        metadata["status"] = line.split(":**")[1].strip().rstrip("*")
                    elif "**Category:**" in line:
                        metadata["category"] = line.split(":**")[1].strip().rstrip("*")

                return json.dumps({
                    "rule_id": rule_id,
                    "source_file": str(rule_file),
                    "content": rule_content,
                    "metadata": metadata
                }, indent=2)

        # Rule not found in files - try TypeDB
        client = get_typedb_client()
        try:
            if client.connect():
                rules = client.get_all_rules()
                for r in rules:
                    if r.id == rule_id:
                        return json.dumps({
                            "rule_id": rule_id,
                            "source": "typedb",
                            "name": r.name,
                            "directive": r.directive,
                            "category": r.category,
                            "priority": r.priority,
                            "status": r.status,
                            "note": "Full markdown not found in docs/rules/, showing TypeDB summary"
                        }, indent=2)
                client.close()
        except Exception:
            pass

        return json.dumps({"error": f"Rule {rule_id} not found in docs/rules/ or TypeDB"})

    @mcp.tool()
    def governance_get_task_document(task_id: str) -> str:
        """
        Get task details from workspace documents (TODO.md, R&D-BACKLOG.md).

        Args:
            task_id: Task ID (e.g., "P10.1", "P11.5", "RD-001")

        Returns:
            JSON object with task content from source documents
        """
        # Search in R&D-BACKLOG.md
        backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
        todo_file = Path("TODO.md")

        result = {"task_id": task_id, "sources": []}

        for doc_file in [backlog_file, todo_file]:
            if not doc_file.exists():
                continue

            content = doc_file.read_text(encoding="utf-8")

            # Find task mentions
            task_pattern = rf"\|\s*{re.escape(task_id)}\s*\|"

            for match in re.finditer(task_pattern, content):
                # Get the full line
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_end = content.find("\n", match.end())
                if line_end == -1:
                    line_end = len(content)

                line = content[line_start:line_end].strip()

                # Parse table row
                cells = [c.strip() for c in line.split("|") if c.strip()]

                result["sources"].append({
                    "file": str(doc_file),
                    "line": line,
                    "cells": cells
                })

        # Also check TypeDB
        client = get_typedb_client()
        try:
            if client.connect():
                task = client.get_task(task_id)
                if task:
                    result["typedb"] = {
                        "id": task.id,
                        "name": task.name,
                        "status": task.status,
                        "phase": task.phase,
                        "body": task.body,
                        "linked_rules": task.linked_rules,
                        "linked_sessions": task.linked_sessions
                    }
                client.close()
        except Exception:
            pass

        if not result["sources"] and "typedb" not in result:
            return json.dumps({"error": f"Task {task_id} not found in workspace documents or TypeDB"})

        return json.dumps(result, indent=2)

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
