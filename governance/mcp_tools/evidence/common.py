"""
Evidence Common Utilities
=========================
Shared constants and utilities for evidence MCP tools.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Evidence module extraction

Created: 2024-12-28
"""

from pathlib import Path

# Evidence paths (shared across evidence modules)
EVIDENCE_DIR = Path("evidence")
DOCS_DIR = Path("docs")
BACKLOG_DIR = DOCS_DIR / "backlog"
RULES_DIR = DOCS_DIR / "rules"
GAPS_DIR = DOCS_DIR / "gaps"
TASKS_DIR = DOCS_DIR / "tasks"

__all__ = [
    "EVIDENCE_DIR",
    "DOCS_DIR",
    "BACKLOG_DIR",
    "RULES_DIR",
    "GAPS_DIR",
    "TASKS_DIR",
]
