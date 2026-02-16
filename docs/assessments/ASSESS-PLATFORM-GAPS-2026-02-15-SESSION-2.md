# Platform Assessment: Session 2 — P0-P6 Gap Analysis & Fixes

**Date:** 2026-02-15
**Session:** Continuation from ASSESS-PLATFORM-GAPS-2026-02-15
**Methodology:** TDD (Red → Green → Refactor) + Static Analysis

---

## Summary

| Priority | Issue | Status | Tests | Files Changed |
|----------|-------|--------|-------|---------------|
| **P0** | Session evidence not auto-attached | FIXED | 21 pass | `session_evidence.py` (new), `sessions_lifecycle.py` |
| **P1** | Test results not loading on dashboard | VERIFIED | 10 pass | Pipeline verified working at all levels |
| **P2** | Godot games missing from projects | FIXED | 12 pass | `cc_session_scanner.py`, `dashboard_data_loader.py` |
| **P3** | Auto-ingest on startup (architecture) | ANALYZED | — | See analysis below |
| **P4** | Real-time monitoring precision | ANALYZED | — | See analysis below |
| **P5** | Audit trail usability | ANALYZED | — | See analysis below |
| **P6** | Decision log vs rules taxonomy | ANALYZED | — | See analysis below |

**Total new tests:** 43 (21 + 10 + 12)

---

## P0: Session Evidence Auto-Generation (FIXED)

### Root Cause
`end_session()` in `sessions_lifecycle.py` does NOT auto-generate evidence documents when `evidence_files=None`. Chat sessions generate evidence via `session_bridge.py`, but REST API and MCP sessions have no evidence attached, leaving an audit trail gap.

### Solution
Created `governance/services/session_evidence.py` — a pure data-collation service (NO LLM):

| Function | Purpose |
|----------|---------|
| `compile_evidence_data()` | Gathers tool_calls, decisions, tasks from session dict |
| `render_evidence_markdown()` | Generates markdown with summary tables |
| `generate_session_evidence()` | Writes `{session_id}.md` to evidence/ (idempotent) |

**Wired into** `end_session()` in both TypeDB path and fallback path:
- When `evidence_files=None` → auto-generates evidence
- When `evidence_files` provided → skips auto-generation
- Idempotent: won't overwrite existing evidence files

### Test Coverage (21 tests)
- `TestEvidenceGeneratorServiceExists` (3): Import verification
- `TestCompileEvidenceData` (5): Data extraction, duration computation, missing fields
- `TestRenderEvidenceMarkdown` (6): Markdown structure, sections, tool counts
- `TestGenerateSessionEvidence` (5): File creation, naming, idempotency, active session skip
- `TestEndSessionAutoEvidence` (2): Integration with `end_session()`

---

## P1: Test Results Loading (VERIFIED WORKING)

### Analysis
The test results pipeline was verified working at all levels:

| Level | Status | Evidence |
|-------|--------|----------|
| **Store** | 1,644 persisted JSON files load correctly | `_load_persisted_results()` reads last 50 |
| **API** | HTTP 200, returns 3 heuristic runs | `curl localhost:8082/api/tests/results?limit=3` |
| **Controller** | Sets `state.tests_recent_runs` correctly | Unit test verified |
| **UI** | Declared in initial state as `[]` | `state/initial.py:338` |

### Root Cause of User-Perceived Issue
Dashboard Trame has **NO hot-reload** — requires container restart to pick up `agent/` code changes. The pipeline works, but the running container may have stale UI code.

### Test Coverage (10 tests)
- `TestLoadTestsStartup` (3): API success, error, connection refused
- `TestRunnerStorePersistence` (4): Read JSON, limit 50, empty dir, corrupt files
- `TestTestsControllerLoadData` (1): Controller populates state
- `TestListTestResultsAPI` (2): API format, limit parameter

---

## P2: Missing Game Projects (FIXED)

### Root Cause
`discover_cc_projects()` only scans `~/.claude/projects/` and requires JSONL session files. The Godot game projects have:
- No CC project directories (Claude Code sessions were in different project contexts)
- Both `project.godot` markers exist at filesystem level

### Solution
Added `discover_filesystem_projects()` to `cc_session_scanner.py`:

```
_PROJECT_MARKERS = [project.godot, CLAUDE.md, package.json, Cargo.toml, go.mod, pyproject.toml, setup.py]
```

