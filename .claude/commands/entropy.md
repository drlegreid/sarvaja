---
description: /entropy - Check Session Entropy
allowed-tools: Bash, Read, mcp__claude-mem__chroma_save_session_context
---

# /entropy - Check Session Entropy

Check current session entropy and context usage. Per GAP-CONTEXT-EFFICIENCY-001.

## Usage
```
/entropy
```

## What This Does

Shows current session metrics:
- **Tool call count**: Number of tool invocations this session
- **Session duration**: How long the session has been active
- **Entropy level**: LOW/MEDIUM/HIGH/CRITICAL
- **Action required**: What to do based on entropy level

## Entropy Levels & Thresholds

| Level | Tool Calls | Action |
|-------|------------|--------|
| LOW | <50 | Continue working |
| MEDIUM | 50-100 | Consider saving context soon |
| HIGH | 100-150 | Save context now, plan session wrap-up |
| CRITICAL | >150 | STOP - Save to ChromaDB before compaction |

## When to Use

1. **Periodically** - Check every 20-30 tool calls
2. **Before complex tasks** - Know your budget before starting
3. **When output feels slow** - May indicate approaching context limit
4. **After troubleshooting** - Recovery attempts burn context fast

## Context Save Commands

When entropy is HIGH/CRITICAL, save context:

```python
# Via MCP
chroma_save_session_context(
    session_id="SESSION-YYYY-MM-DD-TOPIC",
    summary="What was accomplished",
    key_decisions=["key decision 1"],
    files_modified=["file1.py"],
    gaps_discovered=["GAP-XXX"]
)
```

## Manual Check

Run directly: `python3 .claude/hooks/entropy_monitor.py --status`

## Related

- RECOVER-AMNES-01-v1: Context recovery protocol
- RECOVER-CRASH-01-v1: Crash prevention via file size limits
- GAP-CONTEXT-EFFICIENCY-001: Context efficiency improvement epic
