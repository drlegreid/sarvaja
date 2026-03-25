# TEST-REPORT-01-v1: Triad Test Report Postback

| Field | Value |
|-------|-------|
| **Rule ID** | TEST-REPORT-01-v1 |
| **Category** | quality |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-25 |
| **Depends** | AUDIT-COMMENT-01-v1, DELIVER-QA-MOAT-01-v1, TEST-E2E-01-v1 |

## Directive

Every task closed as DONE MUST have a structured test report posted to its `resolution_notes` via MCP, containing results from all 3 tiers of the test pyramid and all 3 MCP tools of the triad. This is the audit trail that answers "did we test this properly?" without re-reading code or logs.

## Report Template

The following structure MUST be appended to `resolution_notes` as part of the RESOLUTION comment:

```markdown
### TEST REPORT — {date}

#### T1 — Unit (log-analyzer MCP)
- **Tool**: mcp__log-analyzer__run_tests_* / analyze_tests
- **Result**: {N} passed, {M} failed, {K} skipped
- **Key tests**: {list of new/modified test files}
- **Log ref**: {log path or "inline — N tests in Xs"}

#### T2 — API (rest-api MCP)
- **Tool**: mcp__rest-api__test_request
- **Endpoints tested**:
  - {METHOD} {endpoint} → {status_code} ({expected})
  - ...
- **Post-restart**: Yes/No

#### T3 — E2E (playwright MCP)
- **Tool**: mcp__playwright__browser_*
- **Scenarios**:
  - {scenario description} → {PASS/FAIL}
  - ...
- **Screenshots**: {evidence file paths}
- **Post-restart**: Yes/No

#### Executive Summary
- **What changed**: {1-2 sentences}
- **Risk**: {LOW/MEDIUM/HIGH} — {reason}
- **Regressions checked**: {full suite result}
- **Follow-up**: {None / new task IDs}
```

## Field Requirements

| Field | Required | Source |
|-------|----------|--------|
| T1 result counts | YES | log-analyzer or pytest output |
| T1 key test files | YES | test file paths |
| T2 endpoint list | YES | rest-api MCP responses |
| T2 post-restart | YES | must be "Yes" per DELIVER-QA-MOAT-01 |
| T3 scenario list | YES | playwright interactions |
| T3 screenshots | YES | evidence/ file paths |
| T3 post-restart | YES | must be "Yes" per DELIVER-QA-MOAT-01 |
| Executive summary | YES | agent assessment |

## MCP Postback

The report is posted via:
```python
mcp__gov-tasks__task_update(
    task_id="TASK-ID",
    resolution_notes="...existing notes...\n\n### TEST REPORT — 2026-03-25\n..."
)
```

For tasks with linked GitHub issues, the report SHOULD also be posted as an issue comment (per GOV-ISSUE-EVIDENCE-01-v1).

## Enforcement

- DONE gate: `resolution_notes` MUST contain "### TEST REPORT" section
- Heuristic H-AUDIT-REPORT-001: scan DONE tasks for missing test report
- Missing T2/T3 post-restart = automatic FAIL (per DELIVER-QA-MOAT-01-v1)

## Anti-Patterns

| Shortcut | Reality |
|----------|---------|
| "Tests pass" without counts | How many? What files? Where's the log? |
| T2 without endpoint list | Which endpoints did you actually hit? |
| T3 without screenshots | Screenshots are evidence; descriptions are claims |
| No post-restart confirmation | Stale state lies; restart is mandatory |
| Report after close | Post BEFORE closing — the report IS the gate |

## Rationale

This rule exists because the question "did we do 3-tier validation?" recurs every session. A structured report in the task itself eliminates that question permanently. The task becomes its own audit trail.
