# SCHEMA-VERIFY-01-v1: Schema Delivery Verification

| Field | Value |
|-------|-------|
| **Category** | quality |
| **Priority** | CRITICAL |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-22 |

## Directive

Any phase that adds or modifies TypeDB schema attributes, entities, or relations MUST include a live schema verification step. Mocked unit tests are NOT sufficient evidence of schema delivery.

## Requirements

### 1. Schema Change = Live Verification Mandatory
- When a phase modifies `schema.tql` or `schema_3x/` files, the phase is NOT DONE until the change is verified in the running TypeDB container
- Verification: query the live TypeDB to confirm the type/attribute/relation exists
- A migration script MUST be run against the live container, not just committed to the repo

### 2. Schema File = Source of Truth
- `schema.tql` MUST always reflect what the running TypeDB contains
- Dynamic migrations (scripts that add schema at runtime) MUST also update `schema.tql`
- Schema drift (live DB has attributes not in schema.tql, or vice versa) is a CRITICAL bug

### 3. Evidence of Delivery
- Phase completion evidence MUST include one of:
  - TypeDB query result showing the new type exists
  - Migration script output showing success
  - MCP tool call that uses the new schema and succeeds
- Mock test results are necessary but NOT sufficient

## Anti-Patterns
- Marking a phase DONE after only writing code and mocked tests
- Creating migration scripts but never running them
- Assuming schema.tql changes are automatically applied to the running container
- Deferring schema verification as a "known limitation"

## Rationale

EPIC-GOV-TASKS-V2 Phase 9a added `document-references-task` relation to `schema.tql` but never applied it to the running TypeDB. 16 unit tests passed (all mocked). The failure was only discovered 2 phases later when MCP tools failed at runtime. The emotional cost to the operator of discovering deferred quality debt exceeds the cost of verification at delivery time.

## Related Rules
- TEST-LIVE-DB-01-v1 (integration tests must fail loudly)
- DELIVER-VERIFY-01-v1 (features must be verified against running system)
- TEST-E2E-01-v1 (3-tier mandatory testing)
