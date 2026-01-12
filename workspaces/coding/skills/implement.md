# Skill: Code Implementation

**ID:** SKILL-IMPLEMENT-001
**Tags:** coding, implementation, development
**Requires:** Edit, Write, Read, Bash

## When to Use

- Implementing features from research handoffs
- Fixing bugs with clear root cause
- Adding new functionality
- Refactoring code per RULE-032

## Procedure

1. **Review Handoff**
   ```python
   # Read research evidence
   Read("evidence/TASK-{id}-RESEARCH.md")

   # Understand constraints
   governance_query_rules(category="technical")
   ```

2. **Plan Changes**
   - Identify all files to modify
   - Check file sizes (RULE-032: <300 lines)
   - List dependencies affected
   - Note test requirements

3. **Implement**
   ```python
   # Prefer Edit over Write for existing files
   Edit(
       file_path="path/to/file.py",
       old_string="existing_code",
       new_string="new_code"
   )
   ```

4. **Follow Standards**
   - RULE-032: Keep files under 300 lines
   - RULE-008: Safe edit patterns (avoid full rewrites)
   - RULE-023: All changes must have tests

## Evidence Output

```markdown
## Implementation: TASK-001

### Changes Made
| File | Change | Lines |
|------|--------|-------|
| dialogs.py | Added build_error_dialog() call | 45-46 |
| __init__.py | Updated exports | 28 |

### Tests Added
- test_error_dialog_renders
- test_error_dialog_closes

### Verification
- pytest tests/test_dialogs.py -v  PASSED

### Handoff
- Path: evidence/TASK-001-IMPLEMENTATION.md
- Next: CURATOR agent to review
```

## Related Skills

- SKILL-TEST-002 (Test Writing)
- SKILL-DEBUG-003 (Debugging)

---

*Per RULE-008: Safe Edit Patterns*
