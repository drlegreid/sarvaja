# DEP-PIN-01-v1: Pin All External Dependency Versions

| Field | Value |
|-------|-------|
| **Category** | OPERATIONAL |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-20 |

## Directive

All external dependencies MUST use pinned exact versions. NEVER use `@latest`, `^`, `~`, or unpinned specifiers.

## Scope

Applies to all dependency managers in the project:

| Manager | Correct | Wrong |
|---------|---------|-------|
| npm `package.json` | `"0.4.0"` | `"^0.4.0"`, `"~0.4.0"`, `"*"` |
| pip `requirements.txt` | `package==1.2.3` | `package>=1.2.3`, `package` |
| uvx `.mcp.json` args | `"package==0.1.8"` | `"package"` |
| npx (FORBIDDEN) | N/A — use direct node | `npx -y pkg@latest` |

## Rationale

Floating versions cause non-deterministic startup failures:
- npm registry checks add 3-30s+ latency
- MCP connection timeout is 30s — cold `npx` downloads exceed this
- `@latest` forces registry lookup on every invocation, even when cached
- Silent breaking changes from auto-upgrades

## Incident

2026-03-20: `rest-api` and `playwright` MCP servers failed to start due to `npx -y` cold download exceeding 30s timeout. `@latest` tag on playwright forced registry checks on every reconnect.

## Compliance

- `package.json`: No `^`, `~`, `*`, or `x` in version strings
- `requirements.txt`: All entries must have `==X.Y.Z`
- `.mcp.json`: No `@latest` tags; uvx args must include `==X.Y.Z`
