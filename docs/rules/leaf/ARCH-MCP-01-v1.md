# ARCH-MCP-01-v1: MCP Usage Protocol

**Category:** `productivity` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-007
> **Location:** [RULES-TOOLING.md](../technical/RULES-TOOLING.md)
> **Tags:** `mcp`, `productivity`, `tooling`, `automation`

---

## Directive

All sessions MUST actively leverage available MCPs according to task type.

---

## MCP Usage Matrix

| Task Type | Required MCPs | Optional MCPs |
|-----------|---------------|---------------|
| Session Start | claude-mem, filesystem | sequential-thinking |
| Code Research | octocode, filesystem | claude-mem |
| Implementation | filesystem, powershell | llm-sandbox, git |
| Testing | playwright, powershell | desktop-commander |
| Complex Analysis | sequential-thinking | claude-mem |

---

## Active MCPs

| MCP | Purpose |
|-----|---------|
| **claude-mem** | Memory persistence (ChromaDB) |
| **sequential-thinking** | Structured reasoning |
| **filesystem** | File operations |
| **git** | Version control |
| **powershell** | Windows automation |
| **llm-sandbox** | Code execution |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Manual GitHub search | Use octocode MCP |
| Copy-paste context | Query claude-mem |
| Ad-hoc decisions | Use sequential-thinking |

---

## Validation

- [ ] Session starts with claude-mem context query
- [ ] Research tasks use octocode
- [ ] Complex decisions use sequential-thinking

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
