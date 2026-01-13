# UI-TRAME-01-v1: Cross-Workspace Pattern Reuse

**Category:** `strategic` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-017
> **Location:** [RULES-STRATEGY.md](../technical/RULES-STRATEGY.md)
> **Tags:** `patterns`, `reuse`, `workspace`, `wisdom`

---

## Directive

Before implementing new functionality, check cross-workspace wisdom index for existing patterns.

---

## Pattern Sources

| Source | Patterns |
|--------|----------|
| local-gai | EBMSF, DSM, MCP wrappers |
| agno-agi | Base Agno cluster |
| sim-ai | TypeDB hybrid, Governance MCP |

---

## Pattern Categories

| Category | Documents | Tools |
|----------|-----------|-------|
| MCP Wrappers | docker_wrapper.py | Dependency auto-start |
| Type-Safe Tools | pydantic_tools.py | Pydantic AI + FastMCP |
| State Machines | langgraph_workflow.py | LangGraph |
| Evidence Tracking | dsm_tracker.py | DSM phases |

---

## Validation

- [ ] Cross-workspace search performed
- [ ] Existing patterns leveraged
- [ ] New patterns documented for reuse

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
