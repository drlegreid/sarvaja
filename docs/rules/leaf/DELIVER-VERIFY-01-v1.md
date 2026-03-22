# DELIVER-VERIFY-01-v1: Feature Delivery Verification

| Field | Value |
|-------|-------|
| **Category** | quality |
| **Priority** | CRITICAL |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-22 |

## Directive

A feature is NOT DONE until verified against the running system. Design docs, code, migration scripts, and mocked tests are necessary but NOT sufficient evidence of delivery.

## Requirements

### 1. Verification Hierarchy
A feature requires ALL of these to be marked DONE:

| Level | What | Evidence |
|-------|------|----------|
| L1 | Code written | Files in git |
| L2 | Unit tests pass | pytest output (mocked) |
| L3 | Schema applied (if applicable) | Live TypeDB query result |
| L4 | MCP tool works (if applicable) | Successful MCP call with real response |
| L5 | API returns correct data | curl/rest-api MCP with real response |

Levels L1-L2 are necessary but NOT sufficient. If a feature touches TypeDB, L3+ are MANDATORY.

### 2. "Known Limitation" is Not Deferral
- If a feature doesn't work against the running system, it is NOT DONE
- Labeling a broken feature as a "known limitation" and deferring it is FORBIDDEN
- The correct action: keep the phase IN_PROGRESS until the feature works end-to-end
- If the fix requires a different phase, create a BLOCKER dependency

### 3. Emotional Cost Awareness
- Deferred quality debt creates compounding emotional cost for the operator
- Discovering that "completed" work doesn't actually work is more damaging than taking extra time to verify at delivery
- Quality over speed: it is better to deliver 1 verified feature than 3 features with "known limitations"

## Anti-Patterns
- "Works in tests, we'll verify later"
- "Known limitation — deferred to next phase"
- Design docs marked COMPLETE before implementation verified
- Migration scripts committed but never executed

## Rationale

EPIC-GOV-TASKS-V2 experienced a cascade failure: Phase 9a declared BUG-TASK-DOC-001 fixed, Phase 9e declared `task_link_document` failure a "known limitation deferred to Rules V3". The actual root cause was that a schema relation was never applied to the running TypeDB. This was caught only through manual operator review, not by any automated gate. The operator's investment of emotional energy was undermined by deferred verification.

## Related Rules
- SCHEMA-VERIFY-01-v1 (schema delivery verification)
- TEST-LIVE-DB-01-v1 (integration tests must fail loudly)
- TEST-E2E-01-v1 (3-tier mandatory testing)
- COMM-PROGRESS-01-v1 (progress reporting must include impact)
