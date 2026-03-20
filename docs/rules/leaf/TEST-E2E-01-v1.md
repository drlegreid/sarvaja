# TEST-E2E-01-v1: Data Flow Verification Protocol

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `e2e`, `data-flow`, `verification`, `ui`, `gherkin`

---

## Directive

When modifying data flow (controller → API → UI), verification MUST include all three tiers. Unit tests with mocks prove interface contracts only — they do NOT prove the pipeline works end-to-end.

**Tier 3 (Visual) MUST use the Gherkin-first workflow:** Author Gherkin specs → Generate EPIC tasks → Execute via Playwright. Passive screenshots without CRUD interaction are PROHIBITED.

---

## Mandatory Verification Tiers

| Tier | What | How | Proves |
|------|------|-----|--------|
| 1. Unit | Mock-based tests pass | `pytest tests/unit/ -q` | Code compiles, interfaces match |
| 2. Integration | Real API returns correct data | `rest-api` MCP tool or `curl` against running API | Endpoint returns expected JSON |
| 3. Visual CRUD | UI controls work end-to-end | `playwright` MCP tools per Gherkin specs | User can create, read, update, delete through UI |

**ALL THREE TIERS ARE REQUIRED.** Skipping Tier 2 or 3 is a CRITICAL violation.

### Exploratory Integration Testing (MANDATORY)

After implementation, Tier 2 and Tier 3 MUST include **exploratory testing** — not just happy-path verification:

**Tier 2 Exploratory (rest-api MCP):**
- Hit the new/modified endpoint with valid data → verify 200 + correct response shape
- Hit with edge cases: empty results, large offsets, non-existent IDs → verify graceful handling
- Test related endpoints for regressions → verify existing features still work
- Use `mcp__rest-api__test_request` for all API verification

**Tier 3 Exploratory (playwright MCP):**
- Navigate to the affected UI tab → verify data renders
- Click into detail views → verify drill-down works
- Exercise filters, pagination, sorting → verify controls respond
- Test the full user journey: list → detail → back → next page
- Use `mcp__playwright__browser_snapshot` + `browser_click` + `browser_take_screenshot`

**Exploratory testing catches bugs that scripted tests miss** — e.g., Pydantic model vs dict type mismatches that only surface through real API calls (BUG-TASK-SESSION-500-001, 2026-02-15).

---

## Tier 3: Gherkin-First Workflow (MANDATORY)

Tier 3 visual verification follows a strict 5-step process:

```
1. SPEC    → Author Gherkin scenarios in docs/backlog/specs/E2E-T3-*.gherkin.md
             - Cover all CRUD operations (Create, Read, Update, Delete)
             - Cover all filter/search controls
             - Cover navigation and drill-down flows
             - Include cleanup scenario for test data

2. EPIC    → Generate EPIC task breakdown from specs
             - Each feature → one EPIC task with scenario count
             - Link to Gherkin spec file
             - Include domain, priority, acceptance criteria

3. EXECUTE → Run each scenario via Playwright MCP tools
             - browser_navigate → browser_snapshot → browser_click/type/fill
             - Assert state changes (list counts, row presence, field values)
             - Use browser_wait_for for async Trame rendering

4. EVIDENCE → Capture screenshot per scenario
             - evidence/test-results/E2E-T3-{FEATURE}-{SCENARIO}.png
             - Screenshot AFTER state change, not just page load

5. CLOSE   → Mark EPIC task DONE, update TypeDB task status
```

### Anti-Pattern: Superficial Screenshots (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Navigate to tab + take screenshot | Exercise CRUD controls: click Add, fill form, submit, verify result |
| Screenshot proves page renders | CRUD interaction proves controls work end-to-end |
| "Sessions list shows data" | "Created session via form, verified in list, edited, deleted, confirmed removal" |
| Passive observation | Active interaction + state change verification |

---

## Mandatory E2E Scenarios (Added 2026-03-20)

