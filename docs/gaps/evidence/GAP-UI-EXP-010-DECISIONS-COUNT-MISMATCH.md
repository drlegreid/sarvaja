# GAP-UI-EXP-010: Decisions Count Mismatch (UI vs API)

**Status:** OPEN
**Priority:** MEDIUM
**Category:** data_integrity
**Discovered:** 2026-01-14 via Playwright exploratory testing + API comparison

## Problem Statement

The Decisions view shows only 4 decisions but the API returns 7. Missing decisions are from evidence files rather than TypeDB.

## Technical Details

### Evidence Comparison

**UI Display:** 4 decisions
- DECISION-001: Remove Opik from Stack (TypeDB)
- DECISION-002: Mem0 Knowledge Governance (TypeDB)
- DECISION-003: TypeDB Priority Elevation (TypeDB)
- DECISION-004: No Enterprise Lockdown (TypeDB)

**API Response:** 7 decisions
- 4 from TypeDB (shown above)
- DECISION-005: Memory Consolidation Strategy (evidence_file)
- DECISION-006: Portable MCP Configuration Patterns (evidence_file)
- DECISION-003-TYPEDB-FIRST-STRATEGY: TypeDB-First Storage Strategy (evidence_file)

### Affected Files
| File | Line | Issue |
|------|------|-------|
| `agent/governance_ui/views/decisions_view.py` | TBD | Only loads TypeDB decisions |
| `governance/routes/evidence.py` | TBD | API combines TypeDB + evidence files |
| `agent/governance_ui/state/initial.py` | TBD | decisions state initialization |

### Root Cause Analysis

The API merges decisions from two sources:
1. TypeDB (queried via governance MCP)
2. Evidence files (parsed from markdown)

The UI appears to only display TypeDB-sourced decisions, missing the evidence_file sourced ones.

### Fix Approach
1. Verify dashboard API endpoint matches governance_list_decisions()
2. Update decisions_view.py to display all decisions regardless of source
3. Or: sync evidence_file decisions to TypeDB for single source of truth

## Evidence

- **UI Count**: 4 decisions
- **API Count**: 7 decisions
- **Missing**: 3 decisions with source="evidence_file"

## Related

- Rules: RULE-006 (Decision Logging)
- Other GAPs: None
- Session: SESSION-2026-01-14-EXPLORATORY

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
