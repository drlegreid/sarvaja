# GAP-MCP-DIRECTIVE-001: Missing MCP Operational Directives

**Priority:** MEDIUM | **Category:** governance | **Status:** RESOLVED
**Discovered:** 2026-01-17 | **Session:** Quality Assessment

---

## Summary

MCP tools lack operational directives for output size, error handling, and documentation standards. This leads to:
- Context overflow when tools return large outputs (GAP-MCP-PAGING-001)
- Inconsistent error responses across tools
- Undocumented tool behavior requiring trial-and-error

## Evidence

### Existing MCP Rules

| Rule | Coverage | Gap |
|------|----------|-----|
| ARCH-MCP-01-v1 | Tool structure | None |
| ARCH-MCP-02-v1 | Server separation | None |
| MCP-NAMING-01-v1 | Naming convention | None |
| MCP-RESTART-AUTO-01-v1 | Auto-restart | None |

### Missing Directives

1. **MCP-OUTPUT-01**: Tool output size limits
   - Problem: Some tools return 791K+ characters (GAP-MCP-PAGING-001)
   - Need: Max output size, truncation pattern, pagination

2. **MCP-ERROR-01**: Error response format
   - Problem: Inconsistent error structures
   - Need: Standard error JSON schema

3. **MCP-DOC-01**: Tool documentation standard
   - Problem: Docstrings vary in quality
   - Need: Required sections, examples format

## Impact

- **Quality:** Error debugging harder without consistent responses
- **Performance:** Large outputs cause context compaction
- **Onboarding:** New users struggle with undocumented edge cases

## Proposed Rules

### MCP-OUTPUT-01-v1: Tool Output Size Limits

```markdown
## Directive
MCP tools MUST limit output to 50KB. Larger results require pagination parameters.

## Parameters
- `limit`: Max items (default: 50)
- `offset`: Starting position (default: 0)
```

### MCP-ERROR-01-v1: Error Response Format

```markdown
## Directive
MCP tool errors MUST return structured JSON with code, message, and context.

## Schema
{
  "error": true,
  "code": "TYPEDB_CONNECTION_FAILED",
  "message": "Human readable message",
  "context": { "host": "localhost", "port": 1729 }
}
```

### MCP-DOC-01-v1: Tool Documentation Standard

```markdown
## Directive
MCP tools MUST include: summary, args, returns, example, related rules.
```

## Action Items

1. [x] Create MCP-OUTPUT-01-v1 rule - DONE 2026-01-18
2. [x] Create MCP-ERROR-01-v1 rule - DONE 2026-01-18
3. [x] Create MCP-DOC-01-v1 rule - DONE 2026-01-18
4. [ ] Implement output truncation (GAP-MCP-PAGING-001) - Separate gap

## Resolution (2026-01-18)

Created 3 new MCP operational rules:
- [MCP-OUTPUT-01-v1](../../rules/leaf/MCP-OUTPUT-01-v1.md): Output size limits (50KB, pagination)
- [MCP-ERROR-01-v1](../../rules/leaf/MCP-ERROR-01-v1.md): Error response format (structured JSON)
- [MCP-DOC-01-v1](../../rules/leaf/MCP-DOC-01-v1.md): Tool documentation standard (L3 required)

## Related

- GAP-MCP-NAMING-001: Naming inconsistency
- GAP-MCP-PAGING-001: Output truncation
- ARCH-MCP-02-v1: Server separation

---

*Per GAP-DOC-01-v1: Evidence file format*
