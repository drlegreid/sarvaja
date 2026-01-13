# REPORT-DEC-02-v1: Exploratory Test Automation

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-004
> **Location:** [RULES-TESTING.md](../operational/RULES-TESTING.md)
> **Tags:** `testing`, `exploratory`, `automation`, `heuristics`

---

## Directive

All components MUST be testable via domain-specific heuristics. Exploratory testing complements TDD cycle.

---

## Workflow Principles

| Principle | Directive | Gate |
|-----------|-----------|------|
| **Gaps Before Implementation** | Document all gaps BEFORE coding | No PR without GAP-* |
| **Page Object Model (POM)** | All UI tests use OOP page objects | Code review check |
| **Test What You Ship** | RULE-023 compliance | CI/CD gate |
| **Insight Capture** | Document insights during execution | Task description updated |

---

## Domain Heuristics Summary

| Domain | Key Heuristics | Priority |
|--------|---------------|----------|
| **UI** | BOUNDARY, NAVIGATION, STATE, ERROR | HIGH |
| **API** | CONTRACT, IDEMPOTENCY, AUTH, PAYLOAD | HIGH |
| **Shell** | EXIT_CODE, STDERR, PATH_SAFETY | HIGH |
| **Docker** | HEALTHCHECK, RESTART, VOLUME, NETWORK | CRITICAL |
| **Security** | INJECTION, SECRETS, AUDIT_TRAIL | CRITICAL |

---

## Validation

- [ ] 3+ heuristics per domain tested
- [ ] Evidence captured for all test runs
- [ ] Healthcheck suite < 30 seconds

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
