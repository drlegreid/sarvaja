# SAFETY-HEALTH-02-v1: MCP Health Verification

**Category:** `stability` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `safety`, `health`, `mcp`, `recovery`

---

## Directive

Every MCP operation MUST verify server health; failures logged and recovery attempted before failing.

1. **Pre-Operation Check** - Verify MCP server responding before operation
2. **Failure Logging** - Log all failures with context
3. **Recovery Attempt** - Try automatic recovery before hard failure
4. **Graceful Degradation** - Provide fallback when possible

---

## Recovery Protocol

```
1. Detect failure
2. Log error with context
3. Attempt auto-recovery (restart, reconnect)
4. Wait with backoff (1s, 2s, 4s)
5. If recovery fails, notify and degrade gracefully
```

---

## Validation

- [ ] Health check before critical operations
- [ ] Failures logged with timestamp and context
- [ ] Recovery attempted before failing
- [ ] Graceful fallback available

---

*Per SAFETY-HEALTH-01-v1: MCP Healthcheck Protocol*
