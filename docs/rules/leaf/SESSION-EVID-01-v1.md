# SESSION-EVID-01-v1: Session Evidence Logging

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** FOUNDATIONAL

> **Legacy ID:** RULE-001
> **Location:** [RULES-SESSION.md](../governance/RULES-SESSION.md)
> **Tags:** `evidence`, `session`, `logging`, `governance`

---

## Directive

All agent sessions MUST produce evidence logs including:
1. **Thought Chain** - Decisions, rationale, alternatives
2. **Artifact Tracking** - Files modified with timestamps
3. **Session Metadata** - IDs, models, tools, tokens
4. **Export** - `./docs/SESSION-{date}-{topic}.md`

### Interim Requirement (Until GAP-DATA-INTEGRITY-001 Resolved)

**CRITICAL:** Until governance dashboard provides full session→task traceability (currently 0%):
- Session evidence MUST be maintained in markdown files (`docs/SESSION-*.md`)
- Do NOT rely solely on TypeDB/API storage for session traceability
- Markdown files serve as source-of-truth until dashboard is production-ready

> **Lift Condition:** This interim requirement is lifted when:
> - GAP-DATA-INTEGRITY-001 shows 100% session→task linking
> - Dashboard successfully displays session evidence with navigation
> - EPIC-DASHBOARD-READY tasks EPIC-DR-006 through EPIC-DR-008 are complete

---

## Schema

```python
session_log = {
    "session_id": str,
    "thought_chain": [{"step": int, "decision": str, "rationale": str}],
    "artifacts": [{"path": str, "action": "create|modify|delete"}],
    "metadata": {"models": dict, "tools": dict, "tokens": int}
}
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| End session without evidence | Export session log before closing |
| Skip thought chain logging | Document decisions with rationale |
| Omit file modification tracking | List all artifacts with actions |
| Forget session metadata | Include tokens, models, tools used |

---

## Validation

- [ ] Session evidence file created
- [ ] Thought chain documented
- [ ] Artifacts tracked with actions
- [ ] Metadata recorded

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
