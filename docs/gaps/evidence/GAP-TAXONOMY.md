# Gap & Rule Taxonomy

> **Gaps:** GAP-META-002, GAP-RULE-001, GAP-RULE-002
> **Rule:** RULE-013 (Rules Applicability Convention)
> **Status:** ALL RESOLVED 2026-01-04

---

## GAP-META-002: Category Taxonomy

**Categories for Gaps and Rules:**

| Category | Purpose | Examples | Prefix |
|----------|---------|----------|--------|
| governance | Rule/decision management | RULE-001, RULE-011 | GAP-RULE-*, GAP-DOC-* |
| architecture | System design | TypeDB, MCP, hybrid routing | GAP-ARCH-*, GAP-FILE-* |
| testing | Test infrastructure | pytest, E2E, TDD | GAP-TEST-*, GAP-TDD-*, GAP-HEUR-* |
| ui | Dashboard, views | Trame, Vuetify | GAP-UI-* |
| workflow | Process automation | DSP, session, evidence | GAP-WORKFLOW-*, GAP-DSP-* |
| infrastructure | Docker, deployment | containers, health | GAP-INFRA-* |
| security | Auth, validation | API keys, middleware | GAP-SEC-* |
| data | Entities, integrity | TypeDB entities, sync | GAP-DATA-*, GAP-SYNC-* |
| observability | Monitoring, health, logs | healthcheck, metrics | GAP-HEALTH-*, GAP-LOG-* |
| functionality | Features, operations | CRUD, APIs | GAP-STUB-*, GAP-AGENT-* |
| meta | Self-referential | Gap tracking itself | GAP-META-* |

**Usage:** All gaps MUST use lowercase category values from this table.

---

## GAP-RULE-001: Applicability Types

| TYPE | Description | Example |
|------|-------------|---------|
| FORBIDDEN | Must never do | Commit secrets, skip tests |
| REQUIRED | Must always do | Session logging, health checks |
| CONDITIONAL | Context-dependent | Use TypeDB when available |
| RECOMMENDED | Best practice | Modularize >300 line files |
| DEPRECATED | Phase out | Strikethrough in gaps |

---

## GAP-RULE-002: Anti-Patterns Format

All rules should include anti-patterns using this table format:

```markdown
### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip health check | Always call health_check first |
| Hardcode secrets | Use .env and environment variables |
```

---

## Files Updated (36 rules)

- `governance/RULES-SESSION.md`: RULE-001, 003, 006, 018, 026, 029
- `governance/RULES-MULTI-AGENT.md`: RULE-011, 013, 019
- `technical/RULES-ARCHITECTURE.md`: RULE-002, 016, 036
- `technical/RULES-TOOLING.md`: RULE-007, 009
- `technical/RULES-STRATEGY.md`: RULE-008, 010, 017, 025
- `operational/RULES-TESTING.md`: RULE-004, 020, 023, 028
- `operational/RULES-STABILITY.md`: RULE-005, 021, 022
- `operational/RULES-WORKFLOW.md`: RULE-012, 014, 015, 024, 031
- `operational/RULES-STANDARDS.md`: RULE-027, 030, 032, 033, 034, 035

---

*Per RULE-013: Rules Applicability Convention*
