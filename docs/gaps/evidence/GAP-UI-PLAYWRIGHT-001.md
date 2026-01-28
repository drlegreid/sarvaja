# GAP-UI-PLAYWRIGHT-001: UI Data Quality & Leniency Gaps Found via Playwright Exploration

**Status:** OPEN | **Priority:** MEDIUM | **Created:** 2026-01-28
**Rule:** UI-DESIGN-02-v1, ARCH-EBMSF-01-v1

---

## Summary

Exploratory Playwright testing of the Trame Governance Dashboard (localhost:8081) revealed
data quality issues visible in the UI and potential test assertion gaps.

## Views Explored

| View | Status | Findings |
|------|--------|----------|
| Rules (list) | OK | 36 rules loaded, search/filter works |
| Rules (detail) | DATA GAP | "Implementing Tasks: 0" for all rules |
| Tasks | OK | 50 tasks with pagination, tabs, filters |
| Agents | DATA GAP | 3 duplicate "Test Agent" entries |
| Decisions | DATA GAP | All decisions show "No date" / "N/A" |
| Trust | DATA GAP | Duplicate agents inflate total (11 vs 8 unique) |
| Search | OK | ChromaDB evidence search returns results |
| Infrastructure | OK | Health status accurate (Podman/TypeDB/ChromaDB OK) |

## Findings

### 1. Duplicate Agents (Agents + Trust views)

"Test Agent" (test-agent) appears 3 times in both `/api/agents` and the UI:
- Trust leaderboard shows ranks 8, 9, 10 all as "Test Agent | test-agent | 80%"
- Total count inflated: "11 agents registered" should be 8 unique
- Avg trust score skewed by duplicates

**Evidence:** Visible in Agents list and Trust Leaderboard.

### 2. Null Decision Dates (Decisions view)

All 4 decisions show "No date" in the list and "Date: N/A" in detail:
- DECISION-002 (Mem0 Knowledge Governance): "No date", Status: SUPERSEDED
- Same pattern for all other decisions

**Evidence:** Decision detail view shows `decision_date: null` from API.

### 3. Rules Have No Implementing Tasks (Rule Detail)

Every rule detail shows "Implementing Tasks: 0" with "No tasks implementing this rule":
- ARCH-EBMSF-01-v1: 0 implementing tasks
- This suggests `rule_implements` relations are missing from TypeDB

**Evidence:** Rule detail view for ARCH-EBMSF-01-v1.

### 4. UI Functional Checks (Passing)

| Feature | Result |
|---------|--------|
| Navigation (15 views) | All clickable, all load |
| Rules search (text filter) | Filters correctly (tested "safety") |
| Rules status/category filters | Present and interactive |
| Evidence search | Returns 5 results for "governance" |
| Task pagination | "Items per page" + page navigation works |
| Task tabs (All/Available/My Tasks/Completed) | All tabs present |
| Infrastructure health display | Accurate (OK/OFF states) |
| Trace bar (bottom) | Shows event count + last API call |
| Rule detail → back navigation | Works correctly |

### 5. Missing UI Test Coverage

| Scenario | Not Tested |
|----------|-----------|
| Rules search returns 0 results | Edge case not covered |
| Task claim via UI button | Claim button disabled, not tested active state |
| Decision edit/delete | Not covered in existing robot tests |
| Agent detail click-through | Not covered |
| Infrastructure "Start" buttons | Not covered (LiteLLM/Ollama start) |

## Remediation

1. Deduplicate TEST-AGENT-001 entries in TypeDB (3 → 1)
2. Populate `decision_date` for all 4 decisions in TypeDB
3. Create `rule_implements` relations linking tasks to rules in TypeDB
4. Add robot e2e tests for UI CRUD operations (decisions, agents)
5. Add edge case tests for empty search results

---

*Per UI-DESIGN-02-v1: UI/UX Design Standards, ARCH-EBMSF-01-v1: Test Evidence Structure*
