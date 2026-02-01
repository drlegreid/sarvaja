# Exploratory (Dynamic) Testing Rules

> **Domain**: TEST | **Status**: ACTIVE | **Created**: 2026-02-01
> **Sources**: dev.to/johnonline35 (Verdex), Medium/rahulbhardwaj (AI-Healing), MCP Market
> **Companion**: [PATTERNS-EXPLORATORY-TESTING.md](PATTERNS-EXPLORATORY-TESTING.md) — detailed patterns & workflows

---

## Index

| Rule ID | Domain | Name | Automated | Via |
|---------|--------|------|-----------|-----|
| H-TASK-001 | TASK | Task descriptions required | Yes | REST MCP |
| H-TASK-002 | TASK | IN_PROGRESS agent assignment | Yes | REST MCP |
| H-TASK-003 | TASK | DONE completion timestamps | Yes | REST MCP |
| H-TASK-004 | TASK | No TEST-* artifacts | Yes | REST MCP |
| H-SESSION-001 | SESSION | Active session agent_id | Yes | REST MCP |
| H-SESSION-002 | SESSION | Ended sessions have evidence | Yes | REST MCP |
| H-SESSION-003 | SESSION | Stale active sessions (>24h) | Yes | REST MCP |
| H-SESSION-004 | SESSION | No TEST-* artifacts | Yes | REST MCP |
| H-RULE-001 | RULE | ACTIVE rules need document_path | Yes | REST MCP |
| H-RULE-003 | RULE | Rule directive content | Yes | REST MCP |
| H-RULE-004 | RULE | No TEST-* artifacts | Yes | REST MCP |
| H-AGENT-001 | AGENT | Agent trust scores | Yes | REST MCP |
| H-AGENT-002 | AGENT | Agent last_active recency | Yes | REST MCP |
| H-CROSS-001 | CROSS-ENTITY | Service layer coverage | Yes | REST MCP |
| H-CROSS-002 | CROSS-ENTITY | API response consistency | Yes | REST MCP |
| H-API-001 | API | Endpoint health (all return 2xx) | Yes | REST MCP |
| H-API-002 | API | Pagination contract compliance | Yes | REST MCP |
| H-API-003 | API | Error response structure | Yes | REST MCP |
| H-UI-001 | UI | Selector stability (no .nth) | Auto | Playwright MCP |
| H-UI-002 | UI | Container-scoped selectors | Auto | Playwright MCP |
| H-UI-003 | UI | data-testid coverage | Yes | File scan |
| H-UI-004 | UI | Progressive disclosure workflow | Manual | Playwright MCP |
| H-UI-005 | UI | AI self-healing cycle | Manual | Playwright MCP |
| H-MCP-001 | MCP | All servers have metadata | Yes | REST MCP |
| H-MCP-002 | MCP | Backend dependency health | Yes | REST MCP |

---

## 1. Data Integrity Checks (via `mcp__rest-api__test_request`)

**Execution**: All entity-domain checks use `mcp__rest-api__test_request` (base: localhost:8082).
Server-side `POST /api/tests/heuristic/run` is available but suffers self-referential timeouts.

### TASK Domain

**H-TASK-001**: Non-CLOSED tasks must have description >10 chars.
- Why: Undescribed tasks are unactionable and create governance debt.

**H-TASK-002**: IN_PROGRESS tasks must have agent_id.
- Why: Unassigned in-progress work is unaccountable.

**H-TASK-003**: DONE tasks must have completed_at timestamp.
- Why: Completion without evidence timestamp breaks audit trail.

**H-TASK-004**: No TEST-* tasks should persist outside test runs.
- Why: Test artifacts pollute production data.

### SESSION Domain

**H-SESSION-001**: Active sessions must have agent_id.
- Why: Orphaned sessions can't be attributed to any agent.

**H-SESSION-002**: Ended sessions should have evidence files.
- Why: Sessions without evidence provide no audit value.

**H-SESSION-003**: Sessions ACTIVE >24h are likely stale.
- Why: Unclosed sessions indicate crashes or lost context.

**H-SESSION-004**: No TEST-* sessions outside test runs.

### RULE Domain

**H-RULE-001**: ACTIVE rules should have document_path.
- Why: Rules without backing documents are unverifiable.

**H-RULE-003**: Rule directives must be non-empty (>10 chars).
- Why: Empty directives are unenforceable.

**H-RULE-004**: No TEST-* rules outside test runs.

### AGENT Domain

**H-AGENT-001**: All registered agents must have trust_score > 0.
- Why: Zero-trust agents can't participate in governance.

