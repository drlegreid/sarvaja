# REPORT-ISSUE-01-v1: GitHub Certification Issue Protocol

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-049
> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `reporting`, `github`, `certification`, `milestone`

---

## Directive

All milestone completions MUST be posted as GitHub issues with standardized format:

1. **Title Format:** `[CERT] {Topic}: Status {STATUS}`
2. **Labels:** `certification`, `status:{status}`, `milestone`
3. **Auto-Close:** Issues with `Status: COMPLETE` should be closed immediately

---

## Issue Template

```markdown
## Certification: {TOPIC}

**Date:** {YYYY-MM-DD}
**Session:** SESSION-{date}-{topic}
**Status:** {COMPLETE | PARTIAL | BLOCKED}

### Summary
{1-3 sentence overview of what was accomplished}

### Changes Made
| Category | Count | Details |
|----------|-------|---------|
| Files Modified | N | list... |
| Rules Created | N | list... |
| Gaps Resolved | N | GAP-XXX |
| Tests Added | N | list... |

### Evidence
- Commit: `{sha}` - {message}
- Tests: {pass/fail status}
- Health: {governance_health output}

### Rules Applied
- {RULE-ID}: {brief description}

### Session Wisdom
> {Zen koan or relevant insight per REPORT-HUMOR-01-v1}

---
*Generated per REPORT-ISSUE-01-v1*
```

---

## Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| `COMPLETE` | All objectives met | Close issue |
| `PARTIAL` | Some objectives met | Keep open, link follow-up |
| `BLOCKED` | Cannot proceed | Keep open, document blocker |

---

## Automation

**gh CLI Command:**
```bash
gh issue create \
  --title "[CERT] Topic: Status COMPLETE" \
  --body "$(cat certification.md)" \
  --label "certification,status:complete,milestone"

# Auto-close if complete
gh issue close {issue_number} --comment "Milestone verified and closed."
```

---

## Workflow Integration

1. Session produces summary per REPORT-SUMM-01-v1
2. Agent formats as GitHub issue per this rule
3. Issue created with appropriate labels
4. If COMPLETE: auto-close with verification comment
5. If PARTIAL/BLOCKED: link to follow-up tasks

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip GitHub issue | Always post milestone completions |
| Leave COMPLETE issues open | Close with verification comment |
| Use inconsistent titles | Follow `[CERT] Topic: Status X` format |
| Forget labels | Apply certification + status labels |

---

## Validation

- [ ] Issue title follows format
- [ ] Status label applied
- [ ] Evidence section complete
- [ ] COMPLETE issues closed

---

*Per REPORT-SUMM-01-v1: Session Summary Reporting*
*Per REPORT-HUMOR-01-v1: Session Wisdom*
