# Tooling Rules

Rules governing MCP usage, version compatibility, and tooling protocols.

> **Parent:** [RULES-TECHNICAL.md](../RULES-TECHNICAL.md)
> **Tags:** `tooling`, `mcp`, `versions`, `configuration`

---

## Rules Summary

| Rule | Name | Priority | Status | Type | Leaf |
|------|------|----------|--------|------|------|
| **MCP-HEALTH-01-v1** | Autonomous MCP Health Management | CRITICAL | ACTIVE | TOOLING | [View](../leaf/MCP-HEALTH-01-v1.md) |
| **ARCH-MCP-01-v1** | MCP Usage Protocol | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/ARCH-MCP-01-v1.md) |
| **CONTAINER-DEV-01-v1** | DevOps Version Compatibility | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/CONTAINER-DEV-01-v1.md) |
| **ARCH-INFRA-02-v1** | Portable Configuration Patterns | HIGH | ACTIVE | TECHNICAL | [View](../leaf/ARCH-INFRA-02-v1.md) |

---

## Quick Reference

- **MCP-HEALTH-01-v1**: Agent MUST autonomously diagnose and fix MCP failures
- **ARCH-MCP-01-v1**: Sessions MUST actively leverage available MCPs
- **CONTAINER-DEV-01-v1**: Check container version BEFORE installing packages
- **ARCH-INFRA-02-v1**: Use portable patterns (relative paths, wrapper scripts)

---

## Tags

`tooling`, `mcp`, `versions`, `compatibility`, `configuration`, `portability`, `health`, `autonomous`

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
