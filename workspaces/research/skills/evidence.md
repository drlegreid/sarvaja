# Skill: Evidence Collection

**ID:** SKILL-EVIDENCE-003
**Tags:** research, documentation, handoff
**Requires:** session_start, session_end, Write

## When to Use

- Documenting research findings
- Creating handoff packages for other agents
- Recording session outcomes
- Capturing context for future sessions

## Procedure

1. **Start Evidence Collection**
   ```python
   session_start(topic="TASK-{id}")
   session_capture_intent(
       goal="Analyze GAP-UI-005",
       source="governance_get_backlog()"
   )
   ```

2. **Gather Evidence**
   - Screenshots (for UI issues)
   - Code snippets (relevant lines)
   - Test outputs (failure messages)
   - Rule references (applicable constraints)

3. **Create Handoff**
   ```markdown
   # evidence/TASK-{id}-RESEARCH.md

   ## Task Handoff: {title}
   **From:** RESEARCH Agent
   **To:** CODING Agent
   **Status:** READY_FOR_CODING

   ### Context
   [What was discovered]

   ### Action Required
   [Clear next steps]

   ### Constraints
   [Rules and limits to observe]
   ```

4. **End Session**
   ```python
   session_capture_outcome(
       status="COMPLETE",
       achieved_tasks="TASK-001",
       handoff_items="Handoff to CODING agent"
   )
   session_end(topic="TASK-{id}")
   ```

## Evidence Output

```markdown
## Evidence: TASK-001 Research Complete

### Findings
- File: governance_ui/views/dialogs.py:45
- Issue: Missing function call
- Impact: Error feedback not shown

### Files Referenced
| File | Lines | Purpose |
|------|-------|---------|
| dialogs.py | 40-60 | Dialog builders |
| __init__.py | 28 | Exports |

### Handoff Created
- Path: evidence/TASK-001-RESEARCH.md
- Next: CODING agent to implement fix
```

## Related Skills

- SKILL-EXPLORE-001 (Codebase Exploration)
- SKILL-ANALYZE-002 (Gap Analysis)

---

*Per RULE-001: Evidence-First Development*
