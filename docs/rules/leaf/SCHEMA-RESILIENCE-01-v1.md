# SCHEMA-RESILIENCE-01-v1: External Data Schema Resilience

| Field | Value |
|-------|-------|
| **Rule ID** | SCHEMA-RESILIENCE-01-v1 |
| **Category** | quality |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-20 |

## Directive

When ingesting data from external sources (e.g., Claude Code JSONL sessions), the pipeline MUST handle schema changes gracefully:

1. **Unknown fields** MUST be logged and ignored — never crash
2. **Missing expected fields** MUST use defaults — never crash
3. **Unknown entry types** MUST be preserved with `type='unknown'` — never skipped
4. **Schema detection** (`detect_entry_schema()`) MUST record field sets per session for diagnostics
5. `EXPECTED_COMMON_FIELDS` and `EXPECTED_FIELDS_BY_TYPE` constants define the baseline schema — deviations are warnings, not errors

## Implementation

```python
# cc_session_scanner.py
def detect_entry_schema(entry: dict) -> dict:
    """Detect schema version/fields for a JSONL entry."""
    entry_type = entry.get("type", "unknown")
    known_fields = EXPECTED_FIELDS_BY_TYPE.get(entry_type, set())
    actual_fields = set(entry.keys())
    return {
        "type": entry_type,
        "known_fields": actual_fields & known_fields,
        "extra_fields": actual_fields - known_fields - EXPECTED_COMMON_FIELDS,
        "missing_fields": known_fields - actual_fields,
    }
```

## Rationale

External tools like Claude Code can change their JSONL format at any time without notice. During P2-10f (2026-03-19), schema resilience tests were added to verify the ingestion pipeline handles:
- Extra fields from future CC versions
- Missing fields from older CC versions
- Unknown entry types from new CC features

Without this rule, a CC update could silently break all session ingestion.

## Related Rules

- DATA-INGEST-01-v1: JSONL ingestion service (timestamp passthrough)
- TEST-FIXTURE-01-v1: Production-Faithful Test Fixtures
- TEST-E2E-01-v1: Data Flow Verification
