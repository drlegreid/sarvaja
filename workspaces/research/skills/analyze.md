# Skill: Gap Analysis

**ID:** SKILL-ANALYZE-002
**Tags:** research, gaps, analysis
**Requires:** governance_get_backlog, governance_query_rules, Read, Grep

## When to Use

- Identifying missing functionality
- Finding rule violations
- Analyzing test coverage gaps
- Prioritizing work items

## Procedure

1. **Load Current State**
   ```python
   # Get prioritized gaps
   governance_get_backlog(limit=20)

   # Get relevant rules
   governance_query_rules(category="technical")
   ```

2. **Analyze Gap**
   - Read related code files
   - Check for rule compliance
   - Identify missing tests
   - Note dependencies

3. **Classify Severity**
   | Priority | Criteria |
   |----------|----------|
   | CRITICAL | Blocks functionality, security issue |
   | HIGH | Major feature gap, rule violation |
   | MEDIUM | Minor issue, polish item |
   | LOW | Nice-to-have, minor improvement |

4. **Document Analysis**
   - Impact assessment
   - Affected components
   - Suggested approach
   - Time estimate (Small/Medium/Large)

## Evidence Output

```markdown
## Gap Analysis: GAP-UI-005

### Summary
Error dialogs never displayed to users.

### Impact
- Severity: MEDIUM
- Affected: agent/governance_ui/views/dialogs.py
- Users cannot see error feedback

### Root Cause
`build_error_dialog()` defined but never called in `build_all_dialogs()`.

### Resolution
Add call in build_all_dialogs() function at line 45.

### Related Rules
- RULE-019: UI/UX Standards
- RULE-023: Test Before Ship
```

## Related Skills

- SKILL-EXPLORE-001 (Codebase Exploration)
- SKILL-EVIDENCE-003 (Evidence Collection)

---

*Per GAP-INDEX.md tracking standards*
