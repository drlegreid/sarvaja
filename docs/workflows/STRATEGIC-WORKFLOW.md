# STRATEGIC Workflow

## Purpose
A lens for viewing project progress from a strategic game perspective:
- **Vision & Goals** - Where are we headed?
- **Current State** - What capabilities do we have?
- **Roadmap** - What options lie ahead?
- **Risks** - What could go wrong?
- **Enablers** - What accelerates us?
- **Assumptions** - What are we betting on?
- **Questions** - What's unresolved?

## When to Use

Use STRATEGIC workflow when:
1. Completing a major phase (P7.x, P9.x, etc.)
2. Making architectural decisions
3. Planning next sprint/iteration
4. Stakeholder communication
5. UAT / Certification test runs

## Certification Test Run Template

```markdown
# STRATEGIC Certification Test Run

**Date:** YYYY-MM-DD
**Phase:** Px.x (Description)
**Status:** ✅/⚠️/❌

---

## Test Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total Tests | X | Y | +Z |
| Passed | X | Y | ✅ |
| Failed | 0 | 0 | ✅ |

### Phase Completion Matrix

| Phase | Component | Tests | Status |
|-------|-----------|-------|--------|
| Px.x | Name | N | ✅ |

---

## STRATEGIC GAME VIEW

### Vision Statement
> [One-line goal statement]

### Current Capabilities
[What we have now - layered view]

### Roadmap Options
| Priority | Option | Risk | Effort |
|----------|--------|------|--------|
| P10 | ... | ... | ... |

### Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| ... | ... | ... |

### Enablers
- ✅ What accelerates us

### Assumptions
1. What we're betting on

### Open Questions
1. What's unresolved?

---

## Key Artifacts
| File | Purpose |
|------|---------|
| ... | ... |

---

*🤖 Generated with Claude Code*
```

## GitHub Integration

1. Create issue with `STRATEGIC:` prefix
2. Include full certification template
3. Link to relevant PRs/commits
4. Track as milestone progress

## Related

- [R&D-BACKLOG.md](../backlog/R&D-BACKLOG.md) - Task tracking
- [RULES-DIRECTIVES.md](../RULES-DIRECTIVES.md) - Governance rules
- [TODO.md](../../TODO.md) - Active gaps

---

*Created: 2024-12-25*
*Per RULE-001: Session Evidence Logging*
