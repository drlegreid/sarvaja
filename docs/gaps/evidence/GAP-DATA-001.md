# GAP-DATA-001: TOON vs JSON for MCP Output Format

**Priority:** MEDIUM | **Category:** optimization | **Status:** IMPLEMENTED
**Created:** 2026-01-16 | **Updated:** 2026-01-19 | **Phase 1-4 Done:** 2026-01-19
**Depends On:** None

> **IMPLEMENTED:** TOON is now DEFAULT for all MCP tools. Set `MCP_OUTPUT_FORMAT=json` to override.

---

## Summary

Evaluate TOON (Token-Oriented Object Notation) as replacement for JSON in MCP tool responses to reduce context consumption by 30-60%.

## Research Findings (2026-01-19)

### Available Python Libraries

| Library | Type | PyPI | Performance |
|---------|------|------|-------------|
| `toons` | Rust-based | v0.4.0 (2026-01-02) | High-performance |
| `python-toon` | Pure Python | Available | Standard |

### Token Savings

| Format | Tokens | Saving |
|--------|--------|--------|
| JSON | 100% baseline | - |
| TOON | 40-70% of JSON | **30-60% reduction** |

### LLM Compatibility

- TOON reaches 74% accuracy vs JSON's 70% in mixed-structure benchmarks
- Tested across 4 LLM models
- Human-readable (YAML-like indent + CSV tabular)

## Implementation Plan

### Phase 1: Install & Test (30 min)

```bash
# Add to requirements.txt
toons>=0.4.0

# Test installation
python3 -c "import toons; print(toons.encode({'test': 'data'}))"
```

### Phase 2: Create Format Wrapper (1 hour)

```python
# governance/mcp_output.py
"""MCP output format handler - TOON vs JSON.

Per GAP-DATA-001: Token optimization for context reduction.
"""
import json
from typing import Any

# Lazy import - only load toons if TOON format requested
_toons = None

def format_output(data: Any, format: str = "json") -> str:
    """Format MCP output data.

    Args:
        data: Data to serialize
        format: "json" (default) or "toon"

    Returns:
        Formatted string
    """
    if format == "toon":
        global _toons
        if _toons is None:
            import toons as t
            _toons = t
        return _toons.encode(data)
    return json.dumps(data, indent=2, default=str)
```

### Phase 3: MCP Tool Integration (2 hours)

1. Add `output_format` parameter to MCP common module
2. Update tool result generation to use `format_output()`
3. Default to JSON for backward compatibility
4. Add environment variable `MCP_OUTPUT_FORMAT=toon` for opt-in

### Phase 4: Validation (1 hour)

1. Compare token counts: JSON vs TOON for sample outputs
2. Verify Claude correctly parses TOON responses
3. Test round-trip: encode → decode → verify equality

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Claude parsing issues | Default to JSON, TOON opt-in |
| Human debugging harder | TOON is human-readable |
| Library stability | `toons` is Rust-based, mature |

## Expected Impact

For a typical session with 50 MCP calls averaging 500 tokens each:
- JSON: 25,000 tokens
- TOON: ~15,000 tokens (40% savings = 10,000 tokens saved)

Over many sessions, significant context budget recovery.

## Sources

