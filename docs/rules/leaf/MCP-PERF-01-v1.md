# MCP-PERF-01-v1: MCP Server Direct Invocation Over Package Runners

| Field | Value |
|-------|-------|
| **Category** | TECHNICAL |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-20 |

## Directive

Node MCP servers MUST use direct node invocation via `scripts/mcp-node-runner.sh`, NOT `npx`.
Python MCP servers MUST use `scripts/mcp-runner.sh` or direct venv invocation, NOT bare `uvx` without pinned versions.

## Performance Data

| Method | Startup Time | Notes |
|--------|-------------|-------|
| `npx -y package` (cold) | 30s+ (TIMEOUT) | Downloads from registry |
| `npx -y package` (cached) | 3s+ | Still resolves package |
| `npx -y package@latest` | 3-30s+ | Forces registry check every time |
| `node path/to/index.js` | **~300ms** | Direct invocation, no overhead |

## Architecture

```
.mcp.json → bash scripts/mcp-node-runner.sh <package> [args...]
                    ↓
              node_modules/<package>/  (installed via npm install)
                    ↓
              node <entry-point.js>   (~300ms startup)
```

Dependencies pinned in `package.json` (exact versions, no ranges).
Installed via `npm install` into project-local `node_modules/`.

## Runner Scripts

| Script | For | Pattern |
|--------|-----|---------|
| `scripts/mcp-node-runner.sh` | Node MCP servers | Resolves bin from package.json, exec node |
| `scripts/mcp-runner.sh` | Python MCP servers | Resolves venv, exec python3 -m module |

## Incident

2026-03-20: Both `rest-api` and `playwright` MCP servers timed out on initial connection (30s limit) due to `npx` overhead. Fix: switched to direct node invocation, startup dropped from 30s+ to 300ms.

## Related Rules

- DEP-PIN-01-v1: Pin dependency versions (no @latest)
- WORKFLOW-SHELL-01-v1: Use python3, not python
