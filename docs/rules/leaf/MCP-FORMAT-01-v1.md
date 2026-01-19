# MCP-FORMAT-01-v1: TOON Default Format for MCP Tools

| Field | Value |
|-------|-------|
| **Rule ID** | MCP-FORMAT-01-v1 |
| **Category** | OPERATIONAL |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Created** | 2026-01-19 |

## Directive

All MCP tools MUST use TOON format by default for output. JSON format is available via explicit override.

## Default Format

| Configuration | Format | Use Case |
|---------------|--------|----------|
| Default (no env) | TOON | Normal operation, 30-60% token savings |
| `MCP_OUTPUT_FORMAT=toon` | TOON | Explicit TOON (redundant but clear) |
| `MCP_OUTPUT_FORMAT=json` | JSON | Debugging, external tool integration |

## Implementation Pattern

```python
from governance.mcp_output import format_output

# Default: TOON format (implicit)
result = format_output(data)

# Explicit JSON (for debugging/integration)
from governance.mcp_output import OutputFormat
result = format_output(data, format=OutputFormat.JSON)
```

## Token Savings

| Data Type | JSON | TOON | Savings |
|-----------|------|------|---------|
| Simple object | 100% | ~75% | ~25% |
| Array of 10 | 100% | ~60% | ~40% |
| Nested structure | 100% | ~55% | ~45% |

## TOON Format Characteristics

TOON (Token-Oriented Object Notation) differs from JSON:

| Aspect | JSON | TOON |
|--------|------|------|
| Object delimiter | `{...}` | Field names with `:` |
| Array notation | `[...]` | `[count]{fields}:` |
| String quotes | Always quoted | Unquoted when safe |
| Whitespace | `indent` parameter | Optimized for tokens |

## Environment Variable

```bash
# Default (TOON)
# No env var needed

# Override to JSON
export MCP_OUTPUT_FORMAT=json
```

## Test Requirements

All MCP tools MUST have tests validating:
1. Default output is TOON format
2. JSON output works when `MCP_OUTPUT_FORMAT=json`
3. Data roundtrip: encode → decode preserves equality

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Use `json.dumps()` directly | Use `format_output()` |
| Assume JSON format | Check environment for format |
| Skip format tests | Test both TOON and JSON paths |

## Migration Checklist

For new MCP tools:
- [ ] Import `from governance.mcp_output import format_output`
- [ ] Replace `json.dumps(data)` with `format_output(data)`
- [ ] Add unit test for TOON default
- [ ] Add unit test for JSON override
- [ ] Verify roundtrip preservation

## Related

- GAP-DATA-001 (TOON implementation)
- MCP-OUTPUT-01-v1 (Output size limits)
- RULE-007 (MCP Usage Protocol)

---

*Per GAP-DATA-001: TOON format for context efficiency*
