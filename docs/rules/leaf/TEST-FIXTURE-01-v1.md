# TEST-FIXTURE-01-v1: Production-Faithful Test Fixtures

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `fixtures`, `data-quality`, `mocks`, `production-parity`

---

## Directive

Test fixtures MUST match production data format. No oversimplified mocks that skip more than 20% of real fields. Fixture factories (e.g., `CCJsonlFactory`) MUST generate entries with all production-required fields including timestamps, UUIDs, model names, and nested structures.

Fixtures that omit fields present in production data create false confidence — tests pass but real data breaks the pipeline.

---

## Requirements

### Field Coverage

| Requirement | Threshold |
|-------------|-----------|
| Production fields present in fixture | ≥80% |
| Required fields (timestamps, IDs, types) | 100% |
| Nested structures (tool_use.input, etc.) | Must match production nesting depth |
| Field types (string vs int vs datetime) | Must match production types exactly |

### Fixture Factory Pattern

All test fixtures for data pipeline testing MUST use a factory pattern:

```python
# CORRECT — factory with production-faithful fields
from tests.fixtures.cc_jsonl_factory import CCJsonlFactory

factory = CCJsonlFactory()
entries = factory.build_session(
    entry_count=10,
    include_tool_use=True,
    include_thinking=True
)

# WRONG — oversimplified inline fixture
entries = [{"type": "user_prompt", "message": "hello"}]  # Missing 20+ fields
```

### Validation Checklist

Before merging fixtures, verify against a real production sample:

1. Extract field names from a real CC session JSONL entry
2. Compare against fixture factory output
3. Flag any missing fields >20% threshold
4. Verify nested object structures match

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| `{"type": "tool_use", "name": "Read"}` | Include `id`, `timestamp`, `model`, `input`, `stop_reason`, etc. |
| Hardcode timestamps as strings | Use `datetime.now().isoformat()` or factory-generated |
| Skip `uuid` field in test entries | Generate realistic UUIDs via `uuid.uuid4()` |
| Omit `costUSD`, `durationMs` from result entries | Include all billing/performance fields |
| Test with 2-field dicts when production has 25+ | Use factory that generates all fields |

---

## Root Cause (P2-10d, 2026-03-19)

During JSONL ingestion E2E testing, synthetic test fixtures used 3-5 field entries while production CC JSONL has 25+ fields per entry. This caused:
- `scan_jsonl_metadata()` to miss fields it expected
- `stream_transcript()` to fail on missing nested structures
- Schema detection to report wrong field coverage percentages

Fix: `CCJsonlFactory` in `tests/fixtures/cc_jsonl_factory.py` with 8 builder methods and 25+ fields per entry type.

---

## Heuristic Check

**H-FIXTURE-001**: When a new test file creates inline JSONL/JSON fixtures with fewer than 10 fields per entry, flag for review against production data format.

---

*Per TEST-E2E-01-v1: Data Flow Verification Protocol*
*Per TEST-COMP-01-v1: Comprehensive Testing Protocol*
