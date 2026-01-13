# Stability Rules - Sim.ai

Rules governing memory management, MCP health, and system integrity.

> **Parent:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Tags:** `stability`, `memory`, `health`, `recovery`

---

## Rules Summary

| Rule | Name | Priority | Status | Type | Leaf |
|------|------|----------|--------|------|------|
| **RECOVER-MEM-01-v1** | Memory & MCP Stability | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/RECOVER-MEM-01-v1.md) |
| **SAFETY-HEALTH-01-v1** | MCP Healthcheck Protocol | CRITICAL | ACTIVE | TECHNICAL | [View](../leaf/SAFETY-HEALTH-01-v1.md) |
| **SAFETY-INTEG-01-v1** | Integrity Verification (Frankel Hash) | HIGH | DRAFT | TECHNICAL | [View](../leaf/SAFETY-INTEG-01-v1.md) |
| **RECOVER-CRASH-01-v1** | Crash Investigation Protocol | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/RECOVER-CRASH-01-v1.md) |

---

## Quick Reference

- **RECOVER-MEM-01-v1**: Memory thresholds: <500MB=HEALTHY, >2000MB=CRITICAL, >3000MB=EMERGENCY
- **SAFETY-HEALTH-01-v1**: Every MCP operation MUST verify health; auto-recovery on failure
- **SAFETY-INTEG-01-v1**: Critical files MUST have integrity verification via hashing
- **RECOVER-CRASH-01-v1**: On crash, IMMEDIATELY investigate logs before resuming

---

## Tags

`stability`, `memory`, `health`, `mcp`, `recovery`, `integrity`, `crash`, `investigation`

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
