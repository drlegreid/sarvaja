# Session Evidence: Playwright MCP & GAP-TRAME-001 Resolution

**Date:** 2026-01-10
**Session Type:** Integration Fix
**Agent:** Claude Opus 4.5

---

## Summary

Resolved Playwright MCP configuration and fixed GAP-TRAME-001 (nav-infra not rendering).

---

## Reasoning Chain

### 1. Problem: Playwright MCP Not Working

**Context:** User migrated to xubuntu, npx command unavailable.

**Hypothesis 1:** Node.js not installed
- **Evidence:** `which npx` returned empty
- **Action:** Installed nvm + Node.js v20.19.6
- **Result:** Node.js installed at `~/.config/nvm/versions/node/v20.19.6/`

**Hypothesis 2:** Wrong package name
- **Evidence:** `@anthropic-ai/mcp-server-playwright` returned 404
- **Action:** Searched npm registry, found `@playwright/mcp`
- **Result:** Correct package identified

**Hypothesis 3:** Browser not found
- **Evidence:** Error: "Chromium distribution 'chrome' is not found"
- **Action:** Added `--browser firefox` and `--executable-path` flags
- **Result:** Firefox from Python Playwright cache used successfully

**Final Config:**
```json
{
  "playwright": {
    "type": "stdio",
    "command": "/home/oderid/.config/nvm/versions/node/v20.19.6/bin/npx",
    "args": ["-y", "@playwright/mcp@latest", "--browser", "firefox", "--executable-path", "/home/oderid/.cache/ms-playwright/firefox-1497/firefox/firefox"],
    "env": {
      "PLAYWRIGHT_BROWSERS_PATH": "/home/oderid/.cache/ms-playwright"
    }
  }
}
```

---

### 2. Problem: GAP-TRAME-001 (nav-infra Not Rendering)

**Context:** Infrastructure Health view created but nav item missing from UI.

**Hypothesis 1:** View not registered
- **Evidence:** `views/__init__.py` includes `build_infra_view`
- **Result:** View correctly registered

**Hypothesis 2:** Duplicate NAVIGATION_ITEMS definitions
- **Evidence:**
  - `constants.py` line 59: 12 items (NO Infrastructure)
  - `navigation.py` line 12: 13 items (HAS Infrastructure)
- **Root Cause:** Dashboard imports from `constants.py`, which was missing Infrastructure
- **Action:** Added Infrastructure to `constants.py`:
  ```python
  {'title': 'Infrastructure', 'icon': 'mdi-server', 'value': 'infra'},  # GAP-INFRA-004
  ```
- **Result:** Infrastructure now renders (confirmed via Playwright MCP)

---

## Evidence Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Screenshot (before) | `.playwright-mcp/nav-items-evidence.png` | 12 nav items |
| Screenshot (after) | `.playwright-mcp/infra-view-fixed.png` | 13 nav items + infra view |

---

## Files Modified

| File | Change |
|------|--------|
| `~/.claude.json` | Playwright MCP config with Firefox |
| `.claude/MCP.md` | Documentation updated |
| `agent/governance_ui/state/constants.py` | Added Infrastructure nav item |
| `docs/gaps/GAP-INDEX.md` | Marked GAP-TRAME-001 and GAP-INFRA-004 as RESOLVED |

---

## Decisions Made

| Decision | Rationale | Confidence |
|----------|-----------|------------|
| Use Firefox over Chrome | Python Playwright has Firefox cached; Chrome requires sudo install | 0.95 |
| Fix constants.py not navigation.py | Dashboard imports from constants.py; fix at source | 0.99 |
| Use nvm for Node.js | No sudo access; nvm allows user-space installation | 0.90 |

---

## Open Questions for Future Sessions

1. Should we consolidate NAVIGATION_ITEMS to single source of truth?
2. Is there a way to auto-detect such duplication via linting?
3. Can Playwright MCP use system Chromium (`/snap/bin/chromium`) instead?

---

## Related

- **GAPs:** GAP-TRAME-001 (RESOLVED), GAP-INFRA-004 (RESOLVED)
- **Rules:** RULE-037 (Fix Validation Protocol)
- **R&D:** TOOL-010 (MCP via SSE transport)

---

## R&D Integration Validation

### MCP Tool Integration Status

| MCP Server | Status | Tools Tested |
|------------|--------|--------------|
| governance-core | OK | query_rules, create_rule, get_rule |
| governance-tasks | OK | list_all_tasks (74 returned) |
| governance-sessions | OK | list_sessions (10 available) |
| governance-agents | OK | list_agents |
| playwright | OK | navigate, click, screenshot |

### TypeDB Data Verification