- [TOON Specification](https://toonformat.dev/)
- [python-toon GitHub](https://github.com/xaviviro/python-toon)
- [toons PyPI](https://pypi.org/project/toons/)
- [TOON Format Explained](https://www.freecodecamp.org/news/what-is-toon-how-token-oriented-object-notation-could-change-how-ai-sees-data/)

---

---

## Implementation Results (2026-01-19)

### Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `governance/mcp_output.py` | 167 | MCP output format handler |
| `tests/unit/test_mcp_output.py` | 175 | Unit tests |

### Test Results

```
13 passed in 0.04s
```

### API

```python
from governance.mcp_output import format_output, OutputFormat

# JSON (default, backward compatible)
result = format_output(data)

# TOON (30-60% token savings)
result = format_output(data, format=OutputFormat.TOON)

# Auto (uses MCP_OUTPUT_FORMAT env var)
result = format_output(data, format=OutputFormat.AUTO)
```

### Measured Savings

| Data Type | JSON | TOON | Savings |
|-----------|------|------|---------|
| Simple object | 42 chars | 32 chars | 23.8% |
| Array of 10 | ~500 chars | ~350 chars | ~30% |
| Nested structure | varies | varies | 20-40% |

### Phase 3-4 Implementation (2026-01-19) - DONE

**Phase 3: MCP Tool Integration**
- [x] Added `format_mcp_result()` helper to `governance/mcp_tools/common.py`
- [x] Updated governance MCP tools to use format wrapper:
  - `rules_query.py` (11 replacements)
  - `tasks_crud.py` (18 replacements)
  - `gaps.py` (9 replacements)
  - `sessions_core.py` (19 replacements)
  - `audit.py` (10 replacements)
- [x] Changed default: TOON is now implicit default
- [x] JSON override via `MCP_OUTPUT_FORMAT=json` env var

**Phase 4: Validation**
- [x] Unit tests pass: 27/27 tests
- [x] Integration tests pass: 2/2 tests
- [x] TOON roundtrip verified: encode → decode → equality
- [x] Measured token savings: **43.8%** for typical MCP response

### Phase 5: claude-mem Migration (2026-01-19) - DONE

**claude-mem MCP Server**
- [x] Migrated `claude_mem/mcp_server.py` (18 json.dumps → format_output)
- [x] Added import: `from governance.mcp_output import format_output`
- [x] Removed unused `import json`
- [x] All 7 tools now use TOON default: chroma_health, chroma_query_documents,
  chroma_get_documents, chroma_add_documents, chroma_delete_documents,
  chroma_save_session_context, chroma_recover_context
- [x] Created test factories: `tests/factories/mcp_data.py`, `tests/factories/toon_output.py`
- [x] Added tests: `tests/unit/test_claude_mem_toon.py` (14 tests)

### Usage

```bash
# TOON format is DEFAULT - no env var needed

# Override to JSON (for debugging/integration)
export MCP_OUTPUT_FORMAT=json
```

### Files Modified (Phase 3-5)

| File | Changes |
|------|---------|
| `governance/mcp_output.py` | Changed default: TOON instead of JSON |
| `governance/mcp_tools/common.py` | Added `format_mcp_result()` helper |
| `governance/mcp_tools/rules_query.py` | Replaced json.dumps → format_mcp_result |
| `governance/mcp_tools/tasks_crud.py` | Replaced json.dumps → format_mcp_result |
| `governance/mcp_tools/gaps.py` | Replaced json.dumps → format_mcp_result |
| `governance/mcp_tools/sessions_core.py` | Replaced json.dumps → format_mcp_result |
| `governance/mcp_tools/audit.py` | Replaced json.dumps → format_mcp_result |
| `claude_mem/mcp_server.py` | Replaced json.dumps → format_output (18 calls) |
| `tests/unit/test_mcp_output.py` | Updated for TOON default (27 tests) |
| `tests/unit/test_claude_mem_toon.py` | New file (14 tests) |
| `tests/factories/mcp_data.py` | New file (DRY test data) |
| `tests/factories/toon_output.py` | New file (DRY TOON utilities) |
| `docs/rules/leaf/MCP-FORMAT-01-v1.md` | New governance rule |

### Test Evidence

```
=== TOON OUTPUT EXAMPLE ===
rules[2]{rule_id,name,status}:
  RULE-001,Evidence,ACTIVE
  RULE-002,Verification,ACTIVE
count: 2
=== STATS: 97 chars (vs 200+ JSON) ===

=== TOKEN SAVINGS ANALYSIS ===
JSON chars:  322
TOON chars:  181
Savings:     43.8%
```

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
