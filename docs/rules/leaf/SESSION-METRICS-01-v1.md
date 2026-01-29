# SESSION-METRICS-01-v1: Claude Code Session Log Analytics

**Category:** `analytics` | **Priority:** HIGH | **Status:** TO_IMPLEMENT | **Type:** TECHNICAL

> **Location:** [RULES-TECHNICAL.md](../technical/RULES-TECHNICAL.md)
> **Tags:** `session`, `analytics`, `metrics`, `logs`, `duration`
> **Related:** SESSION-EVID-01-v1, SESSION-HOOK-01-v1, RECOVER-CRASH-01-v1

---

## Directive

The platform SHALL provide an MCP tool and CLI command to parse Claude Code session JSONL transcripts, extracting session duration, tool call metadata, thinking process records, and per-day analytics. All metrics MUST be derived from the authoritative source: Claude Code's local JSONL log files.

---

## Problem Statement

Session duration and activity metrics are essential for governance reporting, context budget planning, and operational visibility. Currently no tool exists to parse Claude Code's native `.jsonl` transcript files. Ad-hoc Python scripts are used instead, creating a repeatable gap.

---

## Data Source

### Location
```
~/.claude/projects/{project-path-slug}/*.jsonl
```

Example: `~/.claude/projects/-home-oderid-Documents-Vibe-sarvaja-platform/349e6ab5-527b-4c8c-8d8c-1c6322353d84.jsonl`

Agent subprocesses: `agent-*.jsonl` in the same directory.

### JSONL Entry Schema (Observed)

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Entry type: `user`, `assistant`, `system`, `progress`, `file-history-snapshot`, `queue-operation` |
| `timestamp` | ISO 8601 | Entry timestamp (UTC) |
| `sessionId` | UUID | Session identifier |
| `uuid` | UUID | Message identifier |
| `parentUuid` | UUID | Parent message (threading) |
| `message.role` | string | `user` or `assistant` |
| `message.content` | array | Content blocks (text, tool_use, tool_result, thinking) |
| `message.model` | string | Model used (assistant entries only) |
| `mcpMeta` | object | MCP server metadata (present on MCP tool results) |
| `isSidechain` | bool | Whether entry is from a sidechain/subagent |
| `toolUseID` | string | Tool invocation identifier |
| `parentToolUseID` | string | Parent tool use (for nested calls) |
| `compactMetadata` | object | Compaction event metadata (trigger, preTokens) |
| `version` | string | Claude Code version |
| `gitBranch` | string | Active git branch |
| `cwd` | string | Working directory |

### Content Block Types

| Block Type | Fields | Notes |
|------------|--------|-------|
| `thinking` | `thinking` (string) | Model's reasoning chain. **Privacy-sensitive.** |
| `text` | `text` (string) | Model's visible response |
| `tool_use` | `id`, `name`, `input` | Tool invocation with parameters |
| `tool_result` | `tool_use_id`, `content` | Tool execution result |

---

## Metrics to Extract

### Required Metrics

| Metric | Algorithm | Unit |
|--------|-----------|------|
| **Active Duration** | Sum of inter-message gaps < idle threshold (default: 30 min) | minutes |
| **Wall-Clock Duration** | Last timestamp - first timestamp per session | minutes |
| **Session Count** | Distinct activity bursts separated by idle threshold | count |
| **Message Count** | Count of `user` + `assistant` type entries | count |
| **Tool Call Count** | Count of `tool_use` content blocks | count |
| **Tool Call Breakdown** | Group tool_use by `name`, count per tool | dict |
| **MCP Call Count** | Count of tool_use where name starts with `mcp__` | count |
| **Compaction Count** | Count of `system` entries with `subtype=compact_boundary` | count |
| **Model Used** | Extract from `message.model` on assistant entries | string |
| **Thinking Token Estimate** | Sum of `len(thinking_text)` across thinking blocks | chars |

### Optional Metrics (Future)

