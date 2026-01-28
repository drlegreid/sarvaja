# DOC-LINK-01-v1: Relative Document Linking

**Category:** `documentation` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-034
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `documentation`, `links`, `relative`, `markdown`

---

## Directive

ALL document references MUST use relative markdown links: `[text](relative/path)`

---

## Link Formats

| Type | Format | Example |
|------|--------|---------|
| Evidence | `[ID](evidence/FILE.md)` | `[SESSION-2026](evidence/SESSION-2026.md)` |
| Gaps | `[GAP-X](docs/gaps/GAP-INDEX.md#gap-x)` | `[GAP-003](docs/gaps/GAP-INDEX.md#gap-003)` |
| Rules | `[RULE-X](docs/rules/FILE.md#rule-x)` | `[RULE-034](#rule-034)` |
| Source | `[file:line](path#Lline)` | `[api.py:42](governance/api.py#L42)` |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| `sim-ai-session` (plain text) | `[sim-ai-session](evidence/...)` |
| `See GAP-INDEX.md` | `See [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)` |

---

## Validation

- [ ] All references use relative links
- [ ] Links are clickable
- [ ] No broken links

## Test Coverage

**2 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/document_service.robot` | unit |
| `tests/robot/unit/workspace_scanner_split.robot` | unit |

```bash
# Run all tests validating this rule
robot --include DOC-LINK-01-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
