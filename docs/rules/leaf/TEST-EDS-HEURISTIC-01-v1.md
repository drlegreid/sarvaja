# TEST-EDS-HEURISTIC-01-v1: EDS Heuristic Coverage Requirements

| Field | Value |
|-------|-------|
| **Category** | Testing |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-21 |

## Directive

EDS (Exploratory Dynamic Specification) validation gates MUST include at least one scenario per heuristic category. CRUD-only EDS is necessary but NOT sufficient.

## Requirements

### 1. Required Heuristic Categories

Every EDS spec MUST cover these 5 categories in addition to CRUD:

| Category | What to Validate |
|----------|-----------------|
| **DATA_MODEL** | Field propagation across all layers (TypeDB → service → route → UI), enum consistency, auto-generated field correctness |
| **UX_DEFAULTS** | Sort order defaults, filter dropdown values, empty state messages, column sizing |
| **CROSS_NAV** | Linked entities are clickable, bidirectional navigation, back-button context, missing entity errors |
| **SEARCH** | Server-side execution, pagination interaction, structured syntax support |
| **FIELD_INTEGRITY** | No null fields needing defaults, no embedded metadata in wrong fields, timestamp ordering, status normalization |

### 2. Coverage Verification

- `governance/eds/heuristic_categories.py` defines `HEURISTIC_CATEGORIES` dict
- `analyze_eds_coverage(scenario)` returns list of missing categories
- EDS spec must have explicit pass/fail per category

### 3. EDS Spec Format

Each EDS spec (per TEST-EXPLSPEC-01-v1) must include a heuristic coverage table:

```markdown
## Heuristic Coverage
| Category | Scenario | Result |
|----------|----------|--------|
| DATA_MODEL | New field in API response | PASS |
| UX_DEFAULTS | Default sort order | PASS |
| CROSS_NAV | Task→Session click | PASS |
| SEARCH | Server-side search | PASS |
| FIELD_INTEGRITY | No null priority | PASS |
```

## Rationale

EPIC-GOV-TASKS-V2 ran 3 EDS gates (Phases 6, 6c, 9b) that caught CRUD bugs but missed 8 concerns related to data model, UX defaults, navigation, search, and field integrity. These were only discovered during manual review, proving that CRUD-only EDS is insufficient.

## Evidence

- Gap analysis: `docs/backlog/specs/EDS-TASKS-V2-HEURISTICS-2026-03-21.eds.md`
- Category definitions: `governance/eds/heuristic_categories.py`
- Tests: `tests/unit/test_eds_heuristic_categories.py` (10 tests)

## Related Rules
- TEST-EXPLSPEC-01-v1 (EDS 3-layer spec format)
- TEST-E2E-01-v1 (3-tier mandatory testing)
- TEST-CVP-01-v1 (continuous validation pipeline)
