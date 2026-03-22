# TEST-LIVE-DB-01-v1: Integration Tests Must Fail Loudly

| Field | Value |
|-------|-------|
| **Category** | testing |
| **Priority** | CRITICAL |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-22 |

## Directive

Integration tests MUST fail loudly when TypeDB is unavailable during a phase that claims to modify schema. Silent skipping is FORBIDDEN for schema-dependent tests.

## Requirements

### 1. No Silent Skips for Schema Tests
- Tests that validate TypeDB schema (relations, attributes, entities) MUST NOT use `pytest.skip()` when TypeDB is unreachable
- Instead: fail with a clear message: "TypeDB unavailable — schema verification CANNOT be skipped"
- The `typedb_available` fixture in `conftest.py` MUST distinguish between:
  - "TypeDB is optional for this test" → skip OK
  - "TypeDB is required for schema verification" → MUST FAIL

### 2. Mock vs Live Distinction
- Unit tests: mocking TypeDB is acceptable (tests code logic)
- Schema tests: MUST connect to live TypeDB (tests actual database state)
- A test file that validates schema alignment MUST NOT import `MagicMock` for the TypeDB client

### 3. Test Naming Convention
- Tests requiring live TypeDB: prefix with `test_live_` or in `tests/integration/`
- Tests that are mock-only: standard naming in `tests/unit/`
- CI/CD: `tests/integration/` runs only when TypeDB container is up

## Anti-Patterns
- `conftest.py` fixtures that silently skip ALL tests when TypeDB is down
- Schema alignment tests that parse `.tql` files with regex but never query TypeDB
- 10,000+ mocked tests creating false confidence about database state

## Rationale

The Sarvaja platform has 10,515+ unit tests, all mocking TypeDB. Integration tests silently skip when TypeDB is unreachable. This created a blind spot where schema changes were declared DONE based on mocked test results while the running database had none of the changes applied.

## Related Rules
- SCHEMA-VERIFY-01-v1 (schema delivery verification)
- DELIVER-VERIFY-01-v1 (running system verification)
- TEST-E2E-01-v1 (3-tier mandatory testing)
