---
description: Context Statistics
allowed-tools: Bash, Read
---

# Context Statistics

Show actual context window usage (token counts, not estimates).

## Quick Stats

```bash
# Run context monitor status
python3 .claude/hooks/checkers/context_monitor.py --status
```

## Usage Levels

| Level | Usage | Action |
|-------|-------|--------|
| LOW | <50% | Continue working |
| MEDIUM | 50-75% | Monitor, consider checkpoints |
| HIGH | 75-90% | Save context soon |
| CRITICAL | >90% | STOP - Save/compact immediately |

## Metrics Tracked

- **total_input_tokens**: All input tokens in context
- **total_output_tokens**: All output tokens generated
- **context_window_size**: Max context window (usually 200k)
- **used_percentage**: Actual % of context used
- **tool_count**: Number of tool calls this session

## Context vs Entropy

| Metric | Source | Accuracy |
|--------|--------|----------|
| Context | Claude Code hook data | **Actual** token counts |
| Entropy | Tool call counting | Proxy estimate |

Use `/context-stats` for accurate metrics when making decisions.

## Related

- `/entropy` - Entropy-based proxy estimates
- `/health` - Infrastructure healthcheck
- `/compact` - Trigger context compaction

---
*Per CONTEXT-SAVE-01-v1: Monitor session entropy periodically*
