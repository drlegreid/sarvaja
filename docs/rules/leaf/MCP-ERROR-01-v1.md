# MCP-ERROR-01-v1: Error Response Format

| Field | Value |
|-------|-------|
| **Rule ID** | MCP-ERROR-01-v1 |
| **Category** | OPERATIONAL |
| **Priority** | MEDIUM |
| **Status** | ACTIVE |
| **Created** | 2026-01-18 |

## Directive

MCP tool errors MUST return structured JSON with code, message, and context.

## Error Schema

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human readable description",
  "context": {
    "additional": "debugging info"
  }
}
```

## Standard Error Codes

| Code | HTTP Equiv | Description |
|------|------------|-------------|
| `TYPEDB_CONNECTION_FAILED` | 503 | TypeDB unreachable |
| `CHROMADB_CONNECTION_FAILED` | 503 | ChromaDB unreachable |
| `ENTITY_NOT_FOUND` | 404 | Requested item doesn't exist |
| `VALIDATION_ERROR` | 400 | Invalid input parameters |
| `PERMISSION_DENIED` | 403 | Trust score too low |
| `INTERNAL_ERROR` | 500 | Unexpected failure |

## Context Fields

Include relevant debugging information:

| Error Type | Context Fields |
|------------|----------------|
| Connection | `host`, `port`, `timeout_ms` |
| Not found | `entity_type`, `entity_id` |
| Validation | `field`, `expected`, `received` |
| Permission | `required_trust`, `actual_trust` |

## Example

```python
# Good error response
return json.dumps({
    "error": True,
    "code": "ENTITY_NOT_FOUND",
    "message": "Task P10.99 not found in TypeDB",
    "context": {
        "entity_type": "task",
        "entity_id": "P10.99",
        "suggestion": "Use tasks_list to see available tasks"
    }
})
```

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Return plain error strings | Use structured JSON |
| Expose stack traces | Summarize error safely |
| Use inconsistent codes | Follow standard codes |

## Rationale

- Consistent error handling across tools
- Actionable error messages
- Easier debugging and automation

## Related

- GAP-MCP-DIRECTIVE-001 (Missing operational directives)
- SAFETY-HEALTH-01-v1 (Health check recovery)

---

*Per GAP-MCP-DIRECTIVE-001: MCP operational directives*
