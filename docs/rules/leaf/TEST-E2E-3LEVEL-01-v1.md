---
rule_id: TEST-E2E-3LEVEL-01-v1
name: Three-Level E2E Edge Coverage
status: ACTIVE
category: quality
priority: HIGH
applicability: MANDATORY
---

## Rule

Every feature that touches the service layer MUST have Robot Framework E2E tests at **three levels**, written TDD-first (before implementation):

| Level | What | Tool |
|-------|------|------|
| **L1 — REST API** | Create/mutate via REST endpoints, verify via REST audit/query | `mcp__rest-api__test_request` |
| **L2 — MCP** | Create/mutate via MCP tool functions, verify via MCP query tools | Robot `mcp_*.py` libraries |
| **L3 — Playwright** | Full UI journey — interact with dashboard, verify state changes | `mcp__playwright__*` |

## Rationale

**Origin (2026-03-28):** SRVJ-FEAT-AUDIT-TRAIL-01 P2 — initial Robot specs only tested REST API (L1). MCP tools and Playwright UI were not covered. This missed the fact that MCP runs in-process with a separate audit store from the container, and that the TypeDB unlink query was broken (only visible at L1+L2 cross-verification).

Single-level E2E gives false confidence. L1 alone misses MCP-specific bugs. L2 alone misses REST routing bugs. L3 alone misses data-layer bugs. All three together prove the feature works from edge to edge.

## Architecture Note

L1 and L2 use **separate test tasks** because:
- L1 (REST API) → hits the container → audit entries in container's in-memory store
- L2 (MCP library) → runs in-process → audit entries in Robot process's in-memory store

They are NOT cross-verified against each other. Each level is self-consistent: create and query via the same path.

## Do / Don't

| Don't | Do Instead |
|-------|------------|
| Write only REST API tests | Add MCP-level tests using `mcp_*.py` Robot libraries |
| Write only happy-path tests | Include edge cases: idempotency, error paths, field-level diffs |
| Have 1 journey test as "L3" | Write multiple L3 scenarios covering distinct user journeys |
| Use `curl` or raw `pytest` for validation | Use MCP tools: rest-api (T2), log-analyzer (T1), playwright (T3) |

## File Conventions

- Robot suites: `tests/e2e/robot/suites/{feature}.robot`
- MCP libraries: `tests/e2e/robot/libraries/mcp_{domain}.py`
- Test naming: `L{level} {Description}` (e.g., `L1 Link Rule Produces LINK Audit Entry`)
