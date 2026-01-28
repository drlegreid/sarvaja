# GAP-ENTROPY-HOOK-001: PostToolUse Hook Missing for Entropy Tracking

| Field | Value |
|-------|-------|
| **ID** | GAP-ENTROPY-HOOK-001 |
| **Priority** | HIGH |
| **Status** | RESOLVED |
| **Created** | 2026-01-19 |
| **Resolved** | 2026-01-19 |
| **Category** | Infrastructure |

## Problem Statement

Entropy monitoring system was designed but not wired up to Claude Code hooks. The `EntropyChecker.increment_and_check()` method was never invoked because:

1. No `PostToolUse` hook was configured in `.claude/settings.local.json`
2. The entropy checker used relative imports that fail when called as CLI script

**Evidence:**
```json
{
  "tool_count": 121,
  "check_count": 2  // Only 2 checks despite 121 tool calls!
}
```

## Root Cause

The hooks configuration only included:
- `SessionStart` → healthcheck.py
- `UserPromptSubmit` → prompt_healthcheck.py
- `PreToolUse(Bash)` → pre_bash_check.py

Missing: `PostToolUse` hook to track tool call entropy.

## Resolution

1. Created standalone CLI wrapper: `.claude/hooks/entropy_cli.py`
   - No relative imports (self-contained)
   - Supports `--increment`, `--status`, `--reset` flags
   - Exit codes: 0=OK, 1=warning, 2=error

2. Added `PostToolUse` hook to settings:
```json
"PostToolUse": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/entropy_cli.py\" --increment -q",
        "timeout": 1
      }
    ]
  }
]
```

## Files Modified

- `.claude/hooks/entropy_cli.py` - Created (standalone CLI)
- `.claude/hooks/checkers/entropy.py` - Added CLI entry point (unused, kept for imports)
- `.claude/settings.local.json` - Added PostToolUse hook

## Verification

```bash
# Test CLI
python3 .claude/hooks/entropy_cli.py --status
python3 .claude/hooks/entropy_cli.py --increment
python3 .claude/hooks/entropy_cli.py --reset

# Hook will auto-trigger on next session
```

## Task Boundary Limitation (2026-01-20 Investigation)

**User Request:** Investigate why entropy hook doesn't warn at task boundaries.

**Findings:**

| Question | Answer |
|----------|--------|
| PostToolUse receives tool name? | **No** - Claude Code API doesn't expose `CLAUDE_TOOL_NAME` |
| Filter PostToolUse by TodoWrite? | **No** - `matcher` only works for PreToolUse |
| Current behavior | Counts ALL tool calls, warns at 50/100/150 thresholds |

**Conclusion:** This is a **Claude Code API limitation**, not a code bug. There's no way to detect specifically when TodoWrite marks a task complete without reading state files after every tool call.

**Workaround Options:**
1. Check todo state periodically (expensive - runs every tool call)
2. Request Claude Code feature: expose `CLAUDE_TOOL_NAME` for PostToolUse
3. Accept current behavior (threshold-based warnings)

**Status:** Original issue RESOLVED. Task boundary feature is UNFEASIBLE with current API.

---

## Related

- CONTEXT-SAVE-01-v1 (Context efficiency rule)
- RECOVER-AMNES-01-v1 (AMNESIA recovery)
- GAP-CONTEXT-EFFICIENCY-001 (Context monitoring)
