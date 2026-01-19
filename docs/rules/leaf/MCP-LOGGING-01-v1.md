# MCP-LOGGING-01-v1: MCP Server Structured Logging

**Status:** ACTIVE
**Priority:** HIGH
**Category:** observability
**Created:** 2026-01-19
**Semantic ID:** MCP-LOGGING-01-v1

## Directive

**ALL MCP servers MUST use structured logging with configurable levels and metrics collection.**

## Rationale

- **Debugging**: Track MCP protocol issues, tool call timing, failures
- **Metrics**: Startup times, tool call durations, error rates
- **Production**: Default ERROR level minimizes noise
- **Development**: DEBUG/TRACE levels for troubleshooting

## Log Levels

| Level | Value | Use Case |
|-------|-------|----------|
| TRACE | 5 | Protocol-level details, JSON-RPC messages |
| DEBUG | 10 | Tool invocations, timing, internal state |
| INFO | 20 | Server start/stop, tool registration |
| WARNING | 30 | Recoverable issues, deprecations |
| ERROR | 40 | Failures, exceptions (DEFAULT) |

## Configuration

```bash
# Set log level (default: ERROR)
export MCP_LOG_LEVEL=DEBUG

# Log file (default: logs/mcp.jsonl)
export MCP_LOG_FILE=logs/mcp.jsonl

# Metrics file (default: logs/mcp-metrics.jsonl)
export MCP_METRICS_FILE=logs/mcp-metrics.jsonl
```

## Implementation

```python
# In each mcp_server_*.py
from governance.mcp_logging import get_logger, log_server_start, MCPMetrics

logger = get_logger("gov-core")
metrics = MCPMetrics("gov-core")

# Log startup
log_server_start(logger, "gov-core", tool_count, version="1.25.0")
metrics.record_startup(tool_count, startup_ms)

# Log tool calls
with log_tool_call(logger, "health_check", args={}):
    result = do_health_check()
```

## Files

- [governance/mcp_logging.py](../../../governance/mcp_logging.py): Logging infrastructure
- [logs/mcp.jsonl](../../../logs/mcp.jsonl): Structured log output
- [logs/mcp-metrics.jsonl](../../../logs/mcp-metrics.jsonl): Metrics output

## Related

- [MCP-HEALTH-01-v1](MCP-HEALTH-01-v1.md): MCP server health validation
- [GAP-MCP-VALIDATE-001](../../gaps/evidence/GAP-MCP-VALIDATE-001.md): MCP validation gap
