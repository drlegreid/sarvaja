# BACKFILL-OPS-01-v1: Backfill Operation Standards

**Status:** ACTIVE | **Priority:** HIGH | **Category:** OPERATIONAL
**Created:** 2026-01-20

---

## Directive

Data backfill operations MUST follow enterprise component patterns:
1. **Service Layer**: Logic in `governance/*.py` module (NOT standalone scripts)
2. **MCP Exposure**: Operations exposed via MCP tools for auditability
3. **Dry-Run Pattern**: Always support `scan` (preview) and `execute` (apply) modes
4. **Reusability**: Components designed for reuse across entity types

---

## Rationale

Standalone scripts violate:
- **Auditability**: No trace in session evidence
- **Reusability**: One-off code wastes effort
- **Consistency**: Breaks established patterns
- **Governance**: Operations not tracked by MCP

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ MCP Tools (governance/mcp_tools/)                          │
│   ├── backfill_scan_*()     → Dry run, show what changes   │
│   └── backfill_execute_*()  → Apply changes with audit     │
└────────────────────┬────────────────────────────────────────┘
                     │ delegates to
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Service Layer (governance/backfill_service.py)              │
│   ├── scan_evidence_for_linkages() → Returns proposed links │
│   └── apply_linkages()             → Creates relations      │
└─────────────────────────────────────────────────────────────┘
```

---

## Patterns

### Pattern 1: Scan/Execute Separation

```python
# MCP Tool: Dry run
@mcp.tool()
def backfill_scan_task_sessions() -> str:
    """Scan evidence files for task-session linkages (dry run)."""
    from governance.backfill_service import scan_evidence_for_linkages
    return format_mcp_result(scan_evidence_for_linkages())

# MCP Tool: Execute
@mcp.tool()
def backfill_execute_task_sessions(dry_run: bool = True) -> str:
    """Create task-session linkages from evidence files."""
    if dry_run:
        return backfill_scan_task_sessions()
    from governance.backfill_service import apply_linkages
    return format_mcp_result(apply_linkages())
```

### Pattern 2: Reusable Scanner

```python
# Generic evidence scanner - reusable for different entity types
def scan_evidence_files(
    pattern: str = "SESSION-*.md",
    entity_extractor: Callable[[str], Set[str]]
) -> Dict[str, Set[str]]:
    """Scan evidence files and extract entities."""
    pass
```

---

## Anti-Patterns

| DON'T | DO |
|-------|-----|
| Standalone scripts in `governance/scripts/` | MCP tools + service layer |
| Direct TypeDB writes without audit | MCP tools with session tracking |
| One-off code for specific backfill | Reusable patterns |
| Execute without preview | Always scan first |

---

## Related

- WORKSPACE_SCAN pattern in `workspace_scanner.py`
- TEST-FIX-01-v1: Verification before marking complete
- SESSION-EVID-01-v1: Session evidence requirements

---

*Per GAP-UI-AUDIT-001: Architectural lesson from backfill implementation*