- Scans configurable parent directories for subdirectories with project markers
- Auto-detects type via `detect_project_type()` (returns "gamedev" for Godot)
- Deduplicates against existing paths and project IDs
- Wired into `_load_projects()` — scans parent + grandparent of known projects

### Test Coverage (12 tests)
- `TestFilesystemDiscoveryExists` (2): Import, returns list
- `TestDiscoversGodotProjects` (3): Find Godot, multiple games, required fields
- `TestDiscoversOtherProjectTypes` (3): CLAUDE.md, skip hidden, skip empty
- `TestDeduplicationWithCC` (2): Exclude known paths, exclude known IDs
- `TestLoadProjectsIntegration` (2): Real Godot games found, correct ID generation

---

## P3: Auto-Ingest on Startup (ANALYSIS)

### Current Architecture

```
Dashboard Start
  ↓
load_initial_data() [SYNCHRONOUS, blocking]
  ├── _load_rules()       → GET /api/rules
  ├── _load_decisions()   → GET /api/decisions
  ├── _load_sessions()    → GET /api/sessions + compute metrics
  ├── _load_agents()      → GET /api/agents
  ├── _load_tasks()       → GET /api/tasks
  ├── _load_projects()    → GET /api/projects + CC discovery + FS discovery + auto-ingest
  └── _load_tests()       → GET /api/tests/results + CVP status
```

### Pattern: Hybrid Startup + Lazy + Optional Polling

| Pattern | Where | Trigger |
|---------|-------|---------|
| **Eager startup** | `load_initial_data()` | Dashboard init |
| **Lazy per-view** | `on_view_change()` | Tab click |
| **Background poll** | `poll_for_results()` | Test run started |
| **Reactive filter** | `@state.change()` | Filter change |

### Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Simplicity** | Good | Synchronous startup is easy to reason about |
| **Startup latency** | Poor | `_load_projects()` calls `ingest_all()` per project — can take 10s+ |
| **Error isolation** | Moderate | Each `_load_*` is in own try/except, but failure cascades to MCP fallback |
| **Event-driven** | Missing | No event bus; mutations don't notify other views |
| **Scheduler** | Missing | No periodic refresh; data goes stale after load |

### Recommendation
**Short-term:** Move `_auto_ingest_cc_sessions()` to a background thread so it doesn't block dashboard startup.
**Medium-term:** Add a lightweight event bus (in-memory pub/sub) so CRUD mutations in one tab trigger refresh in related tabs.
**Long-term:** Scheduler with configurable intervals for monitoring/audit data freshness.

---

## P4: Real-Time Monitoring Tab (ANALYSIS)

### Data Model

| Component | Data Source | Precision |
|-----------|-----------|-----------|
| Total Events | `monitor_feed.length` | Count of loaded events (limit-bound) |
| Active Alerts | `monitor_alerts.length` | In-memory alerts (not persisted) |
| Violations | `monitor_stats.events_by_type.violation` | Aggregated count |
| Event Feed | `GET /monitor/events` | Cross-process via audit files |
| Top Rules | `get_top_monitored_rules(limit=10)` | Aggregated from events |

### Gaps

| Issue | Severity | Impact |
|-------|----------|--------|
| No data freshness indicator | MEDIUM | User doesn't know when data was last fetched |
| Stats vs feed inconsistency | MEDIUM | Event feed and stats may show different counts |
| Alert persistence | HIGH | Alerts are in-memory only — lost on restart |
| No metric trends | MEDIUM | Shows current counts, not trends over time |

### Actionability Rating: **Moderate**
- Can see violations and their source rules
- Can acknowledge alerts
- Cannot drill down from event to root cause
- Cannot set alerting thresholds

---

## P5: Audit Trail Tab (ANALYSIS)

### Data Model

| Column | Field | Filter |
|--------|-------|--------|
| Timestamp | `timestamp` | No range filter |
| Action | `action_type` | Dropdown filter |
| Entity | `entity_type` | Dropdown filter |
| Entity ID | `entity_id` | Text search |
| Actor | `actor_id` | — |
| Rules Applied | `applied_rules` (comma-joined) | — |
| Correlation | `correlation_id` | Text search |

### Summary Cards
- Total entries, entity types count, action types count, actor count

### Gaps

| Issue | Severity | Impact |
|-------|----------|--------|
| `applied_rules` comma-joined | HIGH | Loses structure; can't drill down to specific rule |
| No timestamp range filter | MEDIUM | Can only browse latest N entries |
| No daily trend visualization | MEDIUM | Summary shows top-level counts only |
| 7-day retention cap | LOW | By design, but limits historical analysis |
| Loading state not reset on error | LOW | `audit_loading = True` stays stuck |

