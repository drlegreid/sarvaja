# Critical Gaps Analysis - 2026-01-02

## Executive Summary

Based on thorough analysis of the codebase, TypeDB schema, client implementations, and actual data state, the following **CRITICAL** issues were identified:

1. **Playwright MCP is non-functional** - Cannot run E2E UI tests
2. **Entity linkage is incomplete** - Schema exists but relations NOT populated
3. **Sessions come from files, not TypeDB** - No entity relationships
4. **P11.3 stuck IN_PROGRESS** - Linkage task never completed

---

## Analysis Evidence

### 1. Playwright MCP Status

| Aspect | Status | Details |
|--------|--------|---------|
| Config in `.claude.json` | **FIXED** | Changed from wrong package to `@playwright/mcp@latest` |
| Previous Package | WRONG | `@anthropic-ai/mcp-server-playwright@latest` (doesn't exist in npm) |
| Correct Package | `@playwright/mcp@latest` | Verified working with `--help` |
| Impact | **CRITICAL** | Cannot run E2E browser tests per GAP-WORKFLOW-004 |

**ROOT CAUSE FOUND:**
- **Wrong npm package name** in `.claude.json`
- Package `@anthropic-ai/mcp-server-playwright` returns 404 (not in registry)
- Correct package is `@playwright/mcp@latest`

**FIX APPLIED:**
```json
// BEFORE (WRONG):
"args": ["-y", "@anthropic-ai/mcp-server-playwright@latest"]

// AFTER (FIXED):
"args": ["-y", "@playwright/mcp@latest", "--browser", "msedge"]
```

**REQUIRES RESTART** - Claude Code must be restarted to reload MCP servers

### 2. Entity Linkage Analysis

#### TypeDB Schema Relations (DEFINED)
```
implements-rule: Task → Rule
completed-in: Task → Session
has-evidence: Session → Evidence
session-applied-rule: Session → Rule
session-decision: Session → Decision
evidence-supports: Evidence → Task
references-gap: Task → Gap
```

#### Implementation Status (CODE)
| Relation | Read Support | Write Support | Actually Used |
|----------|--------------|---------------|---------------|
| implements-rule | YES | YES (insert only) | PARTIAL - some seed data |
| completed-in | YES | YES (insert only) | PARTIAL - 3 tasks linked |
| has-evidence | YES | YES | NO - no relations exist |
| session-applied-rule | YES | **NO** | NO |
| session-decision | YES | **NO** | NO |
| evidence-supports | YES | **NO** | NO |
| references-gap | YES | **NO** | Uses attribute instead |

#### Data State (TypeDB Query Results)
- **17 tasks** in TypeDB
- **4 tasks** have linked_rules (24%)
- **3 tasks** have linked_sessions (18%)
- **0 tasks** have agent_id
- **0 tasks** have completed_at timestamps
- **0 tasks** have evidence field populated
- **9 sessions** from filesystem, **0 sessions** with proper TypeDB relations

### 3. Why Sessions Don't Link

`governance_list_sessions` reads from **filesystem** (`evidence/*.md`), not TypeDB!

```python
# Current behavior:
# Sessions come from: evidence/SESSION-*.md files
# NOT from TypeDB work-session entities with relations
```

The `work-session` TypeDB entity exists in schema but sessions aren't created there during normal workflow.

### 4. Missing Workflow Integration

When Claude completes a task, the following should happen but DOESN'T:

1. Create `completed-in` relation linking task to current session
2. Create `session-applied-rule` for rules used during session
3. Create `session-decision` for decisions made
4. Create `evidence-supports` linking evidence to task
5. Update task `completed_at` timestamp

**All these methods are MISSING from the client.**

---

## Prioritized Task List

### CRITICAL (P0) - Blocking All Verification

| ID | Task | Description | GAP |
|----|------|-------------|-----|
| C1 | Fix Playwright MCP | Diagnose why tools aren't available, fix or re-enable | GAP-WORKFLOW-004 |
| C2 | E2E Test Framework | Once Playwright works, create exploratory UI test suite | GAP-WORKFLOW-004 |

### HIGH (P1) - Core Functionality Broken

| ID | Task | Description | GAP |
|----|------|-------------|-----|
| H1 | Add session-to-rule linking | Implement `link_rule_to_session()` method | GAP-DATA-002, P11.3 |
| H2 | Add session-to-decision linking | Implement `link_decision_to_session()` method | GAP-DATA-002, P11.3 |
| H3 | Add evidence-to-task linking | Implement `link_evidence_to_task()` method | GAP-DATA-002, P11.3 |
| H4 | Session creation in TypeDB | Create TypeDB sessions during workflow, not just files | GAP-ARCH-002 |
| H5 | Task completion workflow | Auto-create relations when task status → DONE | P11.3 |
| H6 | Sync filesystem sessions | Import existing SESSION-*.md files to TypeDB with relations | GAP-SYNC-001 |

### MEDIUM (P2) - UI and Verification

| ID | Task | Description | GAP |
|----|------|-------------|-----|
| M1 | Sessions list view fix | Show TypeDB sessions with task/evidence counts | GAP-UI-008 |
| M2 | Tasks list view fix | Show linked sessions and rules | GAP-UI-* |
| M3 | Entity relationship viewer | UI component to visualize entity links | NEW |
| M4 | Evidence attachment UI | Allow attaching evidence to tasks/sessions | GAP-UI-* |

### LOW (P3) - Improvements

| ID | Task | Description | GAP |
|----|------|-------------|-----|
| L1 | Bidirectional sync | TypeDB ↔ Filesystem sync for sessions | GAP-SYNC-002 |
| L2 | AMNESIA context loading | Load DECISION context during recovery | GAP-CTX-003 |
| L3 | Memory consolidation | Single memory system (claude-mem vs governance) | GAP-CTX-002 |

---

## Recommended Execution Order

```
Phase 1: E2E Testing Capability
├── C1: Fix Playwright MCP (blocks everything)
└── C2: Create E2E test suite

Phase 2: Core Entity Linkage (P11.3 completion)
├── H4: Session creation in TypeDB
├── H1: Session-to-rule linking
├── H2: Session-to-decision linking
├── H3: Evidence-to-task linking
├── H5: Task completion workflow
└── H6: Sync existing sessions

Phase 3: UI Verification (requires E2E)
├── M1: Sessions view with relations
├── M2: Tasks view with links
├── M3: Entity relationship viewer
└── M4: Evidence attachment UI

Phase 4: Infrastructure
├── L1: Bidirectional sync
├── L2: AMNESIA context loading
└── L3: Memory consolidation
```

---

## Appendix: Investigation Commands

### Check Playwright MCP
```powershell
# Test if playwright server starts
npx -y @anthropic-ai/mcp-server-playwright@latest

# Check if browsers installed
npx playwright install --help
```

### Verify TypeDB Relations
```typeql
# Find sessions with linked rules
match
  $s isa work-session, has session-id $sid;
  (applying-session: $s, applied-rule: $r) isa session-applied-rule;
get $sid;

# Find sessions with linked evidence
match
  $s isa work-session, has session-id $sid;
  (evidence-session: $s, session-evidence: $e) isa has-evidence;
get $sid;
```

---

## MCP Tool Calls Used for Analysis

```json
{
  "governance_health": "Verify TypeDB/ChromaDB healthy",
  "governance_list_all_tasks": "17 tasks, examined linkage",
  "governance_list_sessions": "9 sessions from filesystem",
  "file_reads": [
    "schema.tql - Confirmed relation definitions",
    "typedb/queries/tasks.py - Checked write methods",
    "typedb/queries/sessions.py - Confirmed missing link methods"
  ]
}
```

---

*Generated: 2026-01-02 | Per RULE-001 Evidence Trail*
