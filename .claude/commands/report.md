---
description: Generate session closure report with Zen koan and GitHub issue template
allowed-tools: mcp__gov-sessions__sessions_list, mcp__gov-tasks__tasks_list, Bash
---

# /report - Session Closure Protocol

Per REPORT-HUMOR-01-v1 (RULE-046) & REPORT-ISSUE-01-v1 (RULE-049).

## Session Summary

Generate a session summary that includes:

1. **Tasks Completed** - List all tasks marked done this session
2. **Gaps Resolved** - Any gaps closed during the session
3. **Decisions Made** - Key decisions recorded
4. **Files Modified** - Significant code changes

## Session Wisdom (RULE-046)

Select an appropriate Zen koan or insight based on session activities:

| Activity | Suggested Wisdom Type |
|----------|----------------------|
| Debugging | Self-deprecating humor |
| Refactoring | Zen Koan |
| Test failures | Gallows humor |
| AMNESIA recovery | Meta-humor |
| Rule creation | Philosophical |
| Gap resolution | Achievement |
| Infrastructure | Haiku |

**Format:**
```markdown
## Session Wisdom

> [Zen Koan or contextual joke]

*Context: [Why this relates to session activities]*
```

## GitHub Issue Template (RULE-049)

### For STATUS Issues (Tactical updates)

**Title:** `[STATUS]: {epoch}: {koan_name}`

Generate epoch: `date +%s`

**Body Template:**
```markdown
## Status: {TOPIC}

**Epoch:** {timestamp}
**Mode:** DEV | SLEEP
**Koan:** {wisdom_name}

### Progress
- [x] Task 1
- [x] Task 2
- [ ] Task 3 (in progress)

### Blockers
{None | List blockers}

### Next Actions
1. Action 1
2. Action 2

---
*Per REPORT-ISSUE-01-v1*
```

### For CERT Issues (Milestone certification)

**Title:** `[CERT]: {epoch}: {koan_name}`

**Body Template:**
```markdown
## Certification: {MILESTONE}

**Epoch:** {timestamp}
**Koan:** {wisdom_name}
**Status:** COMPLETE | PARTIAL | BLOCKED

### Validates STATUS Issues
- STATUS-{epoch1}: {summary}

### Definition of Done Checklist
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Documentation updated
- [ ] Evidence attachments present

### Evidence
| Type | File | Description |
|------|------|-------------|
| Tests | test-output.log | Pytest results |

### Session Wisdom
> {Zen koan}

---
*Per REPORT-ISSUE-01-v1 | CERT validates STATUS*
```

## GitHub CLI Command

Create issue with:
```bash
gh issue create --title "[STATUS]: $(date +%s): {KoanName}" --body "$(cat <<'EOF'
{body content}
EOF
)"
```

## Checklist Before Closing

- [ ] Session summary generated
- [ ] Zen koan/wisdom included
- [ ] GitHub issue created (STATUS or CERT)
- [ ] Context saved to claude-mem if significant session
- [ ] TODO.md updated with any deferred tasks
