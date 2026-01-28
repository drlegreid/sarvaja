# WORKFLOW-AUTO-02-v1: Autonomous Task Continuation

**Category:** `operational` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-031
> **Location:** [RULES-WORKFLOW.md](../operational/RULES-WORKFLOW.md)
> **Tags:** `autonomy`, `continuation`, `tasks`, `completion`

---

## Directive

When executing multi-step tasks, agents MUST continue until ALL tasks are complete or explicit halt received.

---

## Continuation Requirements

| Trigger | Action |
|---------|--------|
| Pending items | Continue to next |
| Error during task | Log, recover, continue |
| Subtask complete | Start next immediately |
| All tasks complete | Generate summary |
| Explicit halt | Stop immediately |

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Stop after one issue | Fix all issues in sequence |
| Ask "should I continue?" | Continue automatically |
| Skip pending tasks | Complete all pending |

---

## Validation

- [ ] All tasks completed
- [ ] No unnecessary confirmation requests
- [ ] Summary generated at end

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/langgraph_extended.robot` | unit |

```bash
# Run all tests validating this rule
robot --include WORKFLOW-AUTO-02-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