| Metric | Description |
|--------|-------------|
| Error Rate | Count of entries with `isApiErrorMessage=true` |
| Agent Subprocess Time | Parse `agent-*.jsonl` files for subagent durations |
| Context Burn Rate | Tokens per tool call from compactMetadata |

---

## Interface Specification

### MCP Tool: `session_metrics`

```python
def session_metrics(
    days: int = 5,
    project_path: str = None,     # Auto-detect from cwd if None
    idle_threshold_min: int = 30,  # Gap to split sessions
    include_thinking: bool = False # Privacy: exclude thinking by default
) -> dict:
    """
    Parse Claude Code JSONL logs and return session analytics.

    Returns:
        {
            "days": [...],           # Per-day breakdown
            "totals": {...},         # Aggregated totals
            "sessions": [...],       # Individual session details
            "tool_breakdown": {...}, # Tool usage counts
            "metadata": {...}        # Log file info
        }
    """
```

### Output Schema

```json
{
  "days": [
    {
      "date": "2026-01-29",
      "active_minutes": 122,
      "wall_clock_minutes": 180,
      "session_count": 3,
      "message_count": 45,
      "tool_calls": 89,
      "mcp_calls": 12,
      "compactions": 2
    }
  ],
  "totals": {
    "active_minutes": 1000,
    "session_count": 20,
    "message_count": 350,
    "tool_calls": 800,
    "days_covered": 5
  },
  "tool_breakdown": {
    "Read": 120,
    "Bash": 95,
    "Edit": 45,
    "mcp__gov-core__rules_query": 30
  },
  "metadata": {
    "log_file": "349e6ab5-...jsonl",
    "total_entries": 78222,
    "first_entry": "2026-01-15T10:09:16Z",
    "last_entry": "2026-01-29T22:30:00Z",
    "idle_threshold_min": 30
  }
}
```

---

## Privacy & Safety Constraints

1. **Thinking blocks**: Default `include_thinking=False`. When excluded, report only character count, never content.
2. **Tool inputs**: Truncate to 200 chars max in any output. Never include file contents or secrets.
3. **User messages**: Report count only, never content.
4. **Local only**: Never transmit log data externally. All processing is local.
5. **Read-only**: Parser MUST NOT modify or delete log files.

---

## Implementation Plan

| Phase | Component | Description |
|-------|-----------|-------------|
| 1 | `governance/session_metrics/parser.py` | JSONL log parser core |
| 2 | `governance/session_metrics/calculator.py` | Duration & metrics calculation |
| 3 | `governance/mcp_tools/session_metrics.py` | MCP tool registration |
| 4 | `.claude/commands/session-metrics.md` | CLI slash command |
| 5 | Integration tests | Robot Framework + pytest |

### File Structure
```
governance/session_metrics/
├── __init__.py
├── parser.py          # JSONL file discovery & parsing
├── calculator.py      # Metrics computation
└── models.py          # Data models (dataclasses)
```

---

## Validation Criteria

- [ ] Parser handles 78K+ line JSONL files without OOM (streaming)
- [ ] Active duration matches manual calculation within 1 minute tolerance
- [ ] Idle threshold correctly splits sessions (30 min default)
- [ ] MCP tool returns valid JSON matching output schema
- [ ] Thinking content excluded by default
- [ ] Tool inputs truncated in output
- [ ] Agent subprocess files (`agent-*.jsonl`) handled
- [ ] Graceful handling of missing/empty log directory
- [ ] Performance: < 5 seconds for 100K entries

---

## Test Coverage

Tests SHALL be written BEFORE implementation (TDD).

| Test File | Scope | Tests |
|-----------|-------|-------|
| `tests/unit/test_session_metrics_parser.py` | Unit | JSONL parsing, entry classification |
| `tests/unit/test_session_metrics_calculator.py` | Unit | Duration calc, session splitting, tool counting |
| `tests/robot/unit/session_metrics.robot` | Integration | MCP tool invocation, output schema validation |

---

*Per GAP identified 2026-01-29 | SESSION-2026-01-29-SESSION-METRICS*
