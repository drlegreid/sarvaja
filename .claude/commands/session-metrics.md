# /session-metrics - Claude Code Session Analytics

Parse Claude Code JSONL session logs and display duration analytics. Per SESSION-METRICS-01-v1.

## Usage
```
/session-metrics
```

## What This Does

Calls the `session_metrics` MCP tool to parse Claude Code's local JSONL transcript files and returns:

- **Per-day breakdown**: Active time, session count, tool calls, MCP calls, compactions
- **Totals**: Aggregated active minutes, total sessions, tool usage
- **Tool breakdown**: Which tools were used and how often

## Instructions

When this command is invoked:

1. Call `mcp__gov-sessions__session_metrics(days=5)` to get the last 5 days of analytics
2. Present the results as a table with columns: Date, Active Time, Sessions, Tool Calls, MCP Calls, Compactions
3. Show totals row at the bottom
4. Format active time as `Xh Ym` (e.g. "2h 15m")

If the MCP tool is unavailable, fall back to running directly:

```python
from governance.session_metrics import discover_log_files, parse_log_file, calculate_metrics, filter_entries_by_days
from pathlib import Path
import os

cwd = os.getcwd()
slug = "-" + cwd.replace("/", "-").lstrip("-")
log_dir = Path.home() / ".claude" / "projects" / slug
files = discover_log_files(log_dir, include_agents=False)
entries = [e for f in files for e in parse_log_file(f)]
filtered = filter_entries_by_days(entries, days=5)
metrics = calculate_metrics(filtered, idle_threshold_min=30)
print(metrics.to_dict())
```

## Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `days` | 5 | Number of days to include |
| `idle_threshold_min` | 30 | Minutes of idle gap to split sessions |

## Related

- SESSION-METRICS-01-v1: Rule specification
- SESSION-EVID-01-v1: Session evidence logging
- /entropy: Context entropy monitoring
