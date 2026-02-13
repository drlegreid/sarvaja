# TEST-E2E-01-v1: Data Flow Verification Protocol

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `e2e`, `data-flow`, `verification`, `ui`

---

## Directive

When modifying data flow (controller → API → UI), verification MUST include all three tiers. Unit tests with mocks prove interface contracts only — they do NOT prove the pipeline works end-to-end.

---

## Mandatory Verification Tiers

| Tier | What | How | Proves |
|------|------|-----|--------|
| 1. Unit | Mock-based tests pass | `pytest tests/unit/ -q` | Code compiles, interfaces match |
| 2. Integration | Real API returns correct data | `curl` against running API | Endpoint returns expected JSON |
| 3. Visual | UI renders the data | Playwright screenshot | User actually sees the data |

**ALL THREE TIERS ARE REQUIRED.** Skipping Tier 2 or 3 is a CRITICAL violation.

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
2. Container:      podman compose --profile dev build governance-dashboard-dev
                   podman compose --profile dev restart governance-dashboard-dev
3. API smoke:      curl -s http://localhost:8082/api/{endpoint} | python3 -c "..."
4. UI visual:      Playwright navigate → click → screenshot
5. Evidence:       Save screenshots as e2e-{feature}.png
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| "7617 unit tests pass, we're done" | Run integration + visual verification too |
| Mock the function you just changed | Test the real function via real API call |
| Trust that UI will render data because API returns it | Take a Playwright screenshot to confirm |
| Skip container rebuild after code changes | Dashboard has NO hot-reload — MUST rebuild |
| Declare victory on mocked test pass | The mock proves YOUR MOCK works, not the code |

---

## Root Cause (2026-02-12 Incident)

Six data pipelines were "fixed" with unit tests passing (7617/7617). But:
- `/tools` endpoint crashed with `FileNotFoundError` in container (mocked in tests)
- Evidence files never populated in UI (controller never called evidence endpoint)
- File viewer had no markdown rendering (render_markdown existed but wasn't wired)

All discoverable in <5 minutes with `curl` + Playwright. All invisible to unit tests.

---

## Heuristic Check

**H-TEST-E2E-001**: When files in `controllers/` or `routes/` are modified in a commit, verify that the session evidence includes at least one `curl` command output AND one Playwright screenshot.

---

*Per TEST-FIX-01-v1: Fix Validation Protocol*
