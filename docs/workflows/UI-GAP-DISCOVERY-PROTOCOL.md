# UI Gap Discovery Protocol

**Per:** UI-FIRST-SPRINT-WORKFLOW.md, RULE-004, RULE-020, RULE-023
**Created:** 2024-12-25

---

## Purpose

Systematic discovery of UI gaps during exploratory testing sessions. Each gap is documented, prioritized, and tracked through resolution.

---

## Gap Identification Template

```yaml
gap_id: "GAP-UI-XXX"
discovered: "YYYY-MM-DD"
session_id: "EXP-P10-XXX"

# What
entity: "governance-rule"        # Domain entity affected
view: "Rules Browser"            # UI view where gap exists
operation: "UPDATE"              # CRUD operation: CREATE/READ/UPDATE/DELETE/SEARCH

# Classification
type: "missing_feature"          # missing_feature | broken | incomplete | ux_issue
severity: "HIGH"                 # CRITICAL | HIGH | MEDIUM | LOW
priority: "P0"                   # P0 (blocking) | P1 (next sprint) | P2 (backlog)

# Description
description: "No edit button for rules"
expected: "Edit button visible on rule detail view"
actual: "No way to edit rules from UI"
screenshot: "evidence/screenshots/GAP-UI-XXX.png"

# Resolution
status: "OPEN"                   # OPEN | IN_PROGRESS | RESOLVED | WONT_FIX
resolved_by: ""                  # Commit hash or PR
resolved_date: ""
test_added: ""                   # Robot Framework test file
```

---

## Discovery Heuristics

### Per Entity Checklist

Run this checklist for each domain entity (Rule, Decision, Session, Task, Agent, Evidence):

```
ENTITY: _________________ (e.g., governance-rule)
VIEW:   _________________ (e.g., Rules Browser)
URL:    _________________ (e.g., http://localhost:8081)

NAVIGATION
[ ] Can navigate to entity list view?
[ ] Can navigate to entity detail view?
[ ] Breadcrumb/back navigation works?
[ ] URL is bookmarkable/shareable?

LIST VIEW
[ ] All expected columns present?
    Expected: [id, title, status, category, updated_at]
    Actual:   ________________________________
[ ] Sorting works on each column?
[ ] Filtering/search works?
[ ] Pagination works (if >10 items)?
[ ] Empty state shown when no data?
[ ] Loading state shown during fetch?

DETAIL VIEW
[ ] All entity fields displayed?
    Expected: [full content, metadata, relations]
    Actual:   ________________________________
[ ] Related entities linked/navigable?
[ ] Actions available (edit, delete, etc)?
[ ] Refresh/reload works?

CREATE (Form)
[ ] Form exists and is accessible?
[ ] All required fields present?
[ ] Validation messages shown?
[ ] Success feedback on create?
[ ] Created item appears in list?

UPDATE (Edit)
[ ] Edit button/action exists?
[ ] Pre-populated with current values?
[ ] Can modify and save?
[ ] Changes reflected immediately?

DELETE
[ ] Delete button/action exists?
[ ] Confirmation dialog shown?
[ ] Soft delete (can undo)?
[ ] Item removed from list?

ERROR HANDLING
[ ] API error shown gracefully?
[ ] Network timeout handled?
[ ] 404 (not found) handled?
[ ] 403 (forbidden) handled?
```

---

## Gap Types

| Type | Description | Example |
|------|-------------|---------|
| `missing_feature` | Feature not implemented | No edit button |
| `broken` | Feature exists but doesn't work | Edit button throws error |
| `incomplete` | Partial implementation | Edit form missing fields |
| `ux_issue` | Works but poor UX | No loading indicator |
| `accessibility` | A11y violation | No keyboard navigation |
| `performance` | Slow or unresponsive | List takes >3s to load |
| `data_binding` | Data not synced with backend | Stale data after update |

---

## Severity Matrix

| Severity | User Impact | Action |
|----------|-------------|--------|
| **CRITICAL** | Cannot use the feature at all | Fix before next deploy |
| **HIGH** | Major workflow blocked | Fix in current sprint |
| **MEDIUM** | Workaround available | Schedule for next sprint |
| **LOW** | Cosmetic or minor | Add to backlog |

---

## Discovery Session Flow

```
1. START SESSION
   └── Record session ID, date, target view

2. NAVIGATE
   └── Open target view in browser
   └── Take initial snapshot (Playwright: browser_snapshot)

3. APPLY HEURISTICS
   └── Run through entity checklist above
   └── Note each gap found

4. DOCUMENT GAPS
   └── Create GAP-UI-XXX entry for each issue
   └── Take screenshots for evidence

5. VERIFY WITH API
   └── Check if API supports missing features
   └── Determine: UI gap vs backend gap

6. GENERATE TESTS
   └── Create Robot test for working features
   └── Skip/tag tests for known gaps

7. UPDATE GAP INDEX
   └── Add new gaps to GAP-INDEX.md
   └── Link to session evidence
```

---

## API Contract Verification

For each entity, verify UI displays match API responses:

```
API: GET /api/rules
Response Field    | UI Display Location      | Status
-----------------|--------------------------|--------
rule_id          | List column, Detail header| [ ]
title            | List column, Detail header| [ ]
status           | List badge, Detail meta   | [ ]
category         | List column, Detail meta  | [ ]
directive        | Detail content area       | [ ]
created_at       | Detail metadata           | [ ]
updated_at       | List column               | [ ]
```

---

## Current UI Gaps (P10)

Track gaps discovered during UI-First Sprint:

| ID | Entity | View | Type | Severity | Status |
|----|--------|------|------|----------|--------|
| GAP-UI-001 | - | - | - | - | Template |

---

## Integration Points

- **GAP-INDEX.md**: Master gap tracker
- **R&D-BACKLOG.md**: Feature requests from gaps
- **RULE-023**: Test before ship (verify gaps resolved)
- **UI-FIRST-SPRINT-WORKFLOW.md**: Sprint process
- **Robot tests**: Automated verification

---

*Per RULE-004: Exploratory Test Automation*
*Per RULE-020: LLM-Driven E2E Test Generation*
