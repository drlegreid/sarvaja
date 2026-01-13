# ARCH-MCP-02-v1: MCP Server Separation Pattern

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-036
> **Location:** [RULES-ARCHITECTURE.md](../technical/RULES-ARCHITECTURE.md)
> **Tags:** `architecture`, `mcp`, `separation`, `domains`

---

## Directive

Large MCP servers (>50 tools) MUST be split into domain-specific servers.

---

## Server Domains

| Domain | Server | Tools |
|--------|--------|-------|
| Core | `governance-core` | Rules, decisions, health |
| Agents | `governance-agents` | Agents, trust, proposals |
| Sessions | `governance-sessions` | Sessions, DSM, evidence |
| Tasks | `governance-tasks` | Tasks, workspace, gaps |

---

## Requirements

1. Each server has own entry point (`mcp_server_{domain}.py`)
2. Tool modules split per RULE-032 (<300 lines)
3. Keep unified server for backward compatibility
4. Add all servers to `.mcp.json`

---

## Validation

- [ ] Each server imports <300 lines
- [ ] Each server starts independently
- [ ] Unified server still works
- [ ] Tests validate all servers

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Keep monolith MCP with >50 tools | Split into domain-specific servers |
| Create files >300 lines | Split per RULE-032 |
| Remove unified server immediately | Keep for backward compatibility |
| Skip server independence tests | Verify each server starts alone |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
