# GAP-DOC-01-v1: Gap Documentation Structure

**Category:** `documentation` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Ref:** GAP-META-001
> **Tags:** `gaps`, `documentation`, `evidence`, `tickets`

---

## Directive

ALL gaps/tasks/tickets MUST follow INDEX+EVIDENCE pattern:
1. **INDEX entry:** Brief summary (1 line) with link to evidence file
2. **Evidence file:** Full technical details in `docs/gaps/evidence/GAP-XXX.md`

---

## INDEX Entry Format

```markdown
| GAP-XXX | STATUS | Brief description (1 line) | PRIORITY | category | [Evidence](evidence/GAP-XXX.md) |
```

**Maximum 100 characters in Evidence column** - use link to detail file.

---

## Evidence File Structure

```markdown
# GAP-XXX: Brief Title

**Status:** OPEN/RESOLVED/DEFERRED
**Priority:** CRITICAL/HIGH/MEDIUM/LOW
**Category:** ux/data_integrity/architecture/etc
**Discovered:** YYYY-MM-DD via [method]

## Problem Statement
[What's wrong - user impact]

## Technical Details

### Affected Files
| File | Line | Issue |
|------|------|-------|
| `path/to/file.py` | 42 | Bug description |

### Root Cause
[Why it's happening]

### Fix
[How to fix - code snippets]

## Evidence
- Screenshot: [path]
- API response: [data]
- Logs: [relevant lines]

## Related
- Rules: RULE-XXX
- Other GAPs: GAP-YYY
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Long tech details in INDEX | Link to evidence file |
| No file/line references | Always include `file:line` |
| Fix without evidence | Screenshot/API response/log |

---

## Workflow

1. **Discover issue** during testing
2. **Create evidence file** immediately with tech details
3. **Add INDEX entry** with link to evidence
4. **Write failing test** per TDD
5. **Fix and verify** test passes

---

## Validation

- [ ] INDEX entry is brief (1 line summary)
- [ ] Evidence file exists with full details
- [ ] File:line references included
- [ ] Fix instructions are actionable

---

*Per GAP-META-001: Evidence architecture - Index to Evidence split*