The following scenarios MUST have E2E test coverage. These are not optional — they represent critical data pipeline paths proven by P2-10 work.

| # | Scenario | What to Test | Test File |
|---|----------|-------------|-----------|
| 1 | JSONL Ingestion Pipeline | Scan CC sessions, extract metadata, stream transcript entries | `tests/e2e/test_ingestion_pipeline_e2e.py` |
| 2 | Transcript Rendering (4 tiers) | JSONL → synthetic → evidence → empty, with correct `source` attribution | `tests/e2e/test_session_transcript_e2e.py` |
| 3 | Scheduler Discovery | Drop JSONL file → watcher/scheduler detects → session appears in API + dashboard | `tests/e2e/test_scheduler_discovery_e2e.py` |
| 4 | Schema Resilience | Unknown entry types + extra fields do NOT crash ingestion | `tests/e2e/test_scheduler_discovery_e2e.py` (schema tests) |
| 5 | Data Integrity | CC sessions have JSONL transcripts, tool counts match, timestamps valid | `tests/e2e/test_data_integrity_e2e.py` |

### Evidence (P2-10f, 2026-03-19)

- 76 E2E tests across 4 test files (all pass/skip/xfail — 0 unexpected)
- Schema detection: `cc_session_scanner.py` with `detect_entry_schema()` + 27 TDD unit tests
- Factory: `tests/fixtures/cc_jsonl_factory.py` with 8 builder methods (per TEST-FIXTURE-01-v1)

---

## Trigger Conditions

This rule applies when ANY of these are modified:

- Controller files (`agent/governance_ui/controllers/*.py`)
- Route/endpoint files (`governance/routes/**/*.py`)
- State transform files (`agent/governance_ui/state/*.py`)
- View files that read state (`agent/governance_ui/views/**/*.py`)
- Service layer files that endpoints call (`governance/services/*.py`)

---

## Verification Sequence

```
1. Unit tests:     .venv/bin/python3 -m pytest tests/unit/ -q
2. Container:      podman restart sarvaja-dashboard (or rebuild if Dockerfile changed)
3. API explore:    rest-api MCP → test_request(endpoint, method, params)
                   - Test happy path + edge cases + error paths
4. Gherkin specs:  Author/update docs/backlog/specs/E2E-T3-*.gherkin.md
5. UI explore:     playwright MCP → navigate → snapshot → click → verify state changes
                   - Test list → detail → back → pagination → filters
6. Evidence:       Save screenshots as evidence/test-results/E2E-T3-*.png
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| "9731 unit tests pass, we're done" | Run integration + visual CRUD verification too |
| Mock the function you just changed | Test the real function via real API call |
| Trust that UI will render data because API returns it | Exercise UI controls via Playwright CRUD |
| Skip container rebuild after code changes | Dashboard has NO hot-reload — MUST rebuild |
| Declare victory on mocked test pass | The mock proves YOUR MOCK works, not the code |
| Take passive screenshots as Tier 3 proof | CRUD interactions with state change assertions |

---

## Root Cause (2026-02-12 Incident)

Six data pipelines were "fixed" with unit tests passing (7617/7617). But:
- `/tools` endpoint crashed with `FileNotFoundError` in container (mocked in tests)
- Evidence files never populated in UI (controller never called evidence endpoint)
- File viewer had no markdown rendering (render_markdown existed but wasn't wired)

All discoverable in <5 minutes with `curl` + Playwright CRUD. All invisible to unit tests.

---

## Heuristic Check

**H-TEST-E2E-001**: When files in `controllers/` or `routes/` are modified in a commit, verify that the session evidence includes at least one `rest-api` MCP call or `curl` output AND one `playwright` MCP interaction screenshot (showing state change, not just page load).

---

*Per TEST-FIX-01-v1: Fix Validation Protocol*
*Per TASK-EPIC-01-v1: EPIC-driven task comprehension*
