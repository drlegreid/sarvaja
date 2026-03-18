# RELIABILITY-PLAN-01-v1: Reliability & Resilience Improvement Plan

| Field | Value |
|-------|-------|
| **Category** | ARCH |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **GitHub Issue** | [#30](https://github.com/drlegreid/platform-gai/issues/30) |
| **Created** | 2026-02-15 |

## Directive

The platform MUST implement retry-before-fallback for TypeDB access, persist agent status, and enable auto-remediation in CVP sweeps to reduce manual intervention and improve data consistency.

## Current Architecture (7 Layers)

1. **Prevention** — Input validation (Pydantic, route constraints)
2. **Detection** — 31 Heuristic Checks (H-*)
3. **CVP Pipeline** — 3-tier continuous validation
4. **Resilience** — TypeDB→in-memory fallback, timeout chains
5. **Audit Trail** — Correlation IDs, 7-day retention
6. **Hooks** — 18 pre/post hooks (entropy, MCP-first, destructive-action)
7. **Testing** — 10,075+ unit tests

## Prioritized Actions

1. **Retry decorator** for TypeDB access (max 2 attempts, backoff 0.5s/1s)
2. **Persist agent status** to TypeDB schema
3. **Auto-remediation** in CVP Tier 3 sweep
4. **Post-test cleanup hook** for TEST-* artifacts
5. **Specific exception types** across services (backlog)

## Success Criteria

- Zero `memory_only` sessions from transient TypeDB blips
- Agent status survives container restarts
- CVP sweep auto-fixes known patterns (completed_at, agent_id)
- TEST-* artifacts cleaned after test runs
