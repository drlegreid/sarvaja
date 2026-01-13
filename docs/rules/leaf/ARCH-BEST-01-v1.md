# ARCH-BEST-01-v1: Architectural & Design Best Practices

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-002
> **Location:** [RULES-ARCHITECTURE.md](../technical/RULES-ARCHITECTURE.md)
> **Tags:** `architecture`, `design`, `security`, `observability`

---

## Directive

All code and system design MUST follow:

1. **Separation of Concerns** - Single responsibility, clear layer boundaries
2. **Configuration Over Code** - Environment variables, YAML configs
3. **Observability by Default** - Health endpoints, structured logging
4. **Graceful Degradation** - Fallback models, retries, timeouts
5. **Idempotency** - Retriable operations, upsert patterns
6. **Documentation** - README per component, API contracts

---

## Validation

- [ ] No circular imports detected
- [ ] All secrets in `.env` (not in code)
- [ ] Health endpoint returns 200
- [ ] Session dump created

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Hardcode secrets in source | Use `.env` and environment variables |
| Create circular imports | Refactor to clear layer boundaries |
| Skip health endpoints | Add `/health` to every service |
| Ignore errors silently | Log and provide fallback behavior |
| Write non-idempotent operations | Use upsert patterns for retries |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
