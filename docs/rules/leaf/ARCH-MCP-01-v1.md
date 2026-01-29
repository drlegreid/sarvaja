# ARCH-MCP-01-v1: MCP Usage Protocol

**Category:** `productivity` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-007
> **Location:** [RULES-TOOLING.md](../technical/RULES-TOOLING.md)
> **Tags:** `mcp`, `productivity`, `tooling`, `automation`

---

## Directive

All sessions MUST actively leverage available MCPs according to task type. New features touching API or UI MUST be verified with the corresponding MCP tool before marking RESOLVED.

---

## MCP Server Inventory (7 Servers)

| MCP Server | Purpose | Tier |
|------------|---------|------|
| **claude-mem** | Memory persistence (ChromaDB) | STABLE |
| **gov-core** | Rules, decisions, health checks | HIGH |
| **gov-agents** | Agents, trust scoring, proposals | HIGH |
| **gov-sessions** | Sessions, DSM, evidence collection | HIGH |
| **gov-tasks** | Tasks, workspace, gaps management | HIGH |
| **rest-api** | REST API endpoint testing (localhost:8082) | MEDIUM |
| **playwright** | E2E browser testing (Firefox) | MEDIUM |

---

## Task-Type MCP Matrix

| Task Type | Required MCPs | Verification MCPs |
|-----------|---------------|-------------------|
| Session Start | claude-mem | gov-tasks (backlog) |
| Governance Operations | gov-core, gov-sessions, gov-tasks | claude-mem |
| **New API Endpoint** | gov-sessions (if session-related) | **rest-api** (contract test) |
| **New UI View** | (implementation tools) | **playwright** (visual verify) |
| **New API + UI Feature** | (implementation tools) | **rest-api + playwright** |
| Testing / QA | playwright, rest-api | gov-sessions (evidence) |
| Complex Analysis | claude-mem | gov-core (rules context) |
| DSP / Deep Sleep | gov-sessions (DSM tools) | playwright (DREAM phase) |

**CRITICAL**: The "Verification MCPs" column is MANDATORY for the corresponding task type. Skipping verification MCPs means the feature is NOT verified per TEST-UI-VERIFY-01-v1.

---

## Verification Gate (NEW)

Before marking any gap/feature as RESOLVED, check this gate:

```
Feature includes new API endpoint?
├── YES → mcp__rest-api__test_request() called?
│         ├── YES → PASS
│         └── NO  → BLOCK: Run API verification first
└── NO  → Skip

Feature includes new UI view/component?
├── YES → mcp__playwright__browser_snapshot() called?
│         ├── YES → PASS
│         └── NO  → BLOCK: Run visual verification first
└── NO  → Skip
```

### Tool Bindings

| Verification Need | MCP Tool to Call |
|-------------------|-----------------|
| API endpoint works | `mcp__rest-api__test_request(method, path, body)` |
| UI renders correctly | `mcp__playwright__browser_navigate(url)` + `mcp__playwright__browser_snapshot()` |
| UI interaction works | `mcp__playwright__browser_click(element)` / `browser_fill_form()` |
| Screenshot evidence | `mcp__playwright__browser_take_screenshot()` |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Mark API feature resolved without calling rest-api MCP | Run `test_request()` on each new endpoint |
| Mark UI feature resolved without Playwright verification | Run `browser_snapshot()` or `browser_take_screenshot()` |
| Use only pytest for API — skip live endpoint test | pytest for unit tests, rest-api MCP for integration |
| Use only Robot Framework — skip live browser | Robot for deterministic tests, Playwright MCP for exploratory |
| Reference old MCPs (octocode, powershell, llm-sandbox) | Use current 7-server inventory above |
| Skip MCP verification because "tests pass" | Tests verify logic; MCPs verify integration |

---

## Validation

- [ ] Session starts with claude-mem context query
- [ ] New API endpoints verified via rest-api MCP
- [ ] New UI views verified via playwright MCP
- [ ] Governance operations use gov-* servers
- [ ] MCP inventory matches .mcp.json (7 servers)

---

## Evidence: GAP-SESSION-METRICS-UI (2026-01-29)

**Failure case**: Session metrics UI implemented with 20 pytest tests passing, all 7 phases complete, but:
- `rest-api` MCP never called on `/api/metrics/summary`, `/search`, `/timeline`
- `playwright` MCP never called on metrics dashboard view
- Feature committed without live API or browser verification

**Root cause**: Previous version of this rule had no verification gate and didn't list `rest-api` or `playwright` in the matrix.

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per TEST-UI-VERIFY-01-v1: Visual verification required*
