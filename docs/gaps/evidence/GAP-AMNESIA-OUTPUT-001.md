# GAP-AMNESIA-OUTPUT-001: AMNESIA Detection Output Suppressed

**Created:** 2026-01-15
**Priority:** HIGH
**Category:** observability
**Status:** RESOLVED

## Problem Statement

The AMNESIA detector works correctly but its output is suppressed in normal operation:

1. After first check, healthcheck switches to `format_summary()` mode
2. `format_summary()` does NOT include AMNESIA warnings
3. Only `format_detailed()` shows AMNESIA risk indicators
4. Result: User never sees AMNESIA warnings even when detected

## Root Cause

In [healthcheck.py:498-509](../../.claude/hooks/healthcheck.py#L498-L509):

```python
if hash_changed or check_count == 1:
    context = format_detailed(...)  # Shows AMNESIA
elif retry_ceiling_reached:
    context = format_summary(...)   # NO AMNESIA output
else:
    context = format_summary(...)   # NO AMNESIA output
```

## Fix Required

Modify `format_summary()` to include AMNESIA warnings when detected.

### Files to Modify

1. **`.claude/hooks/healthcheck_formatters.py`**
   - Add `amnesia` parameter to `format_summary()`
   - Append AMNESIA warning to summary output when detected

2. **`.claude/hooks/healthcheck.py`**
   - Pass `amnesia` dict to `format_summary()` calls

## Implementation

```python
# healthcheck_formatters.py - format_summary()
def format_summary(
    services: Dict,
    master_hash: str,
    reason: str = "",
    recovery_actions: List[str] = None,
    zombies: Dict = None,
    amnesia: Dict = None,  # NEW
    core_services: List[str] = None
) -> str:
    # ... existing code ...

    # Add AMNESIA warning if detected
    if amnesia and amnesia.get("detected"):
        base += f" | AMNESIA RISK: {int(amnesia['confidence']*100)}%"

    return base
```

## Acceptance Criteria

- [x] `format_summary()` accepts amnesia parameter
- [x] AMNESIA warnings appear in summary mode when detected
- [x] Unit tests pass (13 tests in `tests/test_health_modes.py`)
- [x] E2E test verifies AMNESIA shown in stable state

## Verification Evidence (2026-01-15)

```bash
$ PYTHONPATH=.claude python -c "from hooks.healthcheck_formatters import format_summary; ..."

Without AMNESIA: [HEALTH OK] Hash: TEST123 (stable). MCP chain ready.
With AMNESIA: [HEALTH OK] Hash: TEST123 (stable). MCP chain ready. | AMNESIA RISK 65%
```

**Files Modified:**
- `.claude/hooks/healthcheck_formatters.py` - Added amnesia parameter to format_summary()
- `.claude/hooks/healthcheck.py` - Pass amnesia dict to format_summary() calls

## Related

- RECOVER-AMNES-01-v1: AMNESIA Recovery Protocol
- GAP-HEALTH-AGGRESSIVE-001: Aggressive health mode (complementary)
