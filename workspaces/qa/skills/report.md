# Skill: Bug Reporting

**ID:** SKILL-QA-REPORT-001
**Tags:** qa, bugs, documentation, evidence
**Requires:** governance-tasks, Read, Write

## When to Use
- Issue discovered during testing
- User-reported problem
- Production incident
- Regression found

## Procedure
1. Reproduce the issue (minimum 2x)
2. Capture evidence (screenshot, logs, API response)
3. Identify root cause if possible
4. Create bug report with template
5. Create task in governance system
6. Link to related rules/gaps

## Bug Report Template

```markdown
# Bug Report: BUG-{ID}

**Reported:** {date}
**Reporter:** QA Agent
**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Component:** {component}
**Status:** NEW | CONFIRMED | IN_PROGRESS | FIXED | CLOSED

## Summary
{One-line description}

## Environment
- **Dashboard:** http://localhost:8081
- **API:** http://localhost:8082
- **Browser:** {browser + version}
- **Containers:** {list relevant containers}

## Steps to Reproduce
1. {Step 1}
2. {Step 2}
3. {Step 3}

## Expected Behavior
{What should happen}

## Actual Behavior
{What happens instead}

## Evidence
- Screenshot: {path}
- API Response: ```{json}```
- Console Errors: ```{errors}```

## Root Cause Analysis
{If known, explain why this happens}

## Suggested Fix
{If known, suggest approach}

## Related
- Rule: {RULE-ID if applicable}
- Gap: {GAP-ID if applicable}
- Task: {TASK-ID if created}
```

## Severity Guidelines

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| CRITICAL | Data loss, security breach, complete outage | Immediate |
| HIGH | Major feature broken, no workaround | Same day |
| MEDIUM | Feature impacted, workaround exists | Within sprint |
| LOW | Minor issue, cosmetic, edge case | Backlog |

## Evidence Output
- `evidence/BUG-{ID}.md` - Bug report file
- Task created in TypeDB via governance-tasks
