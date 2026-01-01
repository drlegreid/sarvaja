"""
Evidence Viewing MCP Tools
==========================
Evidence artifact viewing operations (P9.1 - Strategic Platform).

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Evidence entity module

**Refactored: 2024-12-28 per GAP-FILE-008**
Original: 870 lines → Package with 6 modules (~100-200 lines each)

Modules extracted to governance/mcp_tools/evidence/:
- sessions.py: Session listing and retrieval
- decisions.py: Decision listing and retrieval
- tasks.py: Task listing and dependency tracking
- search.py: Evidence semantic search
- quality.py: Rule quality analysis tools
- documents.py: Document viewing tools
"""

# Re-export the register function from the package
from governance.mcp_tools.evidence import register_evidence_tools

# Re-export common constants for backward compatibility
from governance.mcp_tools.evidence.common import (
    EVIDENCE_DIR,
    DOCS_DIR,
    BACKLOG_DIR,
    RULES_DIR,
    GAPS_DIR,
    TASKS_DIR,
)

__all__ = [
    "register_evidence_tools",
    "EVIDENCE_DIR",
    "DOCS_DIR",
    "BACKLOG_DIR",
    "RULES_DIR",
    "GAPS_DIR",
    "TASKS_DIR",
]
