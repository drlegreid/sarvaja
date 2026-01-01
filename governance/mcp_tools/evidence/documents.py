"""
Document Viewing MCP Tools
==========================
Document viewing operations for evidence, rules, and tasks.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py
Per P10.8 / GAP-DOC-001, GAP-DOC-002: Document viewing

Tools:
- governance_get_document: Get document content by path
- governance_list_documents: List documents in directory
- governance_get_rule_document: Get full rule markdown document
- governance_get_task_document: Get task details from workspace documents

Created: 2024-12-28
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
