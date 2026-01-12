# Skill: Test Writing

**ID:** SKILL-TEST-002
**Tags:** coding, testing, quality
**Requires:** Write, Bash, pytest

## When to Use

- After implementing new code
- Before committing changes (RULE-023)
- Adding coverage for existing code
- E2E validation for UI changes

## Procedure

1. **Identify Test Type**
   | Type | When | Tool |
   |------|------|------|
   | Unit | Functions, classes | pytest |
   | Integration | APIs, MCP tools | pytest + fixtures |
   | E2E | UI, workflows | Robot Framework |

2. **Create Test File**
   ```python
   # tests/test_{module}.py
   import pytest
   from module import function_under_test

   def test_function_happy_path():
       result = function_under_test(valid_input)
       assert result == expected

   def test_function_edge_case():
       with pytest.raises(ValueError):
           function_under_test(invalid_input)
   ```

3. **Run Tests**
   ```bash
   # Single file
   pytest tests/test_module.py -v

   # Full suite
   pytest tests/ -v --tb=short

   # E2E
   python -m robot tests/e2e/
   ```

4. **Verify Coverage**
   - All new code paths tested
   - Edge cases covered
   - Error handling verified

## Evidence Output

```markdown
## Test Summary: TASK-001

### Tests Created
| Test | Type | Status |
|------|------|--------|
| test_error_dialog_renders | Unit | PASS |
| test_error_dialog_closes | Unit | PASS |
| test_error_dialog_e2e.robot | E2E | PASS |

### Coverage
- Lines: 95% (dialogs.py)
- Branches: 90%

### Commands
```bash
pytest tests/test_dialogs.py -v  # 3 passed
```

### Artifacts
- results/robot/log.html (E2E report)
```

## Related Skills

- SKILL-IMPLEMENT-001 (Code Implementation)
- SKILL-DEBUG-003 (Debugging)

---

*Per RULE-023: Test Before Ship*
