# GAP-TEST-LENIENCY-001: Test Leniency Gaps Found via Exploratory API Testing

**Status:** OPEN | **Priority:** MEDIUM | **Created:** 2026-01-28
**Rule:** ARCH-EBMSF-01-v1, TEST-STRUCT-01-v1

---

## Summary

Exploratory REST API testing revealed leniency patterns where tests accept overly broad conditions,
reducing their ability to catch regressions.

## Findings

### 1. Health Check Accepts 503 (governance_crud.robot:26)

```robot
# LENIENT: Accepts both success AND failure
Should Be True    ${status_code} == 200 or ${status_code} == 503

# STRICT: Health should be 200 when services are running
Should Be Equal As Integers    ${status_code}    200
...    msg=Health check returned ${status_code}, expected 200
```

### 2. Count >= 0 is Always True (governance_crud.robot:53,106)

```robot
# LENIENT: Always passes (count can never be negative)
Should Be True    ${result}[count] >= 0

# STRICT: System should have known minimum data
Should Be True    ${result}[count] >= 30
...    msg=Expected at least 30 rules, got ${result}[count]
```

### 3. Key Existence Without Value Check (governance_crud.robot:27-28)

```robot
# LENIENT: Just checks key exists
Should Be True    'status' in $result

# STRICT: Check actual value
Should Be Equal    ${result}[status]    ok
...    msg=Expected status 'ok', got '${result}[status]'
```

### 4. Data Quality Gaps Found

| Issue | Evidence |
|-------|----------|
| Duplicate agents | TEST-AGENT-001 appears 3 times in /api/agents |
| Null decision_dates | All 4 decisions have `decision_date: null` |
| Orphaned test sessions | 30+ leftover ACTIVE test sessions in /api/sessions |
| Null fields | `semantic_id`, `created_date` often null in rules |

### 5. Missing Negative Tests

| Scenario | Expected | Not Tested |
|----------|----------|------------|
| POST /api/rules with invalid category | 422 with validation error | Not covered |
| POST /api/rules with duplicate ID | 409 Conflict | Not covered |
| PUT /api/rules with invalid priority | 422 | Not covered |
| DELETE /api/rules/nonexistent | 404 | Not covered |

## Remediation

1. Replace lenient assertions with value-specific checks per ARCH-EBMSF-01-v1
2. Add negative test cases for validation and conflict scenarios
3. Clean up orphaned test data in TypeDB (leftover sessions, duplicate agents)
4. Fix null fields in existing rules data (semantic_id, created_date)

---

*Per ARCH-EBMSF-01-v1: Test Evidence Structure*
