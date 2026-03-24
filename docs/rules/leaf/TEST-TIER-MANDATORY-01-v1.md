# TEST-TIER-MANDATORY-01-v1: Mandatory 3-Tier Validation

| Field | Value |
|-------|-------|
| **Rule ID** | TEST-TIER-MANDATORY-01-v1 |
| **Category** | OPERATIONAL |
| **Priority** | CRITICAL |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-24 |

## Directive

ALL implementation phases MUST validate at 3 tiers before declaring DONE. No tier may be skipped. "If time permits" is NOT an acceptable qualifier. Skipping a tier requires explicit user approval AND a documented reason linked to the task.

---

## Mandatory Tiers

| Tier | What | Command / Tool | Proves |
|------|------|---------------|--------|
| 1. Unit | Full test suite, 0 regressions | `.venv/bin/python3 -m pytest tests/unit/ -q` | Code compiles, interfaces match, no regressions |
| 2. Integration | Live TypeDB + REST API | `rest-api` MCP or `curl localhost:8082/api/...` | Real data flows correctly through the pipeline |
| 3. E2E | Playwright on live dashboard | `playwright` MCP tools per Gherkin specs | User can interact with UI, state changes persist |

---

## Validation Sequence

```
1. Tier 1: Run full unit suite
   - Count must be >= previous count (no deleted tests)
   - 0 failures, 0 errors
   - Report: "{N} passed, 0 failed"

2. Tier 2: Integration against live services
   - Test new/modified endpoints with valid + edge case data
   - Verify TypeDB persistence (write → read-back)
   - Use WS-TEST-SANDBOX workspace (per TEST-DATA-01-v1)

3. Tier 3: Playwright E2E with screenshot evidence
   - Author Gherkin spec if new feature
   - Execute CRUD interactions (not passive screenshots)
   - Capture evidence: evidence/test-results/E2E-T3-*.png
   - Verify state changes in UI after each action
```

---

## Skip Protocol (EXCEPTIONAL ONLY)

If a tier genuinely cannot run (e.g., container down, external dependency unavailable):

1. Document which tier is skipped and WHY in the task evidence
2. Get explicit user approval before proceeding
3. Create follow-up task: `{PROJECT}-DEBT-{SEQ}: Complete Tier {N} for {feature}`
4. Task CANNOT be marked DONE — use BLOCKED status until tier is completed

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| "Unit tests pass, ship it" | Run all 3 tiers — unit tests prove YOUR MOCKS work |
| "Tier 3 if time permits" | Tier 3 is mandatory, not optional |
| Skip Tier 2 because "the code looks right" | Code looking right ≠ code working right in container |
| Declare DONE without evidence | Screenshot + test count in task evidence |
| Passive screenshot as Tier 3 | CRUD interaction with state change verification |

---

## Root Cause (P13 Incident, 2026-03-22)

Tier tests were skipped during P13 implementation, causing bugs to ship that were trivially catchable with integration testing. Cost: 2 extra phases of rework.

---

## Relationship to Existing Rules

- **TEST-E2E-01-v1**: Defines the 3-tier framework and Gherkin-first workflow. TEST-TIER-MANDATORY-01 makes the "mandatory" aspect explicit and adds the skip protocol.
- **TEST-FIX-01-v1**: TDD workflow (failing test first). Complementary — FIX-01 is about HOW to test, TIER-MANDATORY is about WHEN testing is required.
- **TEST-DATA-01-v1**: Sandbox workspace requirement for Tier 2/3.

---

*Per EPIC-TASK-QUALITY-V3 P13: URL-Based Entity Routing*
