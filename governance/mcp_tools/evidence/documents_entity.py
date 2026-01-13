"""
Entity Document Viewing MCP Tools
==================================
Document viewing for rules and tasks with TypeDB integration.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per P10.8 / GAP-DOC-001, GAP-DOC-002: Document viewing

Extracted from documents.py per DOC-SIZE-01-v1.

Tools:
- governance_get_rule_document: Get full rule markdown document
- governance_get_task_document: Get task details from workspace documents

Created: 2026-01-13 (extracted from documents.py)
"""

import json
import re
from pathlib import Path

from governance.mcp_tools.common import get_typedb_client
from .common import (
    DOCS_DIR,
    BACKLOG_DIR,
    RULES_DIR,
)


def register_entity_document_tools(mcp) -> None:
    """Register entity document viewing MCP tools."""

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