### Usability Rating: **Moderate**
- Useful for recent activity investigation
- Correlation ID enables session tracing
- Filtering works for entity/action types
- Missing time-based analysis capability

---

## P6: Decision Log vs Rules Taxonomy (ANALYSIS)

### Decision vs Rule Comparison

| Aspect | Rules | Decisions |
|--------|-------|-----------|
| **Purpose** | System constraints (enforced) | Strategic choices (recorded) |
| **Fields** | id, name, directive, priority, category, status | id, name, context, rationale, status, options[], selected_option |
| **Linkage** | Dependencies (rules→rules) | Linked rules (decision→rules) + evidence refs |
| **Evidence** | Document path (leaf files) | Session ID, evidence_refs (count only) |
| **Lifecycle** | Active → Deprecated → Archived | PROPOSED → APPROVED/REJECTED |
| **Taxonomy** | 9 categories (SESSION, TEST, GOV, ARCH, etc.) | No category taxonomy |

### Key Insight
Decisions capture **WHY** a rule exists or changed. Rules capture **WHAT** must be followed. The relationship is 1:N (one decision can affect multiple rules).

### Current Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| linked_rules shows count, not rationale | MEDIUM | Can't see why specific rules are affected |
| evidence_refs opaque | MEDIUM | Shows count but no link to actual files |
| No decision history | MEDIUM | Only current status, no state transitions |
| Session link is one-way | LOW | Decision→session but not session→decisions |
| No category taxonomy for decisions | LOW | Unlike rules, decisions have no semantic grouping |

### Rule Application Mechanisms (Taxonomy Analysis)

**Current taxonomy (9 categories, 56 rules):**
```
SESSION (4)  → Session lifecycle enforcement
TEST (7)     → Testing requirements
GOV (6)      → Governance process
ARCH (3)     → Architecture constraints
WORKFLOW (5) → Workflow automation
SAFETY (3)   → Safety checks
CONTAINER (3)→ Container runtime
DOC (4)      → Documentation standards
RECOVER (3)  → Recovery protocols
+ META, REPORT, UI, DATA, MCP, COMM (smaller)
```

**Application Mechanism:**
1. **Heuristic Checks** (31 checks): Automated validation against rules (H-TASK-*, H-SESSION-*, H-RULE-*)
2. **CVP Pipeline** (3 tiers): Tier 1 inline, Tier 2 post-session, Tier 3 sweep
3. **Agent Trust Scores**: Rules influence trust scoring in `governance-agents` MCP
4. **Decision Linking**: `create_decision(rules_applied=["RULE-ID"])` atomically links

**Gap:** No mechanism to apply rules to **specific system components** (e.g., "TEST-GUARD-01 applies to `/governance/` but not `/agent/`"). Rules are global.

### Recommendation
Add a `scope` field to rules that specifies which paths/components they apply to:
```
scope: ["governance/**", "agent/**"]  # or ["*"] for global
```
This enables selective enforcement and reduces noise from rules that don't apply to the current context.

---

## Files Modified

| File | Action | Lines Changed |
|------|--------|--------------|
| `governance/services/session_evidence.py` | NEW | 249 lines |
| `governance/services/sessions_lifecycle.py` | MODIFIED | +20 lines (auto-evidence wiring) |
| `governance/services/cc_session_scanner.py` | MODIFIED | +65 lines (discover_filesystem_projects) |
| `agent/governance_ui/dashboard_data_loader.py` | MODIFIED | +30 lines (FS discovery wiring) |
| `tests/unit/test_session_evidence_auto_generation.py` | NEW | 444 lines (21 tests) |
| `tests/unit/test_p1_test_results_loading.py` | NEW | 210 lines (10 tests) |
| `tests/unit/test_p2_filesystem_project_discovery.py` | NEW | 225 lines (12 tests) |
| `docs/assessments/ASSESS-PLATFORM-GAPS-2026-02-15-SESSION-2.md` | NEW | This document |

---

## Next Steps

1. **Container restart** required to pick up P0/P2 changes in dashboard
2. **Rule scope mechanism** (P6 recommendation) — needs design + TDD
3. **Event bus** (P3 recommendation) — medium-term architectural improvement
4. **Alert persistence** (P4) — store alerts in TypeDB instead of memory
5. **Audit timestamp filter** (P5) — add date range picker to audit view
