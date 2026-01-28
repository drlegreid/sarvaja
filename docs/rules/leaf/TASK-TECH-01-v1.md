# TASK-TECH-01-v1: Technology Solution Documentation

**Category:** `governance` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `tasks`, `documentation`, `technology`, `enterprise`

---

## Directive

When implementing a task that involves technology choices, agent MUST document the technology selection with justification. All significant technical decisions require evidence trail.

---

## Required Documentation

### 1. Technology Selection

| Element | Description | Example |
|---------|-------------|---------|
| **Technology** | Name and version | "TypeDB 2.25.0" |
| **Justification** | Why this choice | "Schema flexibility for governance rules" |
| **Alternatives** | What was considered | "PostgreSQL, MongoDB" |
| **Trade-offs** | Pros/cons acknowledged | "Learning curve vs type safety" |

### 2. Integration Points

- **Dependencies**: What this integrates with
- **APIs**: Endpoints or interfaces exposed
- **Data Flow**: How data moves through the solution

### 3. Verification

- **Test Coverage**: How the solution is tested
- **Evidence**: Link to passing tests or demos

---

## Task Linking Requirements

Per enterprise development patterns, tasks MUST link to:

| Link Type | Required | Format |
|-----------|----------|--------|
| Session Documents | Yes | `evidence/SESSION-*.md` |
| Git Commits | Yes | `git log --oneline -1` |
| Related Tasks | If applicable | Parent/child/blocks |
| Design Documents | For MEDIUM+ priority | `docs/design/*.md` |

---

## Task Sections Template

```markdown
## Task: [ID] - [Name]

### Business (Why)
- User problem being solved
- Business value

### Design (What)
- Functional requirements
- Acceptance criteria

### Architecture (How)
- Technical approach
- Technology choices with justification

### Test (Verification)
- Test plan
- Evidence of completion
```

---

## Enforcement

**MCP Tool**: `governance_create_handoff(...)` requires `context_summary` with tech decisions.

**Gap Trigger**: Missing tech documentation triggers GAP-TASK-TECH-*.

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/task_details.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TASK-TECH-01-v1 tests/robot/
```

---

*Per SESSION-EVID-01-v1: Evidence-Based Sessions*
