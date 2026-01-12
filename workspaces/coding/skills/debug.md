# Skill: Debugging

**ID:** SKILL-DEBUG-003
**Tags:** coding, debugging, troubleshooting
**Requires:** Read, Grep, Bash, logs

## When to Use

- Test failures
- Runtime errors
- Unexpected behavior
- Performance issues

## Procedure

1. **Gather Error Context**
   ```python
   # Read error logs
   Read("pytest_output.txt")
   Read("api_err.txt")

   # Check container logs
   Bash("podman logs sim-ai_governance-dashboard-dev_1 --tail 50")
   ```

2. **Reproduce Issue**
   ```bash
   # Run specific test
   pytest tests/test_failing.py::test_name -v

   # Check health
   governance_health()
   ```

3. **Trace Root Cause**
   - Find relevant code with Grep
   - Read surrounding context
   - Identify data flow
   - Check dependencies

4. **Apply Fix**
   - Minimal change to fix issue
   - Add test preventing regression
   - Verify fix with full test suite

## Evidence Output

```markdown
## Debug Report: TASK-001

### Error
```
AssertionError: Expected 'success' but got 'error'
File: tests/test_dialogs.py:45
```

### Root Cause
Missing null check in error_handler() function.

### Investigation Trail
1. Error log pointed to line 45
2. Traced to error_handler() in dialogs.py:120
3. Found missing check for None response

### Fix Applied
```python
# Before
return response.status

# After
return response.status if response else 'unknown'
```

### Verification
- pytest tests/test_dialogs.py -v  PASSED
- Full suite: 1,106 passed, 46 skipped
```

## Related Skills

- SKILL-IMPLEMENT-001 (Code Implementation)
- SKILL-TEST-002 (Test Writing)

---

*Per RULE-014: Halt conditions for investigation*