| Entity | Count | Status |
|--------|-------|--------|
| Rules | 29 | Includes new 037-040 |
| Tasks | 74 | Linked to rules/sessions |
| Sessions | 10 | Evidence files tracked |
| Agents | 3 | Trust scores available |

### New Rules Created

| Rule | Name | Category |
|------|------|----------|
| RULE-037 | Fix Validation Protocol | operational |
| RULE-038 | Single Source of Truth | architecture |
| RULE-039 | Context Compression Standard | operational |
| RULE-040 | Session Reasoning Audit Trail | governance |

### Integration Findings

1. **MCP Split (TOOL-007):** 4-server architecture working correctly
2. **TypeDB Queries:** Inference engine returning linked entities
3. **Session Evidence:** Auto-discovered from evidence/ directory
4. **UI Integration:** Trame dashboard renders data from APIs

### Gaps Identified & Resolved

| Gap | Issue | Status |
|-----|-------|--------|
| GAP-TRAME-001 | Duplicate NAVIGATION_ITEMS | RESOLVED |
| GAP-SYNC-001 | governance_sync_status returns typedb_count=0 | RESOLVED |
| GAP-SERIAL-001 | datetime serialization error in list_all_tasks | RESOLVED |
| - | TypeDB created_date fields are null | MEDIUM |
| - | Session summaries showing "No summary available" | LOW |

---

## Bug Fixes (Session Continuation)

### 3. Problem: GAP-SYNC-001 (typedb_count=0)

**Context:** governance_sync_status MCP tool returned 0 for all TypeDB entity counts despite data existing.

**Root Cause:** TypeDBClient instantiated but `connect()` never called.

**Evidence:**
```python
# Before (broken):
client = TypeDBClient()
typedb_rules = set()
# connect() missing - queries fail silently

# After (fixed):
client = TypeDBClient()
client.connect()  # ADDED
```

**Fix Location:** `governance/mcp_tools/workspace.py` lines 297-298

---

### 4. Problem: GAP-SERIAL-001 (datetime serialization)

**Context:** governance_list_all_tasks crashed with "Object of type datetime is not JSON serializable"

**Root Cause:** `asdict()` preserves datetime objects, but `json.dumps()` has no default handler.

**Evidence:**
```python
# Before (broken):
return json.dumps({"tasks": [asdict(t) for t in tasks]}, indent=2)

# After (fixed):
return json.dumps({"tasks": [asdict(t) for t in tasks]}, indent=2, default=str)
```

**Fix Locations:** Added `default=str` to 8 locations across:
- `governance/mcp_tools/tasks_crud.py` (3 locations)
- `governance/mcp_tools/agents.py` (3 locations)
- `governance/mcp_tools/trust.py` (1 location)

**Verification:** governance_list_all_tasks now returns 74 tasks successfully.

---

## Updated Metrics

| Entity | Before | After |
|--------|--------|-------|
| Tasks synced | 14 | 74 |
| Rules linked | 36 | 41 |
| Gaps resolved | 2 | 4 |

---

## E2E Data Integrity Audit (Session Continuation)

### 5. Entity Linkage Validation

| Relation | Coverage | Status |
|----------|----------|--------|
| Task→Session | 3/74 (4%) | ⚠️ LOW |
| Task→Agent | 0/74 (0%) | ❌ MISSING |
| Task→Rules | ~30/74 (40%) | ✅ GOOD |
| Task→Gap | ~25/74 (34%) | ✅ GOOD |

### 6. Agent Workflow R&D Status

All ORCH-* tasks completed:
- ORCH-001: Orchestration Agent design ✅
- ORCH-002: Task polling (31 tests) ✅
- ORCH-003: Task claim/lock ✅
- ORCH-004: Agent delegation (35 tests) ✅
- ORCH-005: Rules Curator (22 tests) ✅
- ORCH-006: Agent Chat UI (33 tests) ✅
- ORCH-007: Task execution viewer (26 tests) ✅

### 7. MCP Tool Validation

| Tool | Status |
|------|--------|
| governance_list_all_tasks | ✅ 74 tasks |
| governance_list_tasks (filtered) | ✅ Works |
| governance_query_rules | ✅ Works |
| governance_get_document | ✅ Works |
| governance_list_documents | ✅ 12 rule docs |
| governance_evidence_search | ❌ 0 results |

### 8. New Gaps Identified

| Gap | Issue | Priority |
|-----|-------|----------|
| GAP-LINK-001 | Task→Agent 0% | HIGH |
| GAP-LINK-002 | Task→Session 4% | MEDIUM |
| GAP-SEARCH-001 | Semantic search empty | MEDIUM |

---

*Evidence per RULE-001: Session Evidence Logging*
*Reasoning per RULE-040: Session Reasoning Audit Trail*