**H-AGENT-002**: Agent last_active should be within 30 days.
- Why: Stale agents may have outdated configurations.

### CROSS-ENTITY Domain

**H-CROSS-001**: All 4 service layers must report SERVICE_LAYER via `/api/mcp/readiness`.
- Why: Direct TypeDB access bypasses audit/monitoring.

**H-CROSS-002**: All API list endpoints must return consistent pagination structure.
- Why: Inconsistent APIs break UI data binding.

---

## 2. API Testing Patterns (via REST MCP)

### H-API-001: Endpoint Health
All registered API endpoints should return 2xx on GET with default params.
**MCP call**: `mcp__rest-api__test_request(method="GET", endpoint="/api/tasks")` for each endpoint.
Endpoints: `/api/tasks`, `/api/sessions`, `/api/rules`, `/api/agents`, `/api/health`, `/api/mcp/readiness`

### H-API-002: Pagination Contract
All paginated endpoints must return `{items: [], pagination: {total, offset, limit, has_more, returned}}`.
**MCP call**: `mcp__rest-api__test_request(method="GET", endpoint="/api/tasks?limit=1")` — verify structure.

### H-API-003: Error Response Structure
4xx/5xx responses should return `{detail: string}` (FastAPI convention).
**MCP call**: `mcp__rest-api__test_request(method="POST", endpoint="/api/tasks", body={})` — verify error shape.

---

## 3. UI Testing Patterns (via Playwright MCP)

> Detailed patterns, code examples, and workflows in [PATTERNS-EXPLORATORY-TESTING.md](PATTERNS-EXPLORATORY-TESTING.md)

### H-UI-001: Selector Stability
**Anti-pattern**: `.nth(N)` positional selectors break on DOM changes.
**Required**: Container-scoped, role-first selectors.
**Check**: `browser_snapshot` → scan for `.nth(` without `getByTestId` scope.

### H-UI-002: Container-Scoped Selectors (Container → Content → Role)
```
GOOD: getByTestId("task-row").filter({hasText: "TASK-001"}).getByRole("button")
BAD:  getByRole("button", {name: "Edit"})  // ambiguous in repeating context
```

### H-UI-003: data-testid Coverage
All interactive components must have `data-testid` attributes.
**Check**: Scan Trame view files for `VBtn`, `VCard`, `VDialog` without `data-testid`/`data_testid`.

### H-UI-004: Progressive Disclosure Workflow
When generating selectors via Playwright MCP, follow 4-level disclosure:
1. `browser_snapshot` → semantic overview (~2k tokens)
2. Container discovery → find stable `data-testid` boundaries
3. Pattern recognition → identify repeating structures (cards, rows)
4. Anchor extraction → find unique text/role differentiators
**Budget**: ~5k tokens total vs 50k+ for full DOM dump.

### H-UI-005: AI Self-Healing Cycle (Planner → Generator → Healer)
When a test selector fails:
1. Re-snapshot page via `browser_snapshot`
2. Find closest semantic match to original intent
3. If confidence >80%, update selector automatically
4. If <80%, flag as needing human review
5. Record healing event as session evidence via `session_test_result`

---

## 4. MCP Integration Testing

### H-MCP-001: Server Metadata Completeness
All servers in MCP_SERVERS must have entries in MCP_SERVER_META with: tools, depends_on, desc.
**MCP call**: `mcp__rest-api__test_request(method="GET", endpoint="/api/mcp/readiness")`

### H-MCP-002: Backend Dependency Health
MCP servers with `depends_on` must have all dependencies healthy.
A gov-tasks server with `depends_on: [typedb]` should show `ready: READY` only when TypeDB is reachable.

---

## Sources

- [Why AI Can't Write Good Playwright Tests](https://dev.to/johnonline35/why-ai-cant-write-good-playwright-tests-and-how-to-fix-it-knn) — Verdex progressive disclosure, Container→Content→Role pattern
- [Rethinking UI Test Automation: AI-Healing with Playwright MCP](https://medium.com/@rahulbhardwaj8851046/rethinking-ui-test-automation-the-rise-of-ai-healing-with-playwright-mcp-bd420882930f) — Planner/Generator/Healer, 5-step healing cycle
- [MCP Market: API Testing Patterns](https://mcpmarket.com/tools/skills/api-testing-patterns-2) — API contract testing
- Local copies: `docs/rules/Why AI Can't Write Good Playwright Tests*.html`, `docs/rules/🤖 Rethinking UI Test Automation*.html`
