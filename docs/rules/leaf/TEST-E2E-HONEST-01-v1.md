---
rule_id: TEST-E2E-HONEST-01-v1
name: Honest E2E — Fix Bugs, Don't Document Around Them
status: ACTIVE
category: quality
priority: CRITICAL
applicability: MANDATORY
---

## Rule

When an E2E test reveals a bug (e.g., a TypeDB query fails, an API returns 400), the correct response is to **fix the bug** — not to mark it as a "known gap", skip the test, or weaken the assertion.

## Rationale

Unit test coverage means nothing if the feature doesn't work end-to-end. Documenting a bug as a "known gap" and moving on creates false confidence: the checklist shows green, but the user experience is broken.

**Origin (2026-03-28):** SRVJ-FEAT-AUDIT-TRAIL-01 P2 — `unlink_task_from_document` returned 400 in E2E tests. Initial response was to mark it as "known gap: pre-existing TypeDB issue" and skip the UNLINK assertion. Root cause investigation revealed a TypeDB 3.x syntax bug (`$rel (role: $x) isa type` → Thing/ThingType conflict on delete). Fix was 3 lines. The "known gap" was laziness, not wisdom.

## Do / Don't

| Don't | Do Instead |
|-------|------------|
| Mark failing E2E as "known gap" | Investigate root cause, fix it |
| Weaken assertions to make tests pass | Fix the code to match the assertion |
| Skip UNLINK/DELETE tests because "TypeDB doesn't support it" | Check the actual TypeDB docs for the correct syntax |
| Declare DONE based on unit tests when E2E fails | E2E pass is the definition of done |

## Enforcement

- Robot Framework suite must have 0 skipped tests tagged `known-gap`
- Any `[Tags] known-gap` in `.robot` files triggers review
- "Known gap" in test comments requires a linked bug ticket with fix ETA
