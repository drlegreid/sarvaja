# HTTP-ERROR-01-v1: HTTP Exception Handling Protocol

| Field | Value |
|-------|-------|
| **Rule ID** | HTTP-ERROR-01-v1 |
| **Category** | TECHNICAL |
| **Priority** | CRITICAL |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-24 |

## Directive

All route files MUST re-raise `HTTPException` before generic `except Exception` catch-all blocks. Generic catch-alls that swallow HTTPException convert client errors (400/404/422) into misleading 500 responses.

---

## Required Pattern

```python
# CORRECT: HTTPException re-raised before generic catch-all
try:
    result = service.get_entity(entity_id)
    return result
except HTTPException:
    raise  # Preserve 400, 404, 422 etc.
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## HTTP Status Code Contract

| Status | Meaning | When |
|--------|---------|------|
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Entity does not exist |
| 422 | Validation Error | Schema/field validation failure |
| 500 | Internal Error | Unexpected system failure (generic message only) |

**CRITICAL**: 500 responses MUST NOT expose internal details (stack traces, file paths, query text). Use a generic message and log the details server-side.

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| `except Exception` without `except HTTPException: raise` above it | Always re-raise HTTPException first |
| `raise HTTPException(500, detail=str(e))` | Use generic message: `"Internal server error"` |
| Catch-all that returns 200 on error | Let HTTPException propagate with correct status |
| `except (HTTPException, Exception)` in one block | Separate blocks: HTTPException first, Exception second |

---

## Enforcement

**Grep audit**: No `except Exception` in `governance/routes/` without a preceding `except HTTPException: raise` in the same try block.

```bash
# Spot-check command
grep -rn "except Exception" governance/routes/ | grep -v "except HTTPException"
```

---

## Root Cause (P12 Incident, 2026-03-22)

`governance/routes/sessions/crud.py` had `except Exception` catch-all that swallowed `HTTPException(404)` from `get_session()`. Client received 500 instead of 404, making session navigation silently fail.

---

## Related

- MCP-ERROR-01-v1 (MCP error response format)
- SAFETY-HEALTH-01-v1 (Health check recovery)
- TEST-E2E-01-v1 (Data flow verification catches these at Tier 2)

---

*Per EPIC-TASK-QUALITY-V3 P12: Session Navigation Fix*
