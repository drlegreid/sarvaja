# ARCH-EBMSF-01-v1: EBMSF Architecture Standards

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Location:** [RULES-ARCHITECTURE.md](../technical/RULES-ARCHITECTURE.md)
> **Tags:** `architecture`, `security`, `code-review`, `ebmsf`

---

## Directive

All architecture MUST follow EBMSF (Evidence-Based Multi-Session Framework) standards:

1. **Code Reviews Required** - All changes require peer review before merge
2. **No Hardcoded Secrets** - Credentials MUST be in `.env` or secret management
3. **Evidence-Based Decisions** - Architecture changes require documented rationale
4. **Session Continuity** - Design for multi-session agent collaboration

---

## Validation

- [ ] Code review completed before merge
- [ ] No secrets in committed code
- [ ] Architectural Decision Record (ADR) created for changes
- [ ] Session evidence logged

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip code reviews | Require approval before merge |
| Commit secrets to git | Use `.env` and `.gitignore` |
| Make undocumented changes | Create ADRs for decisions |
| Design for single session | Consider multi-agent collaboration |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
