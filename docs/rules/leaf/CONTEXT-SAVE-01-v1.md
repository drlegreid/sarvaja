# CONTEXT-SAVE-01-v1: Context Efficiency Protocol

**Category:** `stability` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Origin:** GAP-CONTEXT-EFFICIENCY-001
> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `context`, `entropy`, `save`, `efficiency`, `recovery`

---

## Directive

Monitor session entropy periodically and save context before compaction risk. Context efficiency prevents loss of work and reduces recovery overhead.

---

## Entropy Thresholds

| Level | Tool Calls | Action |
|-------|------------|--------|
| LOW | <50 | Continue working |
| MEDIUM | 50-100 | Consider saving context |
| HIGH | 100-150 | Save context now |
| CRITICAL | >150 | STOP - Save to ChromaDB immediately |

---

## Monitor Commands

```bash
# Check current entropy level
/entropy

# Manual check via Python
python3 .claude/hooks/entropy_monitor.py --status
```

---

## Context Save Commands

When entropy reaches HIGH or CRITICAL:

```python
# Save session context to ChromaDB
chroma_save_session_context(
    session_id="SESSION-YYYY-MM-DD-TOPIC",
    summary="What was accomplished",
    key_decisions=["decision1", "decision2"],
    files_modified=["file1.py", "file2.py"],
    gaps_discovered=["GAP-XXX-001"]
)
```

---

## When to Check Entropy

1. **Periodically** - Every 20-30 tool calls
2. **Before complex tasks** - Know your budget before starting
3. **When output feels slow** - May indicate approaching context limit
4. **After troubleshooting** - Recovery attempts burn context fast
5. **At natural breakpoints** - Before starting new feature/phase

---

## Context Burn Patterns

Common patterns that burn context quickly:

| Pattern | Context Cost | Prevention |
|---------|-------------|------------|
| Troubleshooting MCP | HIGH | SessionStart validation |
| Reading large files | MEDIUM | Use Grep/offset/limit |
| Multiple tool retries | HIGH | Fix root cause first |
| Verbose health reports | MEDIUM | Use compact format |
| Searching without Task | MEDIUM | Use Explore agent |

---

## Implementation

### Pre-flight Validation (TACTIC-1)
```bash
# Validates MCP servers before session burns context on errors
scripts/check_mcp_duplicates.sh
```

### Pre-commit Guard (TACTIC-2)
```bash
# Prevents duplicate tools from causing MCP startup failures
ln -sf ../../scripts/check_mcp_duplicates.sh .git/hooks/pre-commit
```

### Auto-warning (TACTIC-3)
- EntropyChecker monitors tool count
- Warnings at MEDIUM (50), HIGH (100), CRITICAL (150)
- Time-based reminder at 60 minutes

---

## Related Rules

- RECOVER-AMNES-01-v1: Context recovery protocol
- RECOVER-CRASH-01-v1: Crash investigation protocol
- MCP-HEALTH-01-v1: MCP server health checks

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
