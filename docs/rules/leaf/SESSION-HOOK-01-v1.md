# SESSION-HOOK-01-v1: Session Tool Call Auto-Logging

**Category:** `logging` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** TECHNICAL

> **Location:** [RULES-TECHNICAL.md](../technical/RULES-TECHNICAL.md)
> **Tags:** `session`, `logging`, `hooks`, `audit`

---

## Directive

PostToolUse hooks SHALL automatically log tool calls to the active governance session for audit trail and debugging purposes.

---

## Implementation

| Component | Purpose |
|-----------|---------|
| `hooks_utils/session_tool_logger.py` | Core logging logic |
| `.claude/hooks/session_tool_logger.py` | Hook entry point |
| `governance/session_collector/registry.py` | State file persistence |
| `.claude/hooks/.session_state.json` | Active session state |

---

## Architecture

```
PostToolUse Event
    ↓
session_tool_logger.py (hook)
    ↓
Read CLAUDE_TOOL_NAME + CLAUDE_TOOL_INPUT
    ↓
Load .session_state.json
    ↓
If active session exists:
    → SessionCollector.capture_tool_call()
    → Write to TypeDB
    ↓
Silent fail if unavailable
```

---

## Requirements

1. **Performance**: Hook execution < 500ms
2. **Resilience**: Silent fail if TypeDB/session unavailable
3. **Skip List**: Don't log recursive calls (session_tool_call, session_thought)
4. **State Sync**: Registry persists state on session start/end

---

## Validation

- [ ] 11 unit tests pass (`tests/unit/test_session_tool_logger.py`)
- [ ] Hook registered in settings.local.json
- [ ] State file created on session start
- [ ] Tool calls appear in session evidence

## Test Coverage

**2 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/file_watcher.robot` | unit |
| `tests/robot/unit/session_tool_logger.robot` | unit |

```bash
# Run all tests validating this rule
robot --include SESSION-HOOK-01-v1 tests/robot/
```

---

*Per GAP-SESSION-THOUGHT-001 | SESSION-2026-01-21-AUTONOMOUS-QUALITY*
