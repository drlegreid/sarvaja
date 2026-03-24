# TEST-BUGFIX-01-v1: Exploratory Bug Detection and 3-Tier Fix Validation Workflow

| Field | Value |
|-------|-------|
| **Category** | quality |
| **Priority** | HIGH |
| **Status** | DEPRECATED — Consolidated into TEST-FIX-01-v1 (37 code refs, broader scope) |
| **Applicability** | MANDATORY |
| **Created** | 2026-02-14 |
| **References** | TEST-E2E-01-v1, COMM-PROGRESS-01-v1 |

## Directive

When fixing bugs discovered through exploratory testing, follow this structured 7-step workflow:

### Step 1: EXPLORE
Run exploratory tests (manual UI + API probing) to discover bugs. Use Playwright for UI verification, curl for API probing.

### Step 2: DETECT
Document each bug with:
- **Symptoms**: What the user sees (business impact)
- **Root Cause**: Technical analysis of the failure
- **Steps to Reproduce**: Exact sequence to trigger the bug
- **Impact**: Business (user-facing) and technical (data integrity) consequences

### Step 3: REGISTER
Create bug tasks via MCP:
```
task_create(task_id="BUG-{AREA}-NNN", task_type="bug", priority="{severity}")
```

### Step 4: PRIORITIZE
Rank bugs by impact severity:
1. Data loss/corruption (CRITICAL)
2. Functional breakage (HIGH)
3. Display/formatting (MEDIUM)
4. Cosmetic (LOW)

Fix in priority order.

### Step 5: TEST (TDD)
Write unit tests BEFORE fixing:
- Cover the exact failure scenario
- Cover edge cases and boundary conditions
- Include regression tests for related functionality

### Step 6: FIX
Implement the fix across ALL affected layers. For TypeDB-backed features, this typically means:
1. TypeDB schema (`.tql` files)
2. Entity dataclass (`entities.py`)
3. Pydantic models (`models.py`)
4. TypeDB CRUD queries (`queries/`)
5. Store conversion (`helpers.py`, `typedb_access.py`)
6. Service layer (`services/`)
7. REST routes (`routes/`)
8. MCP tools (`mcp_tools/`)
9. UI components (`governance_ui/`)

### Step 7: VALIDATE (3-Tier E2E)
Per TEST-E2E-01-v1:

| Tier | Method | Proves |
|------|--------|--------|
| 1. Unit | `pytest tests/unit/ -q` | Code compiles, logic correct |
| 2. Integration | `curl http://localhost:8082/api/{endpoint}` | Data round-trips through real stack |
| 3. Visual | Playwright navigate + screenshot | User sees correct data in UI |

## Loopback Rule

**CRITICAL**: If Tier 2 or Tier 3 reveals NEW bugs (e.g. schema not migrated, asymmetric fallback logic), loop back to Step 2. Never declare done on unit tests alone.

Integration issues rarely surface on the first pass. The workflow is designed to be repeated until all tiers pass cleanly.

## Evidence

### First Application (2026-02-14)

4 bugs detected and fixed using this workflow:

| Bug ID | Severity | Layers Touched | Loop Count |
|--------|----------|----------------|------------|
| BUG-SESSION-DURATION-001 | HIGH | UI controller + data loader | 1 |
| BUG-SESSION-END-001 | MEDIUM | UI data loader | 1 |
| BUG-SESSION-EVIDENCE-001 | HIGH | Service + session bridge + TypeDB | 1 |
| BUG-TASK-TAXONOMY-001 | CRITICAL | 9 layers (full stack) | 2 (schema migration + fallback fix) |

**Loopback example**: BUG-TASK-TAXONOMY-001 passed Tier 1 (unit tests) but failed Tier 2 (TypeDB schema not migrated → insert failed). After schema migration, PUT still returned 404 due to asymmetric fallback logic in `update_task()`. Required 2 additional fixes discovered only through integration testing.
