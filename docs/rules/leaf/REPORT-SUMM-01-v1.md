# REPORT-SUMM-01-v1: Session Summary Reporting

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-043
> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `reporting`, `evidence`, `summary`, `certification`

---

## Directive

All significant work sessions MUST produce a summary report with:
1. **Impact Analysis** - What changed, scope, risks addressed
2. **Evidence Attachments** - Test results, screenshots, logs
3. **Commit References** - SHA, PR links, file changes
4. **Gap/Task Linkage** - IDs resolved, created, deferred

---

## Report Structure

```markdown
## Session Summary: {TOPIC}
**Date:** {YYYY-MM-DD}
**Duration:** {time}

### Changes Made
| Category | Count | Details |
|----------|-------|---------|
| Files Modified | N | list... |
| Tests Added | N | list... |
| Gaps Resolved | N | GAP-XXX, GAP-YYY |

### Evidence
- [ ] Static tests passed: `pytest tests/ -v`
- [ ] Exploratory tests: {method}
- [ ] Commit SHA: {sha}

### Next Actions
- [ ] Task 1
- [ ] Task 2
```

---

## Certification Format

For milestone completions, include:

```markdown
## Certification Issue
**Milestone:** {name}
**Status:** COMPLETE | PARTIAL

### Artifacts
- Commit: {sha} - {message}
- PR: #{number} - {title}
- Evidence: evidence/{file}.md

### Verification
| Check | Status | Evidence |
|-------|--------|----------|
| Tests pass | OK | {output} |
| No regressions | OK | {diff} |
| Rules followed | OK | {list} |
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| "Done" without evidence | Attach test output, screenshots |
| Skip impact analysis | Document scope, risks, changes |
| Omit commit references | Link SHA, PR, files modified |
| Ignore gap linkage | Reference GAP-XXX resolved/created |

---

## Enforcement

**MCP Tool**: `governance_verify_completion()` per TEST-FIX-01-v1

**Evidence Directory**: `evidence/` for persistent artifacts

---

## Validation

- [ ] Summary includes impact analysis
- [ ] Evidence attachments present
- [ ] Commit references linked
- [ ] Gap/task IDs referenced

---

*Per SESSION-EVID-01-v1: Session Evidence Logging*
