# MCP-OUTPUT-01-v1: Tool Output Size Limits

| Field | Value |
|-------|-------|
| **Rule ID** | MCP-OUTPUT-01-v1 |
| **Category** | OPERATIONAL |
| **Priority** | MEDIUM |
| **Status** | ACTIVE |
| **Created** | 2026-01-18 |

## Directive

MCP tools MUST limit output to reasonable sizes. Large results require pagination parameters.

## Output Limits

| Output Type | Max Size | Behavior |
|-------------|----------|----------|
| JSON array | 100 items | Truncate with `has_more: true` |
| Text content | 50KB | Truncate with `truncated: true` |
| Log output | 100 lines | Use tail by default |
| Query results | 50 items | Paginate with offset/limit |

## Pagination Parameters

Tools returning lists MUST support:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Maximum items to return |
| `offset` | int | 0 | Starting position |

## Truncation Response

When output is truncated, include metadata:

```json
{
  "items": [...],
  "pagination": {
    "total": 250,
    "offset": 0,
    "limit": 50,
    "has_more": true
  }
}
```

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Return unbounded results | Implement default limit |
| Fail silently on large output | Return truncated flag |
| Require caller to specify limit | Provide sensible defaults |

## Rationale

- Context window efficiency (avoid compaction)
- Predictable tool behavior
- Enable incremental data fetching

## Related

- GAP-MCP-PAGING-001 (Container logs 791K+ chars)
- GAP-MCP-DIRECTIVE-001 (Missing operational directives)

---

*Per GAP-MCP-DIRECTIVE-001: MCP operational directives*
