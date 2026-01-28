---
description: Initiate Deep Sleep Protocol (DSP) cycle for document entropy reduction
allowed-tools: mcp__gov-sessions__dsm_start, mcp__gov-sessions__dsm_advance, mcp__gov-sessions__dsm_checkpoint, mcp__gov-sessions__dsm_finding, mcp__gov-sessions__dsm_complete, mcp__gov-core__governance_analyze_rules, mcp__gov-tasks__backlog_get, mcp__claude-mem__chroma_save_session_context, Read, Write, Edit, Bash, TodoWrite
---

# Deep Sleep Protocol (RULE-012, SESSION-DSM-01-v1)

Initiate a DSP cycle when document entropy is high. Per SESSION-DSP-NOTIFY-01-v1.

## DSP Phases

| Phase | Purpose | MCP Tool |
|-------|---------|----------|
| 1. AUDIT | Scan for issues | `dsm_start()`, `governance_analyze_rules()` |
| 2. HYPOTHESIZE | Formulate fixes | `dsm_checkpoint()` |
| 3. MEASURE | Quantify problems | `dsm_finding()` |
| 4. OPTIMIZE | Apply fixes | Edit files, deprecate rules |
| 5. VALIDATE | Verify improvements | `governance_analyze_rules()` |
| 6. DREAM | Capture learnings | `chroma_save_session_context()` |
| 7. REPORT | Generate evidence | `dsm_complete()` |

## Quick Start

```python
# 1. Start DSP cycle
dsm_start(batch_id="DSP-CLEANUP")

# 2. Run audit
governance_analyze_rules()
backlog_get(limit=20)

# 3. Address findings with dsm_finding() for each issue
dsm_finding(finding_type="gap", description="...", severity="MEDIUM")

# 4. Advance through phases
dsm_advance()  # Call after completing each phase

# 5. Complete and generate evidence
dsm_complete()
```

## Entropy Triggers (Per healthcheck_formatters.py)

DSP is suggested when 2+ conditions are met:
- Evidence files > 20 (accumulation)
- Days since last DSP > 7
- Files > 300 lines detected
- Gap count high

## Common DSP Tasks

1. **Archive old evidence files** - Move SESSION-*.md to archive/
2. **Refactor large files** - Split files > 300 lines per DOC-SIZE-01-v1
3. **Deprecate obsolete rules** - Use `rule_deprecate()`
4. **Clean up gaps** - Mark RESOLVED or DEFERRED
5. **Update documentation** - Ensure indexes match reality

## Output

DSP generates evidence at: `evidence/DSP-{date}-{batch_id}.md`

## Related Rules

- RULE-012: Deep Sleep Protocol phases
- SESSION-DSP-NOTIFY-01-v1: DSP prompting and blocking
- DOC-SIZE-01-v1: File size limits (300 lines max)
- DOC-GAP-ARCHIVE-01-v1: Gap archival process
