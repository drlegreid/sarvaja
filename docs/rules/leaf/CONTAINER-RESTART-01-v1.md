# CONTAINER-RESTART-01-v1: API Server Restart Protocol

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-027
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `api`, `testing`, `restart`, `protocol`

---

## Directive

ALWAYS restart API servers after making code changes BEFORE running tests.

---

## Protocol

1. STOP existing server process
2. START fresh server instance
3. VERIFY server is responsive (/api/health)
4. RUN tests

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Run tests immediately after changes | Restart server first |
| Assume hot-reload caught changes | Explicitly restart |
| Debug "404" without checking server | Check if server has latest code |

---

## Validation

- [ ] Server restarted after code changes
- [ ] Health endpoint verified
- [ ] Tests run on fresh instance

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
