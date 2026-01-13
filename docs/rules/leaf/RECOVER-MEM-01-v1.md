# RECOVER-MEM-01-v1: Memory & MCP Stability

**Category:** `stability` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-005
> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `memory`, `stability`, `mcp`, `thresholds`

---

## Directive

Monitor memory thresholds and respect MCP stability tiers to maintain system health.

---

## Memory Thresholds

| Memory | Status | Action |
|--------|--------|--------|
| < 500 MB | HEALTHY | Normal operation |
| 500-1000 MB | NORMAL | Active development |
| 1000-1500 MB | WARNING | Monitor closely |
| 1500-2000 MB | HIGH | Consider closing files |
| > 2000 MB | CRITICAL | Restart soon |
| > 3000 MB | EMERGENCY | Restart immediately |

---

## MCP Stability Tiers

| Tier | MCPs | Risk |
|------|------|------|
| **STABLE** | claude-mem, sequential-thinking, filesystem, git | LOW |
| **PRODUCTIVE** | octocode, powershell, llm-sandbox | LOW |
| **MODERATE** | desktop-commander, playwright | MEDIUM |
| **CONDITIONAL** | godot-mcp | MEDIUM |

---

## Recovery Levels

1. **Soft**: Restart Claude Code
2. **Medium**: Disable heavy MCPs
3. **Hard**: Kill node processes
4. **Nuclear**: Full system restart

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Ignore memory warnings | Take action at WARNING threshold |
| Enable all MCPs simultaneously | Start with STABLE tier only |
| Wait until EMERGENCY to restart | Restart at CRITICAL threshold |
| Skip recovery levels | Follow escalation sequence |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
