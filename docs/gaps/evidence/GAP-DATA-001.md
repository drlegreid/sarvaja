# GAP-DATA-001: TOON vs JSON for MCP Output Format

**Priority:** MEDIUM | **Category:** optimization | **Status:** IN_PROGRESS
**Created:** 2026-01-16 | **Updated:** 2026-01-19
**Depends On:** None

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

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
