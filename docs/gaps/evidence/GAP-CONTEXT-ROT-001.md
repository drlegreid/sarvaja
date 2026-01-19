# GAP-CONTEXT-ROT-001: Context Rot Prevention

**Created:** 2026-01-19
**Status:** RESOLVED
**Priority:** HIGH
**Category:** OPERATIONAL

## Problem Statement

Context rot occurs when MCP tool responses return large arrays (e.g., 85 tasks),
consuming excessive context tokens and accelerating session entropy toward compaction.

### Root Causes Identified (2026-01-19)

1. **No array truncation** - MCP tools returned full arrays regardless of size
2. **Warning intervals too sparse** - CRITICAL warnings only every 25 tool calls
3. **No pre-prompt entropy check** - Warnings came AFTER tool execution, not before
4. **Silent CRITICAL level** - Could be at 149 calls with no warning until 165

## Resolution

### Fix 1: Array Truncation in MCP Output (governance/mcp_output.py)

Added `_truncate_arrays()` function that:
- Truncates arrays to 30 items by default (configurable via MCP_MAX_ARRAY_ITEMS)
- Adds metadata markers: `_tasks_truncated: true`, `_tasks_total: 85`, `_tasks_shown: 30`
- Applies to common array keys: rules, tasks, agents, sessions, gaps, etc.

```python
# Before: 85 tasks = ~4000 tokens
{"tasks": [...85 items...], "count": 85}

# After: 30 tasks + metadata = ~1500 tokens
{"tasks": [...30 items...], "_tasks_truncated": true, "_tasks_total": 85, "_tasks_shown": 30, "count": 85}
```

### Fix 2: Aggressive CRITICAL Warnings (.claude/hooks/entropy_cli.py)

- Reduced CRITICAL interval from 25 to 10 tool calls
- Added immediate warning when first crossing into CRITICAL (150+)
- Reduced HIGH interval from 20 to 15 calls
- Added emojis for visibility

### Fix 3: Pre-Prompt Entropy Check (.claude/hooks/prompt_healthcheck.py)

Added `check_entropy()` function to UserPromptSubmit hook:
- Warnings now appear BEFORE processing the prompt
- Shows `[ENTROPY CRITICAL] 150 tool calls - SAVE NOW!` at prompt time
- User sees warning before any tools execute

## Evidence

### Before Fix
- Session with 139 tool calls reached HIGH/CRITICAL with no recent warnings
- `last_warning_at: 120`, next warning wouldn't fire until 140
- By the time warning showed, context was already burned

### After Fix
- Warnings fire every 10 calls at CRITICAL level
- Pre-prompt check shows entropy status before processing
- Array truncation reduces token consumption by ~60% for large responses

## Related Rules

- RECOVER-CRASH-01-v1: Crash prevention via file size limits
- RECOVER-AMNES-01-v1: Context recovery protocol
- CONTEXT-SAVE-01-v1: Context efficiency monitoring

## Files Modified

- `governance/mcp_output.py` - Added _truncate_arrays(), DEFAULT_MAX_ARRAY_ITEMS
- `.claude/hooks/entropy_cli.py` - Reduced warning intervals, first-CRITICAL trigger
- `.claude/hooks/prompt_healthcheck.py` - Added check_entropy() pre-prompt check
