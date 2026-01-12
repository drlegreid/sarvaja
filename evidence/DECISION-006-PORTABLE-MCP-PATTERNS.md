# DECISION-006: Portable MCP Configuration Patterns

**Date:** 2026-01-09
**Status:** APPROVED
**Category:** Technical/Operational
**Related Rules:** RULE-036 (MCP Split), RULE-002 (Technical Standards)

## Context

During xubuntu migration, discovered need for portable MCP configuration that works across environments without hardcoded paths.

## Problem Statement

1. Hardcoded paths like `/home/user/.venv/...` break portability
2. Different environments need different Python interpreters
3. PYTHONPATH must be set correctly for module imports
4. Line endings (CRLF vs LF) cause cross-platform issues

## Decision

**Use wrapper scripts + relative paths for MCP configuration**

### Pattern: MCP Runner Script

```bash
#!/bin/bash
# scripts/mcp-runner.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate venv if exists (portable)
if [ -f "$HOME/.venv/sim-ai/bin/activate" ]; then
    source "$HOME/.venv/sim-ai/bin/activate"
fi

export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
exec python -m "$1"
```

### Pattern: .mcp.json Configuration

```json
{
  "mcpServers": {
    "governance-core": {
      "type": "stdio",
      "command": "bash",
      "args": ["scripts/mcp-runner.sh", "governance.mcp_server_core"],
      "cwd": "${workspaceFolder}",
      "env": { ... }
    }
  }
}
```

## Holographic Principles Applied

| Principle | Application |
|-----------|-------------|
| **Granular** | Each MCP server has single responsibility |
| **Self-contained** | Wrapper script handles all env setup |
| **Portable** | No hardcoded paths, uses $HOME |
| **Discoverable** | Pattern documented in CLAUDE.md |

## Learnings Captured

1. **Always use relative paths** in config files
2. **Wrapper scripts** abstract environment details
3. **Fix line endings** with `sed -i 's/\r$//'`
4. **Test imports** before assuming config works
5. **${workspaceFolder}** for IDE portability

## Evidence

- Session: xubuntu migration 2026-01-09
- Files modified: `.mcp.json`, `scripts/mcp-runner.sh`
- Packages installed: `claude-agent-sdk`, `mcp-agent`, core deps

## Related Decisions

- DECISION-003: TypeDB-First Architecture
- DECISION-005: Memory Consolidation

---
*Per RULE-001: Session Evidence Logging*
