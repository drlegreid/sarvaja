"""
Document Viewing Exports (GAP-FILE-007)
=======================================
Document backward compatibility exports for UI/API.

Per RULE-012: DSP Semantic Code Structure
Per P10.8: Document viewing support
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json
import re
from pathlib import Path

from governance.mcp_tools.evidence import EVIDENCE_DIR, DOCS_DIR, BACKLOG_DIR

RULES_DIR = DOCS_DIR / "rules"
GAPS_DIR = DOCS_DIR / "gaps"


def governance_get_document(path, max_lines=500):
    """Get document content (backward compat export)."""
    doc_path = Path(path)
    if not doc_path.is_absolute():
        candidates = [
            Path(path), DOCS_DIR / path, EVIDENCE_DIR / path,
            RULES_DIR / path, GAPS_DIR / path, BACKLOG_DIR / path,
        ]
        for candidate in candidates:
            if candidate.exists():
                doc_path = candidate
                break

    if not doc_path.exists():
        return json.dumps({"error": f"Document not found: {path}"})

    try:
        content = doc_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        if max_lines > 0 and len(lines) > max_lines:
            content = "\n".join(lines[:max_lines])
            truncated = True
        else:
            truncated = False

        return json.dumps({
            "path": str(doc_path),
            "filename": doc_path.name,
            "content": content,
            "line_count": len(lines),
            "truncated": truncated
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to read document: {str(e)}"})


def governance_list_documents(directory="docs", pattern="*.md", recursive=False):
    """List documents (backward compat export)."""
    base_dir = Path(directory)
    if not base_dir.exists():
        return json.dumps({"error": f"Directory not found: {directory}"})

    documents = []
    glob_pattern = f"**/{pattern}" if recursive else pattern
    for filepath in sorted(base_dir.glob(glob_pattern)):
        if filepath.is_file():
            documents.append({
                "path": str(filepath),
                "filename": filepath.name,
                "size_bytes": filepath.stat().st_size
            })

    return json.dumps({
        "directory": str(base_dir),
        "documents": documents,
        "count": len(documents)
    }, indent=2)


def governance_get_rule_document(rule_id):
    """Get rule document (backward compat export)."""
    rule_files = [
        RULES_DIR / "RULES-GOVERNANCE.md",
        RULES_DIR / "RULES-TECHNICAL.md",
        RULES_DIR / "RULES-OPERATIONAL.md",
    ]

    for rule_file in rule_files:
        if not rule_file.exists():
            continue
        content = rule_file.read_text(encoding="utf-8")
        rule_pattern = rf"## {rule_id}[:\s]"
        match = re.search(rule_pattern, content)
        if match:
            start_idx = match.start()
            remaining = content[start_idx:]
            next_rule = re.search(r"\n## RULE-\d+", remaining[10:])
            if next_rule:
                rule_content = remaining[:next_rule.start() + 10].strip()
            else:
                next_section = re.search(r"\n## ", remaining[10:])
                if next_section:
                    rule_content = remaining[:next_section.start() + 10].strip()
                else:
                    rule_content = remaining.strip()

            return json.dumps({
                "rule_id": rule_id,
                "source_file": str(rule_file),
                "content": rule_content
            }, indent=2)

    return json.dumps({"error": f"Rule {rule_id} not found"})


def governance_get_task_document(task_id):
    """Get task document (backward compat export)."""
    backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
    todo_file = Path("TODO.md")
    result = {"task_id": task_id, "sources": []}

    for doc_file in [backlog_file, todo_file]:
        if not doc_file.exists():
            continue
        content = doc_file.read_text(encoding="utf-8")
        task_pattern = rf"\|\s*{re.escape(task_id)}\s*\|"
        for match in re.finditer(task_pattern, content):
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end].strip()
            cells = [c.strip() for c in line.split("|") if c.strip()]
            result["sources"].append({"file": str(doc_file), "line": line, "cells": cells})

    if not result["sources"]:
        return json.dumps({"error": f"Task {task_id} not found"})
    return json.dumps(result, indent=2)
