# GAP-EXPLOR-API-001: API Endpoint Gaps from Exploratory Testing

**Priority:** HIGH | **Category:** api | **Status:** RESOLVED
**Discovered:** 2026-01-18 | **Session:** Exploratory Testing with rest-api MCP

---

## Summary

Exploratory testing with rest-api MCP revealed several API endpoint issues affecting vertical navigation and CRUD operations.

## Evidence

### Issue 1: GET /api/tasks/{id} - 405 Method Not Allowed

**Request:**
```
GET http://localhost:8082/api/tasks/FH-006
```

**Response:**
```json
{
  "statusCode": 405,
  "body": {"detail": "Method Not Allowed"}
}
```

**Impact:** Cannot retrieve individual task details via REST API. Breaks vertical navigation.

---

### Issue 2: GET /api/rules/{id} - 404 Not Found

**Request:**
```
GET http://localhost:8082/api/rules/ARCH-MCP-01-v1
```

**Response:**
```json
{
  "statusCode": 404,
  "body": {"detail": "Rule ARCH-MCP-01-v1 not found"}
}
```

**Impact:** Rule exists in TypeDB (confirmed via /api/rules list) but individual retrieval fails. Routing or query issue.

---

### Issue 3: PUT /api/tasks/{id} - 500 Internal Server Error

**Request:**
```
PUT http://localhost:8082/api/tasks/EXPLOR-TEST-001
Body: {"status": "IN_PROGRESS"}
```

**Response:**
```json
{
  "statusCode": 500,
  "body": "Internal Server Error"
}
```

**Impact:** Cannot update task status via REST API. Critical for task lifecycle management.

---

### Issue 4: Sessions Endpoint Missing Pagination Metadata

**Request:**
```
GET http://localhost:8082/api/sessions?limit=3
```

**Response:** Returns raw array with 3 items, but no pagination metadata.

**Expected (per MCP-OUTPUT-01-v1):**
```json
{
  "items": [...],
  "pagination": {
    "total": 16,
    "offset": 0,
    "limit": 3,
    "has_more": true
  }
}
```

**Actual:** Raw array without pagination wrapper.

**Impact:** Inconsistent with /api/tasks which returns proper pagination. Violates MCP-OUTPUT-01-v1.

---

## Working Endpoints (Verified)

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| /api/health | GET | 200 | TypeDB status included |
| /api/tasks | GET | 200 | Pagination works |
| /api/tasks | POST | 201 | Creates task in TypeDB |
| /api/tasks/{id} | DELETE | 204 | Works correctly |
| /api/rules | GET | 200 | Category filter works |
| /api/sessions | GET | 200 | List works (no pagination) |
| /api/sessions/{id} | GET | 200 | Individual retrieval works |
| /api/decisions | GET | 200 | Returns 4 decisions |

## Action Items

1. [x] Implement GET /api/tasks/{id} route - Added to tasks/crud.py
2. [x] Fix GET /api/rules/{id} routing/query - Fixed to try direct lookup before legacy conversion
3. [x] Debug PUT /api/tasks/{id} 500 error - Fixed datetime serialization in fallback store
4. [x] Add pagination wrapper to sessions endpoint - Returns PaginatedSessionResponse

## Resolution

**Fixed:** 2026-01-18 | **Verified via rest-api MCP testing**

All four issues resolved:
- GET /api/tasks/{id}: Returns 200 with task details
- GET /api/rules/{id}: Returns 200 (rules stored with semantic IDs now looked up correctly)
- PUT /api/tasks/{id}: Returns 200 (datetime.isoformat() conversion fixed)
- GET /api/sessions: Returns proper pagination metadata (total, offset, limit, has_more)

## Related

- MCP-OUTPUT-01-v1: Tool Output Size Limits
- MCP-ERROR-01-v1: Error Response Format
- GAP-UI-PAGING-001: Pagination consistency

---

*Per GAP-DOC-01-v1: Evidence file format*
